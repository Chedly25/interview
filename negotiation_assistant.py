import re
import json
from datetime import datetime, timedelta
import anthropic
import os
from sqlalchemy.orm import Session
from enhanced_database import Car, NegotiationStrategy, NegotiationOutcome, GemScore, ParsedListing
import uuid

class NegotiationAssistantPro:
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ) if os.getenv("ANTHROPIC_API_KEY") else None
        
        # French negotiation patterns and cultural insights
        self.seller_psychology_patterns = {
            "desperate": [
                "urgent", "déménagement", "divorce", "décès", "vite", "rapide",
                "besoin d'argent", "fin de mois", "mutation"
            ],
            "proud": [
                "jamais accidenté", "première main", "excellent état", "soigné",
                "garage", "entretien suivi", "full option"
            ],
            "professional": [
                "garantie", "reprise possible", "financement", "crédit",
                "livraison", "immatriculation"
            ],
            "emotional": [
                "regret", "dommage", "malheureusement", "contraint",
                "adoré", "choyé", "bébé"
            ]
        }
        
        # French cultural negotiation approaches
        self.cultural_approaches = {
            "respectful": {
                "greeting": "Bonjour, j'espère que vous allez bien.",
                "interest": "Je suis très intéressé par votre véhicule.",
                "transition": "J'aimerais discuter du prix si c'est possible."
            },
            "direct": {
                "greeting": "Bonjour,",
                "interest": "Votre voiture m'intéresse.",
                "transition": "Quel serait votre meilleur prix?"
            },
            "empathetic": {
                "greeting": "Bonjour, j'espère que tout va bien pour vous.",
                "interest": "Je comprends que vous devez vendre votre voiture.",
                "transition": "Pourriez-vous m'aider sur le prix?"
            }
        }
        
        # Price negotiation strategies
        self.negotiation_tactics = {
            "immediate_inspection": "Propose inspection immédiate pour justifier baisse",
            "cash_payment": "Paiement comptant immédiat",
            "bulk_purchase": "Intérêt pour plusieurs véhicules si prix groupé",
            "quick_decision": "Décision rapide contre meilleur prix",
            "competitor_comparison": "Comparaison avec annonces similaires",
            "repair_costs": "Négociation basée sur réparations à prévoir",
            "market_expertise": "Expertise du marché pour justifier offre",
            "win_win": "Recherche d'accord équitable pour les deux parties"
        }

    def generate_negotiation_strategy(self, car: Car, db: Session) -> dict:
        """Generate comprehensive negotiation strategy for a specific car"""
        
        # Analyze seller psychology
        seller_profile = self._analyze_seller_psychology(car)
        
        # Get market context
        market_context = self._get_market_context(car, db)
        
        # Get additional insights from other AI features
        gem_analysis = db.query(GemScore).filter(GemScore.car_id == car.id).first()
        parsed_listing = db.query(ParsedListing).filter(ParsedListing.car_id == car.id).first()
        
        # Generate price strategy
        price_strategy = self._calculate_price_strategy(car, market_context, gem_analysis)
        
        # Create cultural approach
        cultural_approach = self._select_cultural_approach(seller_profile, car)
        
        # Generate conversation scripts
        scripts = self._generate_conversation_scripts(car, seller_profile, price_strategy, cultural_approach)
        
        # Calculate success probability
        success_probability = self._calculate_success_probability(
            seller_profile, market_context, price_strategy, car
        )
        
        strategy = {
            "seller_psychology": seller_profile,
            "market_context": market_context,
            "price_strategy": price_strategy,
            "cultural_approach": cultural_approach,
            "conversation_scripts": scripts,
            "success_probability": success_probability,
            "timing_recommendations": self._get_timing_recommendations(car, seller_profile),
            "red_flags_to_avoid": self._identify_negotiation_red_flags(car, parsed_listing),
            "leverage_points": self._identify_leverage_points(car, gem_analysis, parsed_listing),
            "fallback_strategies": self._create_fallback_strategies(price_strategy)
        }
        
        # Use Claude for advanced strategy refinement
        if self.anthropic_client:
            strategy = self._refine_strategy_with_ai(car, strategy)
        
        return strategy

    def _analyze_seller_psychology(self, car: Car) -> dict:
        """Analyze seller psychology from listing"""
        text = f"{car.title} {car.description}".lower()
        
        psychology_scores = {}
        detected_patterns = []
        
        for psych_type, patterns in self.seller_psychology_patterns.items():
            score = 0
            found_patterns = []
            
            for pattern in patterns:
                if pattern in text:
                    score += 1
                    found_patterns.append(pattern)
            
            psychology_scores[psych_type] = score
            if found_patterns:
                detected_patterns.extend(found_patterns)
        
        # Determine primary psychology
        primary_psychology = max(psychology_scores, key=psychology_scores.get)
        confidence = psychology_scores[primary_psychology] / len(self.seller_psychology_patterns[primary_psychology])
        
        # Additional analysis
        urgency_level = self._assess_urgency_level(text)
        price_flexibility = self._assess_price_flexibility(car, text)
        
        return {
            "primary_type": primary_psychology,
            "confidence": min(1.0, confidence),
            "psychology_scores": psychology_scores,
            "detected_patterns": detected_patterns,
            "urgency_level": urgency_level,
            "price_flexibility": price_flexibility,
            "seller_type": car.seller_type,
            "listing_quality": self._assess_listing_quality(car)
        }

    def _assess_urgency_level(self, text: str) -> str:
        """Assess seller urgency level"""
        high_urgency = ["urgent", "vite", "rapide", "immédiat", "fin mois", "départ"]
        medium_urgency = ["négociable", "étudié", "discutable", "souple"]
        
        high_count = sum(1 for word in high_urgency if word in text)
        medium_count = sum(1 for word in medium_urgency if word in text)
        
        if high_count > 0:
            return "high"
        elif medium_count > 0:
            return "medium"
        else:
            return "low"

    def _assess_price_flexibility(self, car: Car, text: str) -> float:
        """Assess price flexibility (0-1)"""
        flexibility_score = 0.5  # Base
        
        # Positive flexibility indicators
        flexible_indicators = ["négociable", "discutable", "débattre", "étudié", "souple"]
        for indicator in flexible_indicators:
            if indicator in text:
                flexibility_score += 0.1
        
        # Negative flexibility indicators
        firm_indicators = ["ferme", "fixe", "non négociable", "prix serré"]
        for indicator in firm_indicators:
            if indicator in text:
                flexibility_score -= 0.2
        
        # Professional sellers typically less flexible
        if car.seller_type == "professionnel":
            flexibility_score -= 0.1
        
        return max(0.0, min(1.0, flexibility_score))

    def _assess_listing_quality(self, car: Car) -> str:
        """Assess overall listing quality"""
        score = 0
        
        if car.description and len(car.description) > 200:
            score += 2
        elif car.description and len(car.description) > 100:
            score += 1
        
        if car.images:
            image_count = len(json.loads(car.images))
            if image_count >= 8:
                score += 2
            elif image_count >= 5:
                score += 1
        
        if car.year and car.mileage and car.fuel_type:
            score += 1
        
        if score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"

    def _get_market_context(self, car: Car, db: Session) -> dict:
        """Get market context for negotiation"""
        if not car.price:
            return {"error": "No price available"}
        
        # Get similar cars
        similar_cars = db.query(Car).filter(
            Car.year.between(car.year - 2, car.year + 2) if car.year else True,
            Car.mileage.between(car.mileage - 30000, car.mileage + 30000) if car.mileage else True,
            Car.price.isnot(None),
            Car.is_active == True,
            Car.id != car.id
        ).limit(15).all()
        
        if len(similar_cars) < 3:
            return {"insufficient_data": True}
        
        prices = [c.price for c in similar_cars]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        # Calculate market position
        percentile = sum(1 for p in prices if p <= car.price) / len(prices)
        
        return {
            "similar_cars_count": len(similar_cars),
            "average_market_price": int(avg_price),
            "price_range": {"min": min_price, "max": max_price},
            "car_price_percentile": percentile,
            "market_position": "above_market" if percentile > 0.7 else "below_market" if percentile < 0.3 else "market_average",
            "negotiation_room": max(0, car.price - min_price),
            "market_context_strength": "strong" if len(similar_cars) > 10 else "moderate"
        }

    def _calculate_price_strategy(self, car: Car, market_context: dict, gem_analysis) -> dict:
        """Calculate price negotiation strategy"""
        if not car.price or "error" in market_context:
            return {"error": "Insufficient data for price strategy"}
        
        # Base negotiation range (typical 5-15% in France)
        base_negotiation = car.price * 0.10  # 10% base
        
        # Adjust based on market position
        if market_context.get("market_position") == "above_market":
            negotiation_room = car.price * 0.15  # 15% if overpriced
        elif market_context.get("market_position") == "below_market":
            negotiation_room = car.price * 0.05  # 5% if underpriced
        else:
            negotiation_room = base_negotiation
        
        # Adjust based on gem analysis
        if gem_analysis and gem_analysis.gem_score > 75:
            negotiation_room *= 0.7  # Less room if it's a gem
        elif gem_analysis and gem_analysis.gem_score < 40:
            negotiation_room *= 1.3  # More room if overpriced
        
        # Calculate price points
        target_discount = int(negotiation_room)
        conservative_offer = car.price - int(negotiation_room * 0.6)
        aggressive_offer = car.price - int(negotiation_room * 1.2)
        final_walk_away = car.price - int(negotiation_room * 0.3)
        
        return {
            "original_price": car.price,
            "estimated_negotiation_room": target_discount,
            "price_points": {
                "aggressive_opening": aggressive_offer,
                "conservative_opening": conservative_offer,
                "target_price": car.price - target_discount,
                "walk_away_price": final_walk_away
            },
            "recommended_opening": conservative_offer,
            "strategy_type": "conservative" if gem_analysis and gem_analysis.gem_score > 60 else "standard"
        }

    def _select_cultural_approach(self, seller_profile: dict, car: Car) -> str:
        """Select appropriate cultural approach for French market"""
        
        if seller_profile["primary_type"] == "emotional":
            return "empathetic"
        elif seller_profile["primary_type"] == "professional":
            return "direct"
        elif seller_profile["urgency_level"] == "high":
            return "respectful"
        else:
            return "respectful"  # Default safe approach in France

    def _generate_conversation_scripts(self, car: Car, seller_profile: dict, price_strategy: dict, cultural_approach: str) -> dict:
        """Generate conversation scripts in French"""
        
        approach = self.cultural_approaches[cultural_approach]
        
        scripts = {
            "opening": {
                "phone": f"{approach['greeting']} Je vous appelle au sujet de votre {car.title}. {approach['interest']}",
                "message": f"{approach['greeting']} Je vous contacte concernant votre annonce pour {car.title}. {approach['interest']} Êtes-vous disponible pour en discuter ?"
            },
            "price_inquiry": {
                "soft": f"J'ai vu le prix affiché à {car.price}€. {approach['transition']}",
                "direct": f"Concernant le prix de {car.price}€, y a-t-il une possibilité de négociation ?",
                "market_based": f"J'ai regardé le marché et je vois des véhicules similaires autour de {price_strategy.get('price_points', {}).get('target_price', car.price)}€. Que pensez-vous de ce prix ?"
            },
            "objection_handling": {
                "price_too_high": "Je comprends votre position. Serait-il possible de se rencontrer à mi-chemin ?",
                "non_negotiable": "Je respecte cela. Y a-t-il d'autres éléments qui pourraient m'aider dans ma décision ?",
                "other_buyers": "C'est une bonne nouvelle pour vous. Si je peux décider rapidement, cela vous aiderait-il ?"
            },
            "closing": {
                "acceptance": f"Parfait ! Je peux venir voir le véhicule dès que possible avec le montant en liquide.",
                "counter_offer": "Je comprends. Ma meilleure offre serait de {price_strategy.get('price_points', {}).get('walk_away_price', car.price)}€. Qu'en pensez-vous ?",
                "walk_away": "Je vous remercie pour votre temps. Si vous changez d'avis, n'hésitez pas à me recontacter."
            }
        }
        
        return scripts

    def _calculate_success_probability(self, seller_profile: dict, market_context: dict, price_strategy: dict, car: Car) -> float:
        """Calculate probability of successful negotiation"""
        base_probability = 0.6  # 60% base in French market
        
        # Seller psychology factors
        if seller_profile["urgency_level"] == "high":
            base_probability += 0.2
        elif seller_profile["urgency_level"] == "low":
            base_probability -= 0.1
        
        # Price flexibility
        base_probability += seller_profile["price_flexibility"] * 0.2
        
        # Market position
        if market_context.get("market_position") == "above_market":
            base_probability += 0.15
        elif market_context.get("market_position") == "below_market":
            base_probability -= 0.1
        
        # Seller type
        if car.seller_type == "particulier":
            base_probability += 0.1
        
        # Listing quality (better listings = less negotiation room)
        if seller_profile["listing_quality"] == "high":
            base_probability -= 0.05
        
        return max(0.1, min(0.95, base_probability))

    def _get_timing_recommendations(self, car: Car, seller_profile: dict) -> dict:
        """Get timing recommendations for negotiation"""
        
        recommendations = {
            "best_times": [],
            "avoid_times": [],
            "urgency_level": seller_profile["urgency_level"]
        }
        
        # Best times based on French culture
        if seller_profile["urgency_level"] == "high":
            recommendations["best_times"].extend([
                "Fin de semaine (vendeur pressé)",
                "Fin de mois (besoins financiers)",
                "Heure de déjeuner (moment détendu)"
            ])
        
        # General good times in France
        recommendations["best_times"].extend([
            "Mardi-Jeudi 10h-12h",
            "Après 17h en semaine",
            "Samedi matin"
        ])
        
        # Times to avoid
        recommendations["avoid_times"].extend([
            "Lundi matin",
            "Vendredi après-midi",
            "Dimanche",
            "Pendant les repas (12h-14h)"
        ])
        
        return recommendations

    def _identify_negotiation_red_flags(self, car: Car, parsed_listing) -> list:
        """Identify what to avoid mentioning in negotiation"""
        red_flags = []
        
        # If we have parsed listing data, use it
        if parsed_listing and parsed_listing.red_flags:
            red_flags.extend([
                f"Éviter de mentionner: {flag}" for flag in parsed_listing.red_flags[:3]
            ])
        
        # General red flags
        text = f"{car.title} {car.description}".lower() if car.description else car.title.lower()
        
        sensitive_topics = [
            ("accident", "Ne pas insister sur l'historique d'accident"),
            ("réparation", "Éviter de mentionner les réparations nécessaires d'emblée"),
            ("urgent", "Ne pas exploiter ouvertement l'urgence du vendeur"),
            ("décès", "Faire preuve de tact concernant les circonstances personnelles")
        ]
        
        for topic, advice in sensitive_topics:
            if topic in text:
                red_flags.append(advice)
        
        return red_flags

    def _identify_leverage_points(self, car: Car, gem_analysis, parsed_listing) -> list:
        """Identify points of leverage for negotiation"""
        leverage_points = []
        
        # Market-based leverage
        if gem_analysis and gem_analysis.gem_score < 50:
            leverage_points.append("Prix au-dessus du marché selon l'analyse")
        
        # Description-based leverage
        if parsed_listing:
            if parsed_listing.missing_information:
                leverage_points.append(f"Informations manquantes: {', '.join(parsed_listing.missing_information[:2])}")
            
            if parsed_listing.seller_credibility < 70:
                leverage_points.append("Description peu détaillée ou crédible")
        
        # Image-based leverage
        if car.images:
            image_count = len(json.loads(car.images))
            if image_count < 5:
                leverage_points.append("Peu de photos disponibles")
        
        # Time-based leverage
        if car.first_seen and (datetime.utcnow() - car.first_seen).days > 14:
            leverage_points.append("Annonce en ligne depuis plus de 2 semaines")
        
        return leverage_points

    def _create_fallback_strategies(self, price_strategy: dict) -> list:
        """Create fallback negotiation strategies"""
        fallbacks = []
        
        if "price_points" in price_strategy:
            fallbacks.extend([
                {
                    "strategy": "Paiement comptant immédiat",
                    "offer": price_strategy["price_points"]["conservative_opening"],
                    "justification": "Élimination des risques de financement"
                },
                {
                    "strategy": "Prise en charge des frais administratifs",
                    "offer": price_strategy["price_points"]["target_price"],
                    "justification": "Simplification pour le vendeur"
                },
                {
                    "strategy": "Inspection immédiate",
                    "offer": price_strategy["price_points"]["walk_away_price"],
                    "justification": "Décision rapide basée sur l'état réel"
                }
            ])
        
        return fallbacks

    def _refine_strategy_with_ai(self, car: Car, strategy: dict) -> dict:
        """Refine strategy using Claude AI"""
        try:
            prompt = f"""
            Analysez cette stratégie de négociation pour une voiture française et proposez des améliorations culturellement appropriées:

            Voiture: {car.title}
            Prix: {car.price}€
            Type vendeur: {car.seller_type}
            
            Stratégie actuelle:
            - Psychologie vendeur: {strategy['seller_psychology']['primary_type']}
            - Probabilité succès: {strategy['success_probability']:.0%}
            - Approche culturelle: {strategy['cultural_approach']}
            
            Améliorez la stratégie en tenant compte:
            1. Des spécificités culturelles françaises
            2. De la psychologie du vendeur détectée
            3. Des meilleures pratiques de négociation automobile
            
            Répondez en JSON avec:
            - improved_approach: approche améliorée
            - cultural_insights: insights culturels spécifiques
            - risk_mitigation: stratégies de réduction des risques
            - success_factors: facteurs clés de succès
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            ai_improvements = json.loads(message.content[0].text)
            strategy["ai_improvements"] = ai_improvements
            
        except Exception as e:
            strategy["ai_improvements"] = {"error": f"AI refinement failed: {str(e)}"}
        
        return strategy

    def save_strategy(self, car: Car, strategy: dict, db: Session) -> str:
        """Save negotiation strategy to database"""
        
        negotiation_strategy = NegotiationStrategy(
            id=str(uuid.uuid4()),
            car_id=car.id,
            strategy_data=strategy,
            seller_psychology=strategy["seller_psychology"],
            price_points=strategy.get("price_strategy", {}).get("price_points", {}),
            scripts=strategy["conversation_scripts"],
            success_probability=strategy["success_probability"],
            cultural_approach=strategy["cultural_approach"]
        )
        
        db.add(negotiation_strategy)
        db.commit()
        
        return negotiation_strategy.id

    def record_outcome(self, car_id: str, strategy_id: str, outcome: str, 
                      final_price: int = None, approach_used: str = None, 
                      lessons: dict = None, db: Session = None) -> dict:
        """Record negotiation outcome for learning"""
        
        original_car = db.query(Car).filter(Car.id == car_id).first()
        discount_achieved = (original_car.price - final_price) if final_price and original_car else 0
        
        outcome_record = NegotiationOutcome(
            id=str(uuid.uuid4()),
            car_id=car_id,
            strategy_id=strategy_id,
            outcome=outcome,
            final_price=final_price,
            discount_achieved=discount_achieved,
            approach_used=approach_used,
            lessons_learned=lessons or {}
        )
        
        db.add(outcome_record)
        db.commit()
        
        return {
            "outcome_id": outcome_record.id,
            "discount_achieved": discount_achieved,
            "success_rate": self._calculate_user_success_rate(db)
        }

    def _calculate_user_success_rate(self, db: Session) -> float:
        """Calculate user's historical success rate"""
        outcomes = db.query(NegotiationOutcome).all()
        if not outcomes:
            return 0.0
        
        successful = sum(1 for o in outcomes if o.outcome == "success")
        return successful / len(outcomes)

    def get_negotiation_insights(self, car_id: str, db: Session) -> dict:
        """Get saved negotiation strategy and insights"""
        strategy = db.query(NegotiationStrategy).filter(
            NegotiationStrategy.car_id == car_id
        ).first()
        
        if not strategy:
            return {"message": "No negotiation strategy found"}
        
        outcomes = db.query(NegotiationOutcome).filter(
            NegotiationOutcome.car_id == car_id
        ).all()
        
        return {
            "strategy": strategy.strategy_data,
            "success_probability": strategy.success_probability,
            "cultural_approach": strategy.cultural_approach,
            "outcomes": [
                {
                    "outcome": o.outcome,
                    "final_price": o.final_price,
                    "discount_achieved": o.discount_achieved,
                    "date": o.created_at.isoformat()
                }
                for o in outcomes
            ],
            "created_at": strategy.created_at.isoformat()
        }

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    assistant = NegotiationAssistantPro()
    db = SessionLocal()
    
    # Test with first car
    car = db.query(Car).filter(Car.price.isnot(None)).first()
    if car:
        print(f"Generating negotiation strategy for: {car.title}")
        strategy = assistant.generate_negotiation_strategy(car, db)
        print(f"Success probability: {strategy['success_probability']:.0%}")
        print(f"Cultural approach: {strategy['cultural_approach']}")
        print(f"Recommended opening: {strategy.get('price_strategy', {}).get('recommended_opening', 'N/A')}€")
        
        # Save strategy
        strategy_id = assistant.save_strategy(car, strategy, db)
        print(f"Strategy saved with ID: {strategy_id}")
    else:
        print("No cars with prices found")
    
    db.close()