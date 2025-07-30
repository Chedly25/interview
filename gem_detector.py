import re
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from enhanced_database import Car, GemScore
import anthropic
import os

class HiddenGemDetector:
    def __init__(self):
        try:
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            ) if os.getenv("ANTHROPIC_API_KEY") else None
        except Exception as e:
            print(f"Warning: Anthropic client initialization failed: {e}")
            self.anthropic_client = None
        
        # French keywords indicating motivated sellers
        self.motivated_seller_keywords = [
            "urgent", "déménagement", "divorce", "succession", "décès",
            "rapide", "vite", "immédiat", "cause santé", "mutation",
            "expatriation", "fin de bail", "besoin d'argent", "négociable"
        ]
        
        # Keywords indicating poor presentation
        self.poor_presentation_indicators = [
            "à voir", "tel quel", "en l'état", "petit prix", "faire offre",
            "à débattre", "prix serré", "dernière chance", "liquidation"
        ]

    def calculate_gem_score(self, car: Car, db: Session) -> dict:
        """Calculate comprehensive gem score for a car"""
        
        scores = {
            "price_anomaly": self._analyze_price_anomaly(car, db),
            "seller_motivation": self._detect_seller_motivation(car),
            "presentation_quality": self._assess_presentation_quality(car),
            "hidden_value": self._identify_hidden_value(car),
            "market_timing": self._evaluate_market_timing(car),
            "profit_potential": self._calculate_profit_potential(car, db)
        }
        
        # Weighted gem score calculation
        weights = {
            "price_anomaly": 0.25,
            "seller_motivation": 0.20,
            "presentation_quality": 0.15,
            "hidden_value": 0.15,
            "market_timing": 0.10,
            "profit_potential": 0.15
        }
        
        gem_score = sum(scores[key] * weights[key] for key in scores)
        gem_score = min(100, max(0, gem_score))  # Clamp to 0-100
        
        # Generate reasons and recommendations
        reasons = self._generate_gem_reasons(scores, car)
        risk_factors = self._identify_risk_factors(car, scores)
        
        return {
            "gem_score": int(gem_score),
            "scores_breakdown": scores,
            "reasons": reasons,
            "profit_potential": self._estimate_profit_euros(car, db),
            "risk_factors": risk_factors,
            "market_position": self._determine_market_position(gem_score),
            "confidence_level": self._calculate_confidence(scores, car),
            "quick_flip": gem_score > 75 and scores["seller_motivation"] > 80,
            "value_add": gem_score > 60 and scores["hidden_value"] > 70
        }

    def _analyze_price_anomaly(self, car: Car, db: Session) -> float:
        """Detect if car is priced significantly below market value"""
        if not car.price or not car.year or not car.mileage:
            return 50  # Neutral score for incomplete data
        
        # Get similar cars for comparison
        similar_cars = db.query(Car).filter(
            Car.year.between(car.year - 2, car.year + 2),
            Car.mileage.between(car.mileage - 20000, car.mileage + 20000),
            Car.price.isnot(None),
            Car.is_active == True,
            Car.id != car.id
        ).limit(20).all()
        
        if len(similar_cars) < 3:
            return 50  # Not enough data
        
        # Calculate average market price
        avg_price = sum(c.price for c in similar_cars) / len(similar_cars)
        price_diff_percentage = ((avg_price - car.price) / avg_price) * 100
        
        # Score based on how much below market price
        if price_diff_percentage > 30:
            return 95  # Extremely undervalued
        elif price_diff_percentage > 20:
            return 85  # Very undervalued
        elif price_diff_percentage > 10:
            return 70  # Moderately undervalued
        elif price_diff_percentage > 0:
            return 60  # Slightly undervalued
        else:
            return max(20, 50 - (price_diff_percentage * -2))  # Overpriced

    def _detect_seller_motivation(self, car: Car) -> float:
        """Analyze seller motivation from title and description"""
        text = f"{car.title} {car.description}".lower()
        
        motivation_score = 0
        motivation_indicators = []
        
        # Check for motivated seller keywords
        for keyword in self.motivated_seller_keywords:
            if keyword in text:
                motivation_score += 15
                motivation_indicators.append(keyword)
        
        # Check for time pressure indicators
        time_patterns = [
            r"vend (ce|cette) (semaine|mois)",
            r"départ (immédiat|urgent)",
            r"fin (de )?mois",
            r"avant le \d+",
            r"rapidement"
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, text):
                motivation_score += 10
                motivation_indicators.append("time_pressure")
        
        # Professional vs private seller (private more motivated)
        if car.seller_type == "particulier":
            motivation_score += 10
        
        # Long listing duration (if we can detect it)
        if "baisse de prix" in text or "prix revu" in text:
            motivation_score += 20
            motivation_indicators.append("price_reduction")
        
        return min(100, motivation_score)

    def _assess_presentation_quality(self, car: Car) -> float:
        """Assess quality of listing presentation"""
        presentation_score = 100  # Start high, deduct points
        
        title = car.title.lower()
        description = car.description.lower() if car.description else ""
        
        # Check for poor presentation indicators
        for indicator in self.poor_presentation_indicators:
            if indicator in f"{title} {description}":
                presentation_score -= 15
        
        # Title quality assessment
        if len(car.title) < 20:
            presentation_score -= 10  # Too short
        
        if car.title.isupper():
            presentation_score -= 10  # All caps (looks desperate)
        
        # Description quality
        if not car.description or len(car.description) < 50:
            presentation_score -= 20  # Missing or poor description
        
        # Multiple exclamation marks or caps
        if "!!!" in f"{title} {description}" or re.search(r'[A-Z]{5,}', car.title):
            presentation_score -= 15
        
        # Grammar and spelling (basic check)
        if re.search(r'\b(sa|ces|est|et)\b.*\b(ça|ses|ait|est)\b', description):
            presentation_score -= 5  # Common French errors
        
        # Image quality (if we have images)
        images = json.loads(car.images) if car.images else []
        if len(images) < 3:
            presentation_score -= 15  # Too few photos
        elif len(images) < 5:
            presentation_score -= 5
        
        return max(0, min(100, presentation_score))

    def _identify_hidden_value(self, car: Car) -> float:
        """Identify valuable features not prominently mentioned"""
        text = f"{car.title} {car.description}".lower()
        hidden_value_score = 0
        
        # Valuable options often not highlighted
        valuable_options = {
            "cuir": 15, "leather": 15, "leder": 15,
            "gps": 10, "navigation": 10, "navi": 10,
            "xenon": 12, "led": 8, "bi-xenon": 15,
            "climatisation": 8, "clim": 8, "airco": 8,
            "jantes alliage": 10, "alu": 8, "bbs": 15,
            "toit ouvrant": 12, "sunroof": 12,
            "attelage": 8, "crochet": 8,
            "régulateur": 6, "cruise": 6,
            "bluetooth": 5, "usb": 3,
            "caméra": 10, "radar": 8,
            "pack sport": 15, "sport package": 15,
            "full option": 20, "full": 15
        }
        
        # Check if valuable options are mentioned but not in title
        title_lower = car.title.lower()
        for option, value in valuable_options.items():
            if option in text and option not in title_lower:
                hidden_value_score += value * 0.7  # Hidden value multiplier
            elif option in title_lower:
                hidden_value_score += value * 0.3  # Properly advertised
        
        # Model-specific valuable features
        make_model = car.title.lower()
        
        # BMW specific
        if any(word in make_model for word in ["bmw", "série"]):
            bmw_features = ["m-sport", "m sport", "pack m", "m-packet"]
            for feature in bmw_features:
                if feature in text and feature not in title_lower:
                    hidden_value_score += 20
        
        # Mercedes specific
        if "mercedes" in make_model or "benz" in make_model:
            mb_features = ["amg", "avantgarde", "elegance", "4matic"]
            for feature in mb_features:
                if feature in text and feature not in title_lower:
                    hidden_value_score += 18
        
        # Audi specific
        if "audi" in make_model:
            audi_features = ["s-line", "sline", "quattro", "s line"]
            for feature in audi_features:
                if feature in text and feature not in title_lower:
                    hidden_value_score += 17
        
        return min(100, hidden_value_score)

    def _evaluate_market_timing(self, car: Car) -> float:
        """Evaluate timing factors affecting car value"""
        timing_score = 50  # Neutral base
        
        current_month = datetime.now().month
        
        # Seasonal factors
        if current_month in [11, 12, 1, 2]:  # Winter
            if "4x4" in car.title.lower() or "quattro" in car.title.lower():
                timing_score += 20  # 4WD more valuable in winter
            else:
                timing_score += 10  # General winter buying opportunity
        
        if current_month in [3, 4, 5]:  # Spring
            timing_score += 15  # Good buying season
        
        if current_month in [6, 7, 8]:  # Summer
            if "cabriolet" in car.title.lower() or "convertible" in car.title.lower():
                timing_score += 25  # Convertibles peak in summer
            else:
                timing_score -= 5  # Higher competition
        
        # End of month/year urgency
        current_day = datetime.now().day
        if current_day > 25:  # Last week of month
            timing_score += 10
        
        # Year-end car changes
        if current_month == 12:
            timing_score += 15
        
        return min(100, max(0, timing_score))

    def _calculate_profit_potential(self, car: Car, db: Session) -> float:
        """Calculate potential profit from flipping this car"""
        if not car.price:
            return 0
        
        # Estimate market value
        similar_cars = db.query(Car).filter(
            Car.year.between(car.year - 1, car.year + 1) if car.year else True,
            Car.price.isnot(None),
            Car.is_active == True,
            Car.id != car.id
        ).limit(10).all()
        
        if not similar_cars:
            return 50
        
        avg_market_price = sum(c.price for c in similar_cars) / len(similar_cars)
        potential_profit = avg_market_price - car.price
        profit_percentage = (potential_profit / car.price) * 100 if car.price > 0 else 0
        
        # Score based on profit percentage
        if profit_percentage > 50:
            return 100
        elif profit_percentage > 30:
            return 90
        elif profit_percentage > 20:
            return 80
        elif profit_percentage > 15:
            return 70
        elif profit_percentage > 10:
            return 60
        else:
            return max(0, 30 + profit_percentage * 2)

    def _estimate_profit_euros(self, car: Car, db: Session) -> int:
        """Estimate potential profit in euros"""
        if not car.price:
            return 0
        
        similar_cars = db.query(Car).filter(
            Car.year.between(car.year - 1, car.year + 1) if car.year else True,
            Car.price.isnot(None),
            Car.is_active == True,
            Car.id != car.id
        ).limit(10).all()
        
        if not similar_cars:
            return 0
        
        avg_market_price = sum(c.price for c in similar_cars) / len(similar_cars)
        potential_profit = max(0, avg_market_price - car.price - 500)  # Minus costs
        
        return int(potential_profit)

    def _generate_gem_reasons(self, scores: dict, car: Car) -> list:
        """Generate human-readable reasons why this is a gem"""
        reasons = []
        
        if scores["price_anomaly"] > 70:
            reasons.append("Prix significativement en dessous du marché")
        
        if scores["seller_motivation"] > 70:
            reasons.append("Vendeur très motivé (urgence détectée)")
        
        if scores["presentation_quality"] < 40:
            reasons.append("Présentation de mauvaise qualité cache le potentiel")
        
        if scores["hidden_value"] > 60:
            reasons.append("Options valorisantes non mises en avant")
        
        if scores["market_timing"] > 70:
            reasons.append("Moment favorable pour l'achat")
        
        if scores["profit_potential"] > 70:
            reasons.append("Fort potentiel de plus-value")
        
        return reasons

    def _identify_risk_factors(self, car: Car, scores: dict) -> list:
        """Identify potential risks"""
        risks = []
        
        if not car.images or len(json.loads(car.images)) < 3:
            risks.append("Peu de photos disponibles")
        
        if car.seller_type == "professionnel" and scores["seller_motivation"] > 80:
            risks.append("Vendeur professionnel très motivé (possible problème caché)")
        
        if scores["presentation_quality"] < 30:
            risks.append("Présentation très pauvre peut cacher des défauts")
        
        if not car.description or len(car.description) < 30:
            risks.append("Description insuffisante")
        
        text = f"{car.title} {car.description}".lower()
        risk_keywords = ["accident", "sinistre", "réparation", "choc", "rayure", "problème"]
        for keyword in risk_keywords:
            if keyword in text:
                risks.append(f"Mention de '{keyword}' dans l'annonce")
        
        return risks

    def _determine_market_position(self, gem_score: float) -> str:
        """Determine market position based on gem score"""
        if gem_score > 80:
            return "extremely_undervalued"
        elif gem_score > 65:
            return "undervalued"
        elif gem_score > 35:
            return "fair_value"
        else:
            return "overpriced"

    def _calculate_confidence(self, scores: dict, car: Car) -> float:
        """Calculate confidence level in the analysis"""
        confidence = 0.5  # Base confidence
        
        # More data = higher confidence
        if car.price and car.year and car.mileage:
            confidence += 0.2
        
        if car.description and len(car.description) > 100:
            confidence += 0.1
        
        if car.images and len(json.loads(car.images)) > 3:
            confidence += 0.1
        
        # Consistent scores = higher confidence
        score_variance = sum((score - 50) ** 2 for score in scores.values()) / len(scores)
        if score_variance < 500:  # Low variance
            confidence += 0.1
        
        return min(1.0, confidence)

    async def analyze_all_active_cars(self, db: Session):
        """Analyze all active cars for gems"""
        active_cars = db.query(Car).filter(Car.is_active == True).all()
        
        for car in active_cars:
            try:
                # Skip if already analyzed recently
                existing = db.query(GemScore).filter(
                    GemScore.car_id == car.id,
                    GemScore.created_at > datetime.utcnow() - timedelta(hours=6)
                ).first()
                
                if existing:
                    continue
                
                # Calculate gem score
                analysis = self.calculate_gem_score(car, db)
                
                # Save to database
                gem_score = GemScore(
                    car_id=car.id,
                    gem_score=analysis["gem_score"],
                    reasons=analysis["reasons"],
                    profit_potential=analysis["profit_potential"],
                    risk_factors=analysis["risk_factors"],
                    market_position=analysis["market_position"],
                    confidence_level=analysis["confidence_level"]
                )
                
                db.add(gem_score)
                db.commit()
                
                print(f"✅ Analyzed car {car.id}: Gem Score {analysis['gem_score']}")
                
            except Exception as e:
                print(f"❌ Error analyzing car {car.id}: {e}")
                continue

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    detector = HiddenGemDetector()
    db = SessionLocal()
    
    # Test with first car
    car = db.query(Car).first()
    if car:
        analysis = detector.calculate_gem_score(car, db)
        print(f"Car: {car.title}")
        print(f"Gem Score: {analysis['gem_score']}")
        print(f"Reasons: {analysis['reasons']}")
        print(f"Profit Potential: {analysis['profit_potential']}€")
    
    db.close()