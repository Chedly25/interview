import json
import requests
from datetime import datetime, timedelta
import base64
import anthropic
import os
from sqlalchemy.orm import Session
from enhanced_database import Car, PhotoAnalysis
import uuid

class AIPhotoAnalyzer:
    def __init__(self):
        try:
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            ) if os.getenv("ANTHROPIC_API_KEY") else None
        except Exception as e:
            print(f"Warning: Anthropic client initialization failed in photo_analyzer: {e}")
            self.anthropic_client = None
        
        # Damage detection keywords
        self.damage_indicators = {
            "rayure": {"severity": "minor", "cost": 200},
            "bosse": {"severity": "moderate", "cost": 400},
            "rouille": {"severity": "major", "cost": 800},
            "choc": {"severity": "major", "cost": 1200},
            "fissure": {"severity": "moderate", "cost": 300},
            "usure": {"severity": "minor", "cost": 150}
        }
        
        # Valuable features to detect
        self.valuable_features = {
            "jantes_sport": 500,
            "xenon_led": 400,
            "toit_ouvrant": 800,
            "cuir": 1000,
            "gps_ecran": 600,
            "attelage": 300,
            "barres_toit": 200,
            "pneus_hiver": 400
        }

    def analyze_car_photos(self, car: Car, db: Session) -> dict:
        """Analyze all photos of a car using Claude Vision"""
        if not car.images:
            return {"error": "No images available"}
        
        images = json.loads(car.images)
        if not images:
            return {"error": "No images in listing"}
        
        analysis_results = []
        overall_condition_score = 0
        detected_damage = []
        detected_features = []
        honesty_issues = []
        
        for i, image_url in enumerate(images[:8]):  # Limit to 8 photos for cost control
            try:
                photo_analysis = self._analyze_single_photo(image_url, i + 1, car.title)
                analysis_results.append(photo_analysis)
                
                # Aggregate condition score
                if photo_analysis.get("condition_score"):
                    overall_condition_score += photo_analysis["condition_score"]
                
                # Collect damage
                if photo_analysis.get("damage_detected"):
                    detected_damage.extend(photo_analysis["damage_detected"])
                
                # Collect features
                if photo_analysis.get("features_detected"):
                    detected_features.extend(photo_analysis["features_detected"])
                
                # Check photo honesty
                if photo_analysis.get("honesty_issues"):
                    honesty_issues.extend(photo_analysis["honesty_issues"])
                    
            except Exception as e:
                analysis_results.append({
                    "photo_index": i + 1,
                    "error": str(e)
                })
        
        # Calculate averages and overall scores
        valid_analyses = [r for r in analysis_results if "condition_score" in r]
        avg_condition = overall_condition_score / len(valid_analyses) if valid_analyses else 5.0
        
        # Calculate honesty score
        honesty_score = max(1.0, 10.0 - (len(honesty_issues) * 1.5))
        
        # Estimate repair costs
        repair_costs = self._estimate_repair_costs(detected_damage)
        
        # Calculate feature value
        feature_value = self._calculate_feature_value(detected_features)
        
        return {
            "overall_condition_score": round(avg_condition, 1),
            "honesty_score": round(honesty_score, 1),
            "detected_damage": detected_damage,
            "detected_features": detected_features,
            "estimated_repair_costs": repair_costs,
            "feature_value_bonus": feature_value,
            "honesty_issues": honesty_issues,
            "photo_count": len(images),
            "analyzed_photos": len(analysis_results),
            "detailed_analysis": analysis_results,
            "summary": self._generate_photo_summary(avg_condition, detected_damage, detected_features)
        }

    def _analyze_single_photo(self, image_url: str, photo_index: int, car_title: str) -> dict:
        """Analyze a single photo using Claude Vision"""
        if not self.anthropic_client:
            return self._fallback_photo_analysis(image_url, photo_index)
        
        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                return {"error": "Could not download image"}
            
            # Encode image to base64
            image_data = base64.b64encode(response.content).decode()
            
            prompt = f"""
            Analysez cette photo de voiture en détail. Il s'agit de la photo {photo_index} d'une {car_title}.

            Analysez et rapportez en JSON:
            1. condition_score: Note de 1-10 sur l'état visible (10 = parfait)
            2. damage_detected: Liste des dommages visibles
            3. features_detected: Équipements/options visibles
            4. photo_quality: Qualité de la photo (éclairage, angle, netteté)
            5. honesty_issues: Problèmes de présentation (angles cachés, filtres, etc.)
            6. area_focus: Quelle partie de la voiture (extérieur, intérieur, moteur, etc.)
            7. visible_wear: Signes d'usure normale
            8. red_flags: Signaux d'alarme importants

            Soyez précis et objectif. Répondez uniquement en JSON valide.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }]
            )
            
            analysis_text = message.content[0].text
            analysis = json.loads(analysis_text)
            analysis["photo_index"] = photo_index
            analysis["image_url"] = image_url
            
            return analysis
            
        except Exception as e:
            return self._fallback_photo_analysis(image_url, photo_index, str(e))

    def _fallback_photo_analysis(self, image_url: str, photo_index: int, error: str = None) -> dict:
        """Fallback analysis when Claude Vision is not available"""
        return {
            "photo_index": photo_index,
            "image_url": image_url,
            "condition_score": 6.0,  # Neutral score
            "damage_detected": [],
            "features_detected": [],
            "photo_quality": "unknown",
            "honesty_issues": [],
            "area_focus": "unknown",
            "visible_wear": [],
            "red_flags": [],
            "analysis_method": "fallback",
            "note": f"Vision analysis unavailable: {error}" if error else "Vision analysis unavailable"
        }

    def _estimate_repair_costs(self, detected_damage: list) -> dict:
        """Estimate repair costs based on detected damage"""
        costs = {
            "minor_repairs": 0,
            "moderate_repairs": 0,
            "major_repairs": 0,
            "total_estimated": 0,
            "breakdown": []
        }
        
        for damage in detected_damage:
            damage_lower = damage.lower()
            estimated_cost = 0
            severity = "minor"
            
            # Match damage with cost estimates
            for keyword, info in self.damage_indicators.items():
                if keyword in damage_lower:
                    estimated_cost = info["cost"]
                    severity = info["severity"]
                    break
            
            if not estimated_cost:
                # Generic estimates based on keywords
                if any(word in damage_lower for word in ["grave", "important", "gros"]):
                    estimated_cost = 1000
                    severity = "major"
                elif any(word in damage_lower for word in ["moyen", "notable"]):
                    estimated_cost = 400
                    severity = "moderate"
                else:
                    estimated_cost = 200
                    severity = "minor"
            
            costs[f"{severity}_repairs"] += estimated_cost
            costs["breakdown"].append({
                "damage": damage,
                "severity": severity,
                "estimated_cost": estimated_cost
            })
        
        costs["total_estimated"] = sum([
            costs["minor_repairs"],
            costs["moderate_repairs"],
            costs["major_repairs"]
        ])
        
        return costs

    def _calculate_feature_value(self, detected_features: list) -> dict:
        """Calculate value of detected features"""
        value = {
            "total_value": 0,
            "features": []
        }
        
        for feature in detected_features:
            feature_lower = feature.lower()
            feature_value = 0
            
            # Match features with values
            for keyword, val in self.valuable_features.items():
                if any(part in feature_lower for part in keyword.split("_")):
                    feature_value = val
                    break
            
            if feature_value > 0:
                value["features"].append({
                    "feature": feature,
                    "estimated_value": feature_value
                })
                value["total_value"] += feature_value
        
        return value

    def _generate_photo_summary(self, condition_score: float, damage: list, features: list) -> str:
        """Generate human-readable summary of photo analysis"""
        summary_parts = []
        
        # Condition assessment
        if condition_score >= 8:
            summary_parts.append("État excellent visible sur les photos")
        elif condition_score >= 6:
            summary_parts.append("État général correct")
        elif condition_score >= 4:
            summary_parts.append("État moyen avec signes d'usure")
        else:
            summary_parts.append("État préoccupant visible")
        
        # Damage summary
        if damage:
            if len(damage) == 1:
                summary_parts.append(f"1 défaut détecté: {damage[0]}")
            else:
                summary_parts.append(f"{len(damage)} défauts détectés")
        else:
            summary_parts.append("Aucun dommage majeur visible")
        
        # Features summary
        if features:
            if len(features) <= 2:
                summary_parts.append(f"Options détectées: {', '.join(features)}")
            else:
                summary_parts.append(f"{len(features)} options valorisantes détectées")
        
        return ". ".join(summary_parts)

    def analyze_and_save(self, car: Car, db: Session) -> dict:
        """Analyze car photos and save results to database"""
        # Check if already analyzed recently
        existing = db.query(PhotoAnalysis).filter(
            PhotoAnalysis.car_id == car.id,
            PhotoAnalysis.analyzed_at > datetime.utcnow() - timedelta(days=1)
        ).first()
        
        if existing:
            return json.loads(existing.analysis_result)
        
        # Perform analysis
        analysis = self.analyze_car_photos(car, db)
        
        if "error" not in analysis:
            # Save to database
            for i, photo_result in enumerate(analysis.get("detailed_analysis", [])):
                if "error" not in photo_result:
                    photo_analysis = PhotoAnalysis(
                        id=str(uuid.uuid4()),
                        car_id=car.id,
                        photo_url=photo_result.get("image_url", ""),
                        analysis_result=photo_result,
                        damage_detected=photo_result.get("damage_detected", []),
                        features_detected=photo_result.get("features_detected", []),
                        condition_score=photo_result.get("condition_score", 5.0),
                        honesty_score=analysis.get("honesty_score", 7.0)
                    )
                    db.add(photo_analysis)
            
            db.commit()
        
        return analysis

    def get_photo_insights(self, car_id: str, db: Session) -> dict:
        """Get saved photo analysis insights for a car"""
        analyses = db.query(PhotoAnalysis).filter(
            PhotoAnalysis.car_id == car_id
        ).all()
        
        if not analyses:
            return {"message": "No photo analysis available"}
        
        # Aggregate insights
        condition_scores = [a.condition_score for a in analyses if a.condition_score]
        avg_condition = sum(condition_scores) / len(condition_scores) if condition_scores else 5.0
        
        all_damage = []
        all_features = []
        
        for analysis in analyses:
            if analysis.damage_detected:
                all_damage.extend(analysis.damage_detected)
            if analysis.features_detected:
                all_features.extend(analysis.features_detected)
        
        return {
            "average_condition_score": round(avg_condition, 1),
            "photos_analyzed": len(analyses),
            "unique_damage": list(set(all_damage)),
            "unique_features": list(set(all_features)),
            "latest_analysis": analyses[-1].analyzed_at.isoformat() if analyses else None,
            "detailed_photos": [
                {
                    "photo_url": a.photo_url,
                    "condition_score": a.condition_score,
                    "damage": a.damage_detected,
                    "features": a.features_detected
                }
                for a in analyses
            ]
        }

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    analyzer = AIPhotoAnalyzer()
    db = SessionLocal()
    
    # Test with first car that has images
    car = db.query(Car).filter(Car.images.isnot(None)).first()
    if car:
        print(f"Analyzing photos for: {car.title}")
        result = analyzer.analyze_and_save(car, db)
        print(f"Analysis result: {result}")
    else:
        print("No cars with images found")
    
    db.close()