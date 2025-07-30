import json
import re
from datetime import datetime, timedelta
from statistics import mean, median
import anthropic
import os
from sqlalchemy.orm import Session
from enhanced_database import Car, InvestmentScore, GemScore, MarketPulse, SocialSentiment
import uuid

class InvestmentGradeScorer:
    def __init__(self):
        try:
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            ) if os.getenv("ANTHROPIC_API_KEY") else None
        except Exception as e:
            print(f"Warning: Anthropic client initialization failed in investment_grade_scorer: {e}")
            self.anthropic_client = None
        
        # Investment grade definitions
        self.grade_thresholds = {
            "A+": 90,  # Exceptional investment opportunity
            "A": 80,   # Excellent investment
            "B+": 70,  # Very good investment
            "B": 60,   # Good investment
            "C+": 50,  # Fair investment
            "C": 40,   # Poor investment
            "D": 0     # Avoid
        }
        
        # Car categories with different investment profiles
        self.investment_categories = {
            "classic": {
                "age_range": (20, 50),
                "appreciation_potential": "high",
                "liquidity": "medium",
                "key_factors": ["rarity", "condition", "provenance", "originality"]
            },
            "modern_classic": {
                "age_range": (15, 25),
                "appreciation_potential": "medium",
                "liquidity": "high",
                "key_factors": ["desirability", "limited_production", "condition"]
            },
            "depreciation_floor": {
                "age_range": (8, 15),
                "appreciation_potential": "low",
                "liquidity": "high",
                "key_factors": ["reliability", "maintenance_costs", "brand_strength"]
            },
            "commodity": {
                "age_range": (0, 8),
                "appreciation_potential": "negative",
                "liquidity": "very_high",
                "key_factors": ["depreciation_rate", "market_saturation"]
            }
        }
        
        # Collector interest indicators
        self.collector_indicators = {
            "high": ["ferrari", "porsche", "lamborghini", "aston martin", "mclaren"],
            "medium": ["bmw m", "mercedes amg", "audi rs", "alfa romeo", "lotus"],
            "low": ["volkswagen", "renault sport", "peugeot gti", "ford st", "honda type r"],
            "minimal": ["citroën", "fiat", "opel", "nissan", "hyundai"]
        }
        
        # Rarity factors
        self.rarity_multipliers = {
            "production_numbers": {
                "under_1000": 2.5,
                "1000_5000": 2.0,
                "5000_10000": 1.5,
                "10000_50000": 1.2,
                "over_50000": 1.0
            },
            "special_editions": {
                "limited_edition": 1.8,
                "commemorative": 1.6,
                "first_last_production": 1.4,
                "special_color": 1.2,
                "standard": 1.0
            }
        }
        
        # Historical performance data (simplified)
        self.historical_performance = {
            "porsche_911": {"5y_return": 15, "10y_return": 45, "volatility": "medium"},
            "bmw_m3": {"5y_return": 8, "10y_return": 25, "volatility": "medium"},
            "ferrari": {"5y_return": 25, "10y_return": 80, "volatility": "high"},
            "mercedes_amg": {"5y_return": 5, "10y_return": 20, "volatility": "low"},
            "audi_rs": {"5y_return": 3, "10y_return": 15, "volatility": "low"}
        }

    def calculate_investment_grade(self, car: Car, db: Session) -> dict:
        """Calculate comprehensive investment grade for a car"""
        
        # Determine investment category
        current_age = datetime.now().year - (car.year or 2000)
        investment_category = self._categorize_investment_type(car, current_age)
        
        # Calculate core investment metrics
        appreciation_potential = self._calculate_appreciation_potential(car, current_age, investment_category, db)
        liquidity_score = self._assess_liquidity(car, investment_category, db)
        rarity_factor = self._calculate_rarity_factor(car)
        collector_interest = self._assess_collector_interest(car)
        
        # Get market context
        market_context = self._get_market_context(car, db)
        
        # Calculate risk factors
        risk_assessment = self._assess_investment_risks(car, current_age, db)
        
        # Get historical performance if available
        historical_performance = self._get_historical_performance(car)
        
        # Calculate overall investment score
        investment_score = self._calculate_overall_score(
            appreciation_potential, liquidity_score, rarity_factor, 
            collector_interest, risk_assessment, market_context
        )
        
        # Determine investment grade
        investment_grade = self._assign_investment_grade(investment_score)
        
        # Generate hold recommendation
        hold_recommendation = self._generate_hold_recommendation(
            investment_category, appreciation_potential, liquidity_score, risk_assessment
        )
        
        # Generate AI insights
        ai_insights = self._generate_ai_investment_insights(car, investment_score, investment_category)
        
        return {
            "car_info": {
                "id": car.id,
                "title": car.title,
                "year": car.year,
                "price": car.price,
                "age": current_age
            },
            "investment_grade": investment_grade,
            "investment_score": investment_score,
            "investment_category": investment_category,
            "metrics": {
                "appreciation_potential": appreciation_potential,
                "liquidity_score": liquidity_score,
                "rarity_factor": rarity_factor,
                "collector_interest": collector_interest
            },
            "market_context": market_context,
            "risk_assessment": risk_assessment,
            "historical_performance": historical_performance,
            "hold_recommendation": hold_recommendation,
            "ai_insights": ai_insights,
            "investment_summary": self._generate_investment_summary(
                investment_grade, appreciation_potential, hold_recommendation
            )
        }

    def _categorize_investment_type(self, car: Car, age: int) -> str:
        """Categorize the type of investment this car represents"""
        
        for category, profile in self.investment_categories.items():
            min_age, max_age = profile["age_range"]
            if min_age <= age <= max_age:
                # Additional checks for special categories
                if category == "classic" and not self._has_classic_potential(car):
                    continue
                elif category == "modern_classic" and not self._has_modern_classic_appeal(car):
                    continue
                return category
        
        return "commodity"  # Default

    def _has_classic_potential(self, car: Car) -> bool:
        """Check if car has classic/collectible potential"""
        title_lower = car.title.lower()
        
        classic_indicators = [
            "ferrari", "porsche", "lamborghini", "aston martin", "maserati",
            "jaguar", "triumph", "austin healey", "mg", "alpine"
        ]
        
        return any(indicator in title_lower for indicator in classic_indicators)

    def _has_modern_classic_appeal(self, car: Car) -> bool:
        """Check if car has modern classic appeal"""
        title_lower = car.title.lower()
        
        modern_classic_indicators = [
            "m3", "m5", "amg", "rs4", "rs6", "type r", "sti", "evo",
            "sport", "gti", "turbo", "s line", "edition", "limited"
        ]
        
        return any(indicator in title_lower for indicator in modern_classic_indicators)

    def _calculate_appreciation_potential(self, car: Car, age: int, category: str, db: Session) -> float:
        """Calculate appreciation potential (-100 to +100)"""
        
        base_potential = {
            "classic": 30,
            "modern_classic": 15,
            "depreciation_floor": 5,
            "commodity": -20
        }.get(category, 0)
        
        # Adjust based on brand prestige
        brand_multiplier = self._get_brand_prestige_multiplier(car.title)
        base_potential *= brand_multiplier
        
        # Adjust based on rarity
        rarity_bonus = self._calculate_rarity_factor(car) * 20
        base_potential += rarity_bonus
        
        # Adjust based on market sentiment
        sentiment_data = db.query(SocialSentiment).filter(
            SocialSentiment.make_model.ilike(f"%{car.title.split()[0]}%")
        ).first()
        
        if sentiment_data and sentiment_data.sentiment_score > 0.3:
            base_potential += 10
        elif sentiment_data and sentiment_data.sentiment_score < -0.2:
            base_potential -= 10
        
        # Age-specific adjustments
        if category == "classic":
            # Sweet spot for classics is 25-35 years
            if 25 <= age <= 35:
                base_potential += 15
            elif age > 40:
                base_potential += 10  # Very rare/historic
        
        elif category == "modern_classic":
            # Modern classics appreciate as they become rarer
            if 18 <= age <= 22:
                base_potential += 10
        
        # Condition impact (if we have gem score)
        gem_score = db.query(GemScore).filter(GemScore.car_id == car.id).first()
        if gem_score:
            if gem_score.gem_score > 80:
                base_potential += 15  # Exceptional condition
            elif gem_score.gem_score < 40:
                base_potential -= 20  # Poor condition hurts appreciation
        
        return max(-100, min(100, base_potential))

    def _get_brand_prestige_multiplier(self, title: str) -> float:
        """Get brand prestige multiplier"""
        title_lower = title.lower()
        
        if any(brand in title_lower for brand in ["ferrari", "lamborghini", "mclaren"]):
            return 2.0
        elif any(brand in title_lower for brand in ["porsche", "aston martin", "bentley"]):
            return 1.8
        elif any(brand in title_lower for brand in ["bmw", "mercedes", "audi"]):
            return 1.3
        elif any(brand in title_lower for brand in ["jaguar", "volvo", "saab"]):
            return 1.1
        else:
            return 1.0

    def _assess_liquidity(self, car: Car, category: str, db: Session) -> int:
        """Assess liquidity score (0-100)"""
        
        base_liquidity = {
            "classic": 40,      # Lower liquidity, niche market
            "modern_classic": 70, # Good liquidity, broad appeal
            "depreciation_floor": 85, # High liquidity
            "commodity": 95     # Very high liquidity
        }.get(category, 60)
        
        # Adjust based on price range
        if car.price:
            if car.price < 10000:
                base_liquidity += 10  # Easier to sell cheaper cars
            elif car.price > 50000:
                base_liquidity -= 15  # Harder to sell expensive cars
            elif car.price > 100000:
                base_liquidity -= 25  # Very limited buyer pool
        
        # Adjust based on brand popularity
        title_lower = car.title.lower()
        if any(brand in title_lower for brand in ["bmw", "mercedes", "audi", "volkswagen"]):
            base_liquidity += 10  # Popular brands easier to sell
        elif any(brand in title_lower for brand in ["ferrari", "lamborghini", "maserati"]):
            base_liquidity -= 10  # Exotic cars have limited buyers
        
        # Market saturation check
        market_pulse = db.query(MarketPulse).filter(
            MarketPulse.make_model.ilike(f"%{car.title.split()[0]}%")
        ).first()
        
        if market_pulse and market_pulse.market_saturation > 70:
            base_liquidity -= 15  # Oversaturated market
        elif market_pulse and market_pulse.market_saturation < 30:
            base_liquidity += 10  # Undersupplied market
        
        return max(0, min(100, base_liquidity))

    def _calculate_rarity_factor(self, car: Car) -> float:
        """Calculate rarity factor (0-3.0)"""
        
        title_lower = car.title.lower()
        rarity_score = 1.0  # Base rarity
        
        # Check for limited edition indicators
        limited_indicators = [
            "limited", "edition", "série limitée", "numérotée",
            "collector", "anniversary", "commemorative"
        ]
        
        if any(indicator in title_lower for indicator in limited_indicators):
            rarity_score *= 1.8
        
        # Check for special variants
        special_variants = [
            "rs", "amg", "m sport", "gti", "turbo s", "gt",
            "competition", "performance", "black series"
        ]
        
        if any(variant in title_lower for variant in special_variants):
            rarity_score *= 1.4
        
        # First/last year models
        if car.year:
            title_with_year = f"{car.title} {car.year}"
            if "first year" in title_with_year.lower() or "last year" in title_with_year.lower():
                rarity_score *= 1.3
        
        # Manual transmission bonus (becoming rare)
        if any(term in title_lower for term in ["manuel", "manual", "boîte manuelle"]):
            rarity_score *= 1.2
        
        # Rare colors
        rare_colors = ["jaune", "orange", "violet", "vert", "yellow", "orange", "purple", "green"]
        if any(color in title_lower for color in rare_colors):
            rarity_score *= 1.1
        
        return min(3.0, rarity_score)

    def _assess_collector_interest(self, car: Car) -> int:
        """Assess collector interest level (0-100)"""
        
        title_lower = car.title.lower()
        
        # Check collector interest by brand/model
        for interest_level, models in self.collector_indicators.items():
            if any(model in title_lower for model in models):
                return {
                    "high": 90,
                    "medium": 70,
                    "low": 45,
                    "minimal": 20
                }.get(interest_level, 30)
        
        # Age-based collector interest
        if car.year:
            age = datetime.now().year - car.year
            if 20 <= age <= 30:
                return 60  # Sweet spot for emerging classics
            elif 15 <= age <= 20:
                return 45  # Building interest
            elif age > 40:
                return 75  # Historic interest
        
        return 30  # Default minimal interest

    def _get_market_context(self, car: Car, db: Session) -> dict:
        """Get market context for investment assessment"""
        
        # Try to get market pulse data
        make_model = " ".join(car.title.split()[:2])
        market_pulse = db.query(MarketPulse).filter(
            MarketPulse.make_model.ilike(f"%{make_model}%")
        ).first()
        
        context = {
            "trend": "unknown",
            "demand": 50,
            "supply": 50,
            "price_momentum": "stable"
        }
        
        if market_pulse:
            context.update({
                "trend": market_pulse.current_trend,
                "demand": market_pulse.demand_score,
                "supply": 100 - market_pulse.market_saturation,
                "price_momentum": market_pulse.current_trend
            })
        
        return context

    def _assess_investment_risks(self, car: Car, age: int, db: Session) -> dict:
        """Assess investment risks"""
        
        risks = {
            "overall_risk": "medium",
            "risk_factors": [],
            "risk_score": 50  # 0 = no risk, 100 = very high risk
        }
        
        # Age-related risks
        if age > 20:
            risks["risk_factors"].append("Parts availability may become limited")
            risks["risk_score"] += 10
        
        if age > 30:
            risks["risk_factors"].append("Maintenance expertise increasingly rare")
            risks["risk_score"] += 15
        
        # Price-related risks
        if car.price and car.price > 75000:
            risks["risk_factors"].append("High-value asset - insurance and storage costs")
            risks["risk_score"] += 10
        
        # Brand-related risks
        title_lower = car.title.lower()
        if any(brand in title_lower for brand in ["ferrari", "lamborghini", "mclaren"]):
            risks["risk_factors"].append("Exotic car - high maintenance and repair costs")
            risks["risk_score"] += 20
        
        # Get gem score for condition risk
        gem_score = db.query(GemScore).filter(GemScore.car_id == car.id).first()
        if gem_score and gem_score.gem_score < 50:
            risks["risk_factors"].append("Below-average condition affects investment potential")
            risks["risk_score"] += 15
        
        # Market risks
        market_context = self._get_market_context(car, db)
        if market_context["trend"] == "falling":
            risks["risk_factors"].append("Declining market trend")
            risks["risk_score"] += 10
        
        # Determine overall risk level
        if risks["risk_score"] < 40:
            risks["overall_risk"] = "low"
        elif risks["risk_score"] < 70:
            risks["overall_risk"] = "medium"
        else:
            risks["overall_risk"] = "high"
        
        return risks

    def _get_historical_performance(self, car: Car) -> dict:
        """Get historical performance data if available"""
        
        title_lower = car.title.lower()
        
        # Try to match with historical data
        for model_key, performance in self.historical_performance.items():
            if model_key.replace("_", " ") in title_lower:
                return performance
        
        # Generic performance based on category
        if any(brand in title_lower for brand in ["ferrari", "porsche", "lamborghini"]):
            return {"5y_return": 12, "10y_return": 35, "volatility": "high"}
        elif any(brand in title_lower for brand in ["bmw", "mercedes", "audi"]):
            return {"5y_return": 3, "10y_return": 18, "volatility": "medium"}
        else:
            return {"5y_return": -5, "10y_return": 5, "volatility": "low"}

    def _calculate_overall_score(self, appreciation: float, liquidity: int, rarity: float, 
                               collector: int, risk: dict, market: dict) -> int:
        """Calculate overall investment score (0-100)"""
        
        # Weighted scoring
        score = 0
        
        # Appreciation potential (30% weight)
        appreciation_score = max(0, (appreciation + 100) / 2)  # Convert -100/+100 to 0-100
        score += appreciation_score * 0.30
        
        # Liquidity (20% weight)
        score += liquidity * 0.20
        
        # Rarity factor (20% weight)
        rarity_score = min(100, (rarity / 3.0) * 100)  # Convert 0-3 to 0-100
        score += rarity_score * 0.20
        
        # Collector interest (15% weight)
        score += collector * 0.15
        
        # Risk adjustment (10% weight, inverted)
        risk_bonus = (100 - risk["risk_score"]) * 0.10
        score += risk_bonus
        
        # Market momentum bonus (5% weight)
        market_bonus = 0
        if market["trend"] == "rising":
            market_bonus = 10
        elif market["trend"] == "falling":
            market_bonus = -10
        
        score += market_bonus * 0.05
        
        return max(0, min(100, int(score)))

    def _assign_investment_grade(self, score: int) -> str:
        """Assign investment grade based on score"""
        
        for grade, threshold in self.grade_thresholds.items():
            if score >= threshold:
                return grade
        
        return "D"

    def _generate_hold_recommendation(self, category: str, appreciation: float, 
                                    liquidity: int, risk: dict) -> str:
        """Generate hold period recommendation"""
        
        # Base recommendations by category
        if category == "classic":
            if appreciation > 20:
                return "long"  # 7+ years
            else:
                return "medium"  # 3-7 years
        elif category == "modern_classic":
            if appreciation > 10:
                return "long"
            else:
                return "medium"
        elif category == "depreciation_floor":
            return "medium"
        else:  # commodity
            return "short"  # 0-3 years

    def _generate_ai_investment_insights(self, car: Car, score: int, category: str) -> dict:
        """Generate AI insights about investment potential"""
        
        if not self.anthropic_client:
            return {"error": "AI analysis not available"}
        
        try:
            prompt = f"""
            Analysez le potentiel d'investissement de cette voiture française:
            
            Voiture: {car.title}
            Année: {car.year}
            Prix: {car.price}€
            Score d'investissement: {score}/100
            Catégorie: {category}
            
            Fournissez une analyse d'investissement en JSON avec:
            1. investment_thesis: thèse d'investissement principale
            2. value_drivers: facteurs clés de valorisation
            3. timing_considerations: considérations de timing
            4. exit_strategy: stratégie de sortie recommandée
            5. comparable_assets: actifs comparables pour benchmarking
            6. market_positioning: positionnement sur le marché
            
            Répondez uniquement en JSON français.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return json.loads(message.content[0].text)
            
        except Exception as e:
            return {"error": f"AI insights failed: {str(e)}"}

    def _generate_investment_summary(self, grade: str, appreciation: float, hold_period: str) -> str:
        """Generate human-readable investment summary"""
        
        grade_descriptions = {
            "A+": "Investissement exceptionnel - Potentiel élevé avec risques maîtrisés",
            "A": "Excellent investissement - Forte probabilité de plus-value",
            "B+": "Très bon investissement - Potentiel intéressant à moyen terme",
            "B": "Bon investissement - Rendement attendu positif",
            "C+": "Investissement correct - Risques et rendements équilibrés",
            "C": "Investissement faible - Rendement incertain",
            "D": "À éviter - Risque de perte élevé"
        }
        
        hold_descriptions = {
            "short": "court terme (0-3 ans)",
            "medium": "moyen terme (3-7 ans)", 
            "long": "long terme (7+ ans)"
        }
        
        appreciation_desc = "forte appréciation" if appreciation > 15 else "appréciation modérée" if appreciation > 0 else "dépréciation probable"
        
        summary = f"{grade_descriptions.get(grade, 'Grade inconnu')}. "
        summary += f"Perspective de {appreciation_desc} sur {hold_descriptions.get(hold_period, 'horizon indéterminé')}."
        
        return summary

    def save_investment_score(self, car: Car, score_data: dict, db: Session) -> str:
        """Save investment score to database"""
        
        investment_score = InvestmentScore(
            id=str(uuid.uuid4()),
            car_id=car.id,
            investment_grade=score_data["investment_grade"],
            appreciation_potential=score_data["metrics"]["appreciation_potential"],
            liquidity_score=score_data["metrics"]["liquidity_score"],
            rarity_factor=score_data["metrics"]["rarity_factor"],
            collector_interest=score_data["metrics"]["collector_interest"],
            historical_performance=score_data["historical_performance"],
            risk_assessment=score_data["risk_assessment"],
            hold_recommendation=score_data["hold_recommendation"]
        )
        
        db.add(investment_score)
        db.commit()
        
        return investment_score.id

    def get_investment_insights(self, car_id: str, db: Session) -> dict:
        """Get investment insights for a specific car"""
        
        investment = db.query(InvestmentScore).filter(
            InvestmentScore.car_id == car_id
        ).first()
        
        if not investment:
            return {"message": "No investment analysis available"}
        
        return {
            "car_id": investment.car_id,
            "investment_grade": investment.investment_grade,
            "appreciation_potential": investment.appreciation_potential,
            "liquidity_score": investment.liquidity_score,
            "rarity_factor": investment.rarity_factor,
            "collector_interest": investment.collector_interest,
            "risk_assessment": investment.risk_assessment,
            "hold_recommendation": investment.hold_recommendation,
            "calculated_at": investment.calculated_at.isoformat()
        }

    def get_top_investment_opportunities(self, db: Session, limit: int = 10) -> list:
        """Get top investment opportunities"""
        
        top_investments = db.query(InvestmentScore).filter(
            InvestmentScore.investment_grade.in_(["A+", "A", "B+"])
        ).order_by(
            InvestmentScore.appreciation_potential.desc(),
            InvestmentScore.liquidity_score.desc()
        ).limit(limit).all()
        
        opportunities = []
        for investment in top_investments:
            car = db.query(Car).filter(Car.id == investment.car_id).first()
            if car:
                opportunities.append({
                    "car": {
                        "id": car.id,
                        "title": car.title,
                        "year": car.year,
                        "price": car.price
                    },
                    "investment_grade": investment.investment_grade,
                    "appreciation_potential": investment.appreciation_potential,
                    "liquidity_score": investment.liquidity_score,
                    "hold_recommendation": investment.hold_recommendation
                })
        
        return opportunities

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    scorer = InvestmentGradeScorer()
    db = SessionLocal()
    
    # Test with cars that might have investment potential
    cars = db.query(Car).filter(
        Car.year.isnot(None),
        Car.price.isnot(None)
    ).limit(5).all()
    
    for car in cars:
        print(f"\nAnalyzing investment potential for: {car.title}")
        investment_analysis = scorer.calculate_investment_grade(car, db)
        
        print(f"Investment Grade: {investment_analysis['investment_grade']}")
        print(f"Investment Score: {investment_analysis['investment_score']}/100")
        print(f"Category: {investment_analysis['investment_category']}")
        print(f"Appreciation Potential: {investment_analysis['metrics']['appreciation_potential']:.1f}%")
        print(f"Hold Recommendation: {investment_analysis['hold_recommendation']}")
        print(f"Summary: {investment_analysis['investment_summary']}")
        
        # Save analysis
        score_id = scorer.save_investment_score(car, investment_analysis, db)
        print(f"Analysis saved with ID: {score_id}")
    
    # Get top opportunities
    print(f"\nTop Investment Opportunities:")
    opportunities = scorer.get_top_investment_opportunities(db, 3)
    for i, opp in enumerate(opportunities, 1):
        print(f"{i}. {opp['car']['title']} - Grade: {opp['investment_grade']} - {opp['appreciation_potential']:.1f}% potential")
    
    db.close()