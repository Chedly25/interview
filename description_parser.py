import re
import json
from datetime import datetime, timedelta
import anthropic
import os
from sqlalchemy.orm import Session
from enhanced_database import Car, ParsedListing
import uuid

class IntelligentDescriptionParser:
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ) if os.getenv("ANTHROPIC_API_KEY") else None
        
        # French automotive terminology patterns
        self.service_patterns = [
            r"révision\s+(?:faite|effectuée|réalisée)?\s*(?:le\s+)?(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})",
            r"entretien\s+(?:complet|fait|suivi)\s*(?:le\s+)?(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})",
            r"vidange\s+(?:faite|changée)\s*(?:il\s+y\s+a\s+)?(\d+)\s*(?:km|kilomètres)",
            r"contrôle\s+technique\s+(?:ok|valide|passé)\s*(?:jusqu['']?au?\s+)?(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})",
            r"distribution\s+(?:changée|faite)\s*(?:à\s+)?(\d+)\s*(?:km|kilomètres)"
        ]
        
        # Equipment detection patterns
        self.equipment_patterns = {
            "climatisation": r"(?:clim|climatisation|air\s*conditioning|airco)",
            "gps": r"(?:gps|navigation|navi|tom\s*tom)",
            "bluetooth": r"(?:bluetooth|kit\s*mains\s*libres|handsfree)",
            "régulateur": r"(?:régulateur|cruise\s*control|limiteur)",
            "jantes_alliage": r"(?:jantes?\s*(?:alu|alliage)|alu|bbs)",
            "toit_ouvrant": r"(?:toit\s*ouvrant|sunroof|toit\s*panoramique)",
            "cuir": r"(?:cuir|leather|leder|alcantara)",
            "xenon": r"(?:xenon|bi-?xenon|led|phares?\s*directionnels?)",
            "attelage": r"(?:attelage|crochet|remorque)",
            "barres_toit": r"(?:barres?\s*de\s*toit|porte\s*bagages?|galerie)",
            "radar_recul": r"(?:radar|capteurs?\s*de\s*recul|park\s*assist)",
            "caméra_recul": r"(?:caméra\s*de\s*recul|rear\s*view)",
            "start_stop": r"(?:start\s*[&-]?\s*stop|stop\s*[&-]?\s*start)",
            "esp": r"(?:esp|asr|abs|ebd|système\s*stabilité)"
        }
        
        # Red flag patterns
        self.red_flag_patterns = {
            "accident": r"(?:accident|choc|sinistre|collision)",
            "panne": r"(?:panne|problème|souci|défaillance)",
            "réparation": r"(?:réparation|réparé|à\s*réparer)",
            "bruit": r"(?:bruit|claquement|grincement|sifflement)",
            "fuite": r"(?:fuite|suinte|coule)",
            "usure": r"(?:usé|usure|fatigué|fin\s*de\s*vie)",
            "rouille": r"(?:rouille|corrosion|oxydation)",
            "urgence": r"(?:urgent|rapide|vite|départ\s*immédiat)"
        }
        
        # Positive signal patterns
        self.positive_patterns = {
            "entretien_suivi": r"(?:entretien\s*suivi|carnet\s*entretien|historique\s*complet)",
            "première_main": r"(?:première?\s*main|1ère?\s*main|premier\s*propriétaire)",
            "non_fumeur": r"(?:non\s*fumeur|pas\s*fumé|sans\s*tabac)",
            "garage": r"(?:toujours\s*au\s*garage|garé\s*au\s*garage|abrité)",
            "factures": r"(?:factures?|justificatifs?|preuves?)",
            "garantie": r"(?:garantie|warranty|sous\s*garantie)",
            "révisé": r"(?:révisé|révision\s*récente|entretien\s*récent)",
            "pneus_neufs": r"(?:pneus?\s*neufs?|gommes?\s*neuves?|train\s*neuf)"
        }

    def parse_description(self, car: Car) -> dict:
        """Parse car description using AI and patterns"""
        if not car.description:
            return {"error": "No description available"}
        
        # Use Claude for intelligent parsing
        claude_analysis = self._claude_parse_description(car)
        
        # Use regex patterns as backup/supplement
        pattern_analysis = self._pattern_parse_description(car)
        
        # Combine results
        combined_analysis = self._combine_analyses(claude_analysis, pattern_analysis)
        
        # Calculate credibility score
        credibility_score = self._calculate_seller_credibility(car, combined_analysis)
        combined_analysis["seller_credibility"] = credibility_score
        
        # Identify missing information
        missing_info = self._identify_missing_information(car, combined_analysis)
        combined_analysis["missing_information"] = missing_info
        
        return combined_analysis

    def _claude_parse_description(self, car: Car) -> dict:
        """Use Claude to intelligently parse the description"""
        if not self.anthropic_client:
            return self._fallback_parsing(car)
        
        try:
            prompt = f"""
            Analysez cette description de voiture française en détail et extrayez les informations structurées.

            Titre: {car.title}
            Description: {car.description}
            Prix: {car.price}€
            Année: {car.year}
            Kilométrage: {car.mileage} km
            Type vendeur: {car.seller_type}

            Extrayez et structurez en JSON:
            1. service_history: Historique d'entretien avec dates et détails
            2. detected_options: Liste complète des équipements mentionnés
            3. red_flags: Signaux d'alarme ou problèmes mentionnés
            4. positive_signals: Points positifs et assurances du vendeur
            5. ownership_info: Informations sur la propriété (nb propriétaires, usage)
            6. condition_assessment: Évaluation de l'état général
            7. seller_motivation: Niveau de motivation du vendeur (1-10)
            8. honesty_indicators: Indicateurs d'honnêteté dans la description
            9. hidden_costs: Coûts cachés ou travaux à prévoir mentionnés
            10. negotiation_leverage: Points qui donnent du pouvoir de négociation

            Soyez précis et objectif. Répondez uniquement en JSON valide français.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis_text = message.content[0].text
            return json.loads(analysis_text)
            
        except Exception as e:
            print(f"Claude parsing error: {e}")
            return self._fallback_parsing(car)

    def _pattern_parse_description(self, car: Car) -> dict:
        """Parse description using regex patterns"""
        text = f"{car.title} {car.description}".lower()
        
        # Extract service history
        service_history = []
        for pattern in self.service_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                service_history.append({
                    "type": self._classify_service_type(match.group(0)),
                    "details": match.group(0),
                    "date_or_km": match.group(1) if match.groups() else None
                })
        
        # Extract equipment
        detected_options = []
        for equipment, pattern in self.equipment_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected_options.append(equipment.replace("_", " ").title())
        
        # Extract red flags
        red_flags = []
        for flag, pattern in self.red_flag_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                red_flags.append({
                    "type": flag,
                    "context": self._extract_context(text, match.start(), match.end())
                })
        
        # Extract positive signals
        positive_signals = []
        for signal, pattern in self.positive_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                positive_signals.append(signal.replace("_", " ").title())
        
        return {
            "service_history": service_history,
            "detected_options": detected_options,
            "red_flags": red_flags,
            "positive_signals": positive_signals,
            "analysis_method": "pattern_matching"
        }

    def _fallback_parsing(self, car: Car) -> dict:
        """Fallback parsing when Claude is not available"""
        return self._pattern_parse_description(car)

    def _combine_analyses(self, claude_analysis: dict, pattern_analysis: dict) -> dict:
        """Combine Claude and pattern analyses"""
        combined = {
            "service_history": [],
            "detected_options": [],
            "red_flags": [],
            "positive_signals": [],
            "ownership_info": [],
            "condition_assessment": "",
            "seller_motivation": 5,
            "honesty_indicators": [],
            "hidden_costs": [],
            "negotiation_leverage": []
        }
        
        # Merge service history
        claude_services = claude_analysis.get("service_history", [])
        pattern_services = pattern_analysis.get("service_history", [])
        combined["service_history"] = claude_services + pattern_services
        
        # Merge equipment (remove duplicates)
        claude_options = claude_analysis.get("detected_options", [])
        pattern_options = pattern_analysis.get("detected_options", [])
        all_options = claude_options + pattern_options
        combined["detected_options"] = list(set(all_options))
        
        # Merge red flags
        claude_flags = claude_analysis.get("red_flags", [])
        pattern_flags = pattern_analysis.get("red_flags", [])
        combined["red_flags"] = claude_flags + pattern_flags
        
        # Merge positive signals
        claude_positive = claude_analysis.get("positive_signals", [])
        pattern_positive = pattern_analysis.get("positive_signals", [])
        all_positive = claude_positive + pattern_positive
        combined["positive_signals"] = list(set(all_positive))
        
        # Take Claude's assessment for complex fields
        for field in ["ownership_info", "condition_assessment", "seller_motivation", 
                     "honesty_indicators", "hidden_costs", "negotiation_leverage"]:
            if field in claude_analysis:
                combined[field] = claude_analysis[field]
        
        combined["analysis_sources"] = {
            "claude_available": "claude_analysis" in str(claude_analysis),
            "pattern_matching": True
        }
        
        return combined

    def _classify_service_type(self, service_text: str) -> str:
        """Classify type of service from text"""
        text = service_text.lower()
        if "révision" in text:
            return "révision"
        elif "vidange" in text:
            return "vidange"
        elif "contrôle" in text:
            return "contrôle_technique"
        elif "distribution" in text:
            return "distribution"
        elif "entretien" in text:
            return "entretien_général"
        else:
            return "autre"

    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract context around a match"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()

    def _calculate_seller_credibility(self, car: Car, analysis: dict) -> float:
        """Calculate seller credibility score 0-100"""
        score = 50  # Base score
        
        # Positive factors
        if analysis.get("service_history"):
            score += len(analysis["service_history"]) * 5
        
        if analysis.get("positive_signals"):
            score += len(analysis["positive_signals"]) * 3
        
        # Professional vs private seller
        if car.seller_type == "professionnel":
            score += 10
        
        # Description quality
        if car.description and len(car.description) > 200:
            score += 10
        elif car.description and len(car.description) > 100:
            score += 5
        
        # Negative factors
        if analysis.get("red_flags"):
            score -= len(analysis["red_flags"]) * 8
        
        # Check for contradictions
        contradictions = self._detect_contradictions(car, analysis)
        score -= len(contradictions) * 15
        
        # Grammar and spelling quality (basic check)
        if car.description:
            typos = self._count_likely_typos(car.description)
            score -= min(20, typos * 2)
        
        return max(0, min(100, score))

    def _detect_contradictions(self, car: Car, analysis: dict) -> list:
        """Detect contradictions in the listing"""
        contradictions = []
        
        # Price vs condition contradictions
        if car.price and car.price < 5000:
            if any("excellent" in str(item).lower() for item in analysis.get("positive_signals", [])):
                contradictions.append("Prix très bas mais état annoncé excellent")
        
        # Year vs mileage contradictions
        if car.year and car.mileage:
            expected_km = (2024 - car.year) * 15000  # Average 15k km/year
            if car.mileage < expected_km * 0.3:
                contradictions.append("Kilométrage très faible pour l'année")
            elif car.mileage > expected_km * 2:
                contradictions.append("Kilométrage très élevé pour l'année")
        
        return contradictions

    def _count_likely_typos(self, text: str) -> int:
        """Count likely typos in French text"""
        typo_patterns = [
            r'\b(?:sa|ces|est|et)\b.*\b(?:ça|ses|ait|est)\b',  # Common French errors
            r'[a-z]{3,}[A-Z]',  # Mixed case within words
            r'\s{2,}',  # Multiple spaces
            r'[.]{2,}',  # Multiple periods
            r'[!]{2,}',  # Multiple exclamations
        ]
        
        typo_count = 0
        for pattern in typo_patterns:
            typo_count += len(re.findall(pattern, text))
        
        return typo_count

    def _identify_missing_information(self, car: Car, analysis: dict) -> list:
        """Identify important missing information"""
        missing = []
        
        # Basic information
        if not car.year:
            missing.append("Année du véhicule")
        if not car.mileage:
            missing.append("Kilométrage")
        if not car.fuel_type:
            missing.append("Type de carburant")
        
        # Service information
        if not analysis.get("service_history"):
            missing.append("Historique d'entretien")
        
        # Ownership information
        ownership_mentioned = any("propriétaire" in str(item).lower() or "main" in str(item).lower() 
                                for item in analysis.get("positive_signals", []))
        if not ownership_mentioned:
            missing.append("Nombre de propriétaires")
        
        # Control technique
        ct_mentioned = any("contrôle" in str(item).lower() 
                          for item in analysis.get("service_history", []))
        if not ct_mentioned:
            missing.append("Contrôle technique")
        
        # Reason for sale
        if car.seller_type == "particulier":
            reason_patterns = ["déménagement", "changement", "achat", "plus besoin"]
            reason_mentioned = any(pattern in car.description.lower() 
                                 for pattern in reason_patterns if car.description)
            if not reason_mentioned:
                missing.append("Raison de la vente")
        
        return missing

    def parse_and_save(self, car: Car, db: Session) -> dict:
        """Parse description and save to database"""
        # Check if already parsed recently
        existing = db.query(ParsedListing).filter(
            ParsedListing.car_id == car.id
        ).first()
        
        if existing and existing.parsed_at > datetime.utcnow() - timedelta(hours=24):
            return {
                "service_history": existing.service_history,
                "detected_options": existing.detected_options,
                "red_flags": existing.red_flags,
                "positive_signals": existing.positive_signals,
                "seller_credibility": existing.seller_credibility,
                "missing_information": existing.missing_information,
                "cached": True
            }
        
        # Parse description
        analysis = self.parse_description(car)
        
        if "error" not in analysis:
            # Save or update
            if existing:
                existing.parsed_data = analysis
                existing.service_history = analysis.get("service_history", [])
                existing.detected_options = analysis.get("detected_options", [])
                existing.red_flags = analysis.get("red_flags", [])
                existing.positive_signals = analysis.get("positive_signals", [])
                existing.seller_credibility = analysis.get("seller_credibility", 50)
                existing.missing_information = analysis.get("missing_information", [])
                existing.parsed_at = datetime.utcnow()
            else:
                parsed_listing = ParsedListing(
                    car_id=car.id,
                    raw_description=car.description,
                    parsed_data=analysis,
                    service_history=analysis.get("service_history", []),
                    detected_options=analysis.get("detected_options", []),
                    red_flags=analysis.get("red_flags", []),
                    positive_signals=analysis.get("positive_signals", []),
                    seller_credibility=analysis.get("seller_credibility", 50),
                    missing_information=analysis.get("missing_information", []),
                    parser_version="1.0"
                )
                db.add(parsed_listing)
            
            db.commit()
        
        return analysis

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    parser = IntelligentDescriptionParser()
    db = SessionLocal()
    
    # Test with first car
    car = db.query(Car).filter(Car.description.isnot(None)).first()
    if car:
        print(f"Parsing description for: {car.title}")
        result = parser.parse_and_save(car, db)
        print(f"Parsed options: {result.get('detected_options', [])}")
        print(f"Red flags: {result.get('red_flags', [])}")
        print(f"Credibility: {result.get('seller_credibility', 0)}%")
    else:
        print("No cars with descriptions found")
    
    db.close()