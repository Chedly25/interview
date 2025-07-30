import re
import json
import requests
from datetime import datetime, timedelta
from statistics import mean
import anthropic
import os
from sqlalchemy.orm import Session
from enhanced_database import Car, SocialSentiment
import uuid

class SocialSentimentAnalyzer:
    def __init__(self):
        try:
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            ) if os.getenv("ANTHROPIC_API_KEY") else None
        except Exception as e:
            print(f"Warning: Anthropic client initialization failed in social_sentiment_analyzer: {e}")
            self.anthropic_client = None
        
        # French automotive forums and review sites
        self.data_sources = {
            "forum_auto": "https://www.forum-auto.com/",
            "caradisiac": "https://www.caradisiac.com/",
            "largus": "https://www.largus.fr/",
            "auto_plus": "https://www.autoplus.fr/",
            "turbo": "https://www.turbo.fr/"
        }
        
        # Sentiment keywords in French
        self.sentiment_keywords = {
            "positive": {
                "excellent": 0.9, "parfait": 0.8, "génial": 0.8, "superbe": 0.7,
                "très bon": 0.7, "recommande": 0.6, "satisfait": 0.6, "content": 0.5,
                "correct": 0.4, "bien": 0.4, "ok": 0.3, "pas mal": 0.3,
                "fiable": 0.7, "solide": 0.6, "économique": 0.5, "confortable": 0.5
            },
            "negative": {
                "horrible": -0.9, "catastrophique": -0.8, "nul": -0.7, "mauvais": -0.6,
                "décevant": -0.6, "problème": -0.5, "panne": -0.7, "défaut": -0.5,
                "regrette": -0.6, "déçu": -0.5, "éviter": -0.8, "fuyez": -0.9,
                "fragile": -0.4, "cher": -0.3, "bruyant": -0.3, "inconfortable": -0.4
            }
        }
        
        # Common car issues mentioned in forums
        self.common_issues = {
            "moteur": ["casse moteur", "surchauffe", "consommation huile", "bruit moteur"],
            "transmission": ["boîte défaillante", "embrayage", "vitesses difficiles"],
            "électronique": ["panne électronique", "capteurs", "ordinateur de bord"],
            "carrosserie": ["rouille", "peinture", "étanchéité"],
            "freinage": ["plaquettes", "disques", "abs défaillant"],
            "suspension": ["amortisseurs", "ressorts", "bruits suspension"],
            "climatisation": ["clim en panne", "froid insuffisant", "réfrigérant"]
        }
        
        # Reliability indicators
        self.reliability_indicators = {
            "très fiable": 0.9,
            "fiable": 0.7,
            "moyennement fiable": 0.5,
            "peu fiable": 0.3,
            "pas fiable": 0.1
        }

    def analyze_social_sentiment(self, make_model: str, db: Session) -> dict:
        """Analyze social sentiment for a car make/model"""
        
        # Check for existing recent analysis
        existing = db.query(SocialSentiment).filter(
            SocialSentiment.make_model == make_model,
            SocialSentiment.analyzed_at > datetime.utcnow() - timedelta(days=7)
        ).first()
        
        if existing:
            return self._format_sentiment_response(existing)
        
        # Simulate social media and forum analysis
        sentiment_data = self._simulate_social_analysis(make_model)
        
        # Enhance with AI analysis if available
        if self.anthropic_client:
            ai_enhancement = self._enhance_with_ai_analysis(make_model, sentiment_data)
            sentiment_data.update(ai_enhancement)
        
        # Calculate overall scores
        overall_sentiment = self._calculate_overall_sentiment(sentiment_data)
        reputation_data = self._build_reputation_profile(make_model, sentiment_data)
        common_issues = self._extract_common_issues(make_model, sentiment_data)
        owner_satisfaction = self._calculate_owner_satisfaction(sentiment_data)
        reliability_score = self._calculate_reliability_score(sentiment_data, common_issues)
        
        # Save analysis
        sentiment_analysis = SocialSentiment(
            id=str(uuid.uuid4()),
            make_model=make_model,
            platform="aggregated",
            sentiment_score=overall_sentiment,
            reputation_data=reputation_data,
            common_issues=common_issues,
            owner_satisfaction=owner_satisfaction,
            reliability_score=reliability_score
        )
        
        db.add(sentiment_analysis)
        db.commit()
        
        return {
            "make_model": make_model,
            "overall_sentiment": overall_sentiment,
            "reputation_profile": reputation_data,
            "common_issues": common_issues,
            "owner_satisfaction": owner_satisfaction,
            "reliability_score": reliability_score,
            "analysis_summary": self._generate_analysis_summary(overall_sentiment, reputation_data, reliability_score),
            "recommendations": self._generate_recommendations(overall_sentiment, common_issues, reliability_score),
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _simulate_social_analysis(self, make_model: str) -> dict:
        """Simulate social media and forum analysis (in production, use real APIs)"""
        
        # Simulate data collection from various sources
        simulated_data = {
            "forum_posts": self._simulate_forum_analysis(make_model),
            "review_sites": self._simulate_review_analysis(make_model),
            "social_mentions": self._simulate_social_mentions(make_model),
            "owner_testimonials": self._simulate_owner_testimonials(make_model)
        }
        
        return simulated_data

    def _simulate_forum_analysis(self, make_model: str) -> dict:
        """Simulate forum post analysis"""
        
        # Generate realistic forum sentiment based on model characteristics
        model_lower = make_model.lower()
        
        # Assign base sentiment based on brand reputation
        if any(brand in model_lower for brand in ["toyota", "honda", "mazda"]):
            base_sentiment = 0.6  # Generally reliable brands
        elif any(brand in model_lower for brand in ["bmw", "mercedes", "audi"]):
            base_sentiment = 0.4  # Premium but potentially expensive to maintain
        elif any(brand in model_lower for brand in ["renault", "peugeot", "citroën"]):
            base_sentiment = 0.3  # Mixed reputation
        elif any(brand in model_lower for brand in ["fiat", "alfa romeo"]):
            base_sentiment = 0.2  # Lower reliability reputation
        else:
            base_sentiment = 0.4  # Default
        
        # Generate simulated forum posts
        posts = []
        
        # Positive posts
        positive_count = int(50 * (base_sentiment + 0.3))
        for i in range(positive_count):
            posts.append({
                "sentiment": 0.6 + (i % 4) * 0.1,
                "content": f"Très content de ma {make_model}, fiable et économique",
                "source": "forum_auto",
                "date": datetime.utcnow() - timedelta(days=i % 180)
            })
        
        # Negative posts
        negative_count = int(50 * (1 - base_sentiment))
        for i in range(negative_count):
            posts.append({
                "sentiment": -0.4 - (i % 3) * 0.2,
                "content": f"Problèmes récurrents avec ma {make_model}, déçu",
                "source": "caradisiac",
                "date": datetime.utcnow() - timedelta(days=i % 180)
            })
        
        return {
            "total_posts": len(posts),
            "posts": posts,
            "average_sentiment": mean([p["sentiment"] for p in posts]) if posts else 0,
            "engagement_level": "high" if len(posts) > 80 else "medium" if len(posts) > 40 else "low"
        }

    def _simulate_review_analysis(self, make_model: str) -> dict:
        """Simulate automotive review site analysis"""
        
        model_lower = make_model.lower()
        
        # Generate expert review scores
        reviews = []
        
        # Professional reviews tend to be more moderate
        if any(brand in model_lower for brand in ["toyota", "honda"]):
            expert_scores = [7.5, 8.0, 7.8, 8.2, 7.6]
        elif any(brand in model_lower for brand in ["bmw", "mercedes", "audi"]):
            expert_scores = [8.0, 8.5, 8.2, 7.9, 8.1]
        elif any(brand in model_lower for brand in ["renault", "peugeot", "citroën"]):
            expert_scores = [6.8, 7.2, 6.9, 7.0, 6.7]
        else:
            expert_scores = [7.0, 7.2, 6.8, 7.1, 6.9]
        
        for i, score in enumerate(expert_scores):
            reviews.append({
                "publication": ["L'Argus", "Auto Plus", "Caradisiac", "Turbo", "Auto Moto"][i],
                "score": score,
                "normalized_sentiment": (score - 5) / 5,  # Convert to -1 to 1 scale
                "review_date": datetime.utcnow() - timedelta(days=30 * i)
            })
        
        return {
            "professional_reviews": reviews,
            "average_score": mean([r["score"] for r in reviews]),
            "average_sentiment": mean([r["normalized_sentiment"] for r in reviews]),
            "review_count": len(reviews)
        }

    def _simulate_social_mentions(self, make_model: str) -> dict:
        """Simulate social media mentions analysis"""
        
        # Simulate Twitter/Facebook mentions
        mentions = {
            "total_mentions": 450 + hash(make_model) % 300,  # Deterministic randomness
            "positive_mentions": 0,
            "negative_mentions": 0,
            "neutral_mentions": 0,
            "trending_hashtags": [f"#{make_model.replace(' ', '')}", "#automotive", "#carreview"],
            "sentiment_trend": []
        }
        
        # Generate mention distribution
        total = mentions["total_mentions"]
        model_lower = make_model.lower()
        
        if any(brand in model_lower for brand in ["tesla", "bmw", "mercedes"]):
            # Premium brands get more discussion
            mentions["positive_mentions"] = int(total * 0.45)
            mentions["negative_mentions"] = int(total * 0.25)
        else:
            mentions["positive_mentions"] = int(total * 0.35)
            mentions["negative_mentions"] = int(total * 0.35)
        
        mentions["neutral_mentions"] = total - mentions["positive_mentions"] - mentions["negative_mentions"]
        
        # Generate sentiment trend over time
        for i in range(30):  # Last 30 days
            mentions["sentiment_trend"].append({
                "date": (datetime.utcnow() - timedelta(days=i)).isoformat()[:10],
                "sentiment": 0.2 + (hash(f"{make_model}{i}") % 60) / 100  # -0.4 to 0.8
            })
        
        return mentions

    def _simulate_owner_testimonials(self, make_model: str) -> dict:
        """Simulate owner testimonials and experiences"""
        
        testimonials = []
        model_lower = make_model.lower()
        
        # Generate testimonials based on brand characteristics
        testimonial_templates = {
            "positive": [
                "Très satisfait de ma {model}, aucun problème en {years} ans",
                "Excellente voiture, je recommande la {model}",
                "Ma {model} est très fiable, jamais tombé en panne",
                "Parfait rapport qualité-prix avec la {model}"
            ],
            "negative": [
                "Déçu de ma {model}, trop de pannes",
                "Ma {model} a eu beaucoup de problèmes électroniques",
                "Je regrette l'achat de ma {model}, pas fiable",
                "Coûts d'entretien élevés pour ma {model}"
            ],
            "mixed": [
                "Ma {model} est correcte mais sans plus",
                "Quelques soucis avec ma {model} mais globalement ok",
                "Ma {model} vieillit bien malgré quelques défauts"
            ]
        }
        
        # Generate owner experiences
        for sentiment_type in ["positive", "negative", "mixed"]:
            count = {"positive": 15, "negative": 8, "mixed": 7}[sentiment_type]
            
            for i in range(count):
                template = testimonial_templates[sentiment_type][i % len(testimonial_templates[sentiment_type])]
                testimonials.append({
                    "content": template.format(model=make_model, years=2 + i % 8),
                    "sentiment_type": sentiment_type,
                    "ownership_duration": f"{2 + i % 8} ans",
                    "mileage": f"{50000 + i * 15000} km",
                    "verified": i % 3 == 0  # 1/3 are verified owners
                })
        
        return {
            "testimonials": testimonials,
            "total_testimonials": len(testimonials),
            "verified_count": sum(1 for t in testimonials if t["verified"]),
            "sentiment_distribution": {
                "positive": len([t for t in testimonials if t["sentiment_type"] == "positive"]),
                "negative": len([t for t in testimonials if t["sentiment_type"] == "negative"]),
                "mixed": len([t for t in testimonials if t["sentiment_type"] == "mixed"])
            }
        }

    def _enhance_with_ai_analysis(self, make_model: str, sentiment_data: dict) -> dict:
        """Enhance analysis with AI insights"""
        
        if not self.anthropic_client:
            return {}
        
        try:
            # Prepare summary for AI analysis
            forum_sentiment = sentiment_data["forum_posts"]["average_sentiment"]
            review_sentiment = sentiment_data["review_sites"]["average_sentiment"]
            social_positive = sentiment_data["social_mentions"]["positive_mentions"]
            social_negative = sentiment_data["social_mentions"]["negative_mentions"]
            
            prompt = f"""
            Analysez la réputation et le sentiment social pour {make_model} sur le marché français:
            
            Données forum: sentiment moyen {forum_sentiment:.2f}
            Avis experts: sentiment moyen {review_sentiment:.2f}
            Réseaux sociaux: {social_positive} mentions positives vs {social_negative} négatives
            
            Fournissez une analyse en JSON avec:
            1. reputation_summary: résumé de la réputation (excellent/bon/moyen/mauvais)
            2. key_strengths: 3 points forts principaux
            3. main_concerns: 3 préoccupations principales
            4. target_buyer: profil de l'acheteur idéal
            5. comparison_context: position vs concurrents
            6. long_term_outlook: perspective à long terme
            
            Répondez uniquement en JSON français.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {"ai_insights": json.loads(message.content[0].text)}
            
        except Exception as e:
            return {"ai_error": f"AI enhancement failed: {str(e)}"}

    def _calculate_overall_sentiment(self, sentiment_data: dict) -> float:
        """Calculate overall sentiment score (-1 to 1)"""
        
        scores = []
        weights = []
        
        # Forum sentiment (weight: 0.4)
        forum_sentiment = sentiment_data["forum_posts"]["average_sentiment"]
        scores.append(forum_sentiment)
        weights.append(0.4)
        
        # Review sentiment (weight: 0.3)
        review_sentiment = sentiment_data["review_sites"]["average_sentiment"]
        scores.append(review_sentiment)
        weights.append(0.3)
        
        # Social sentiment (weight: 0.3)
        social_data = sentiment_data["social_mentions"]
        total_social = social_data["positive_mentions"] + social_data["negative_mentions"] + social_data["neutral_mentions"]
        if total_social > 0:
            social_sentiment = (social_data["positive_mentions"] - social_data["negative_mentions"]) / total_social
            scores.append(social_sentiment)
            weights.append(0.3)
        
        # Weighted average
        if scores and weights:
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            return weighted_sum / total_weight
        
        return 0.0

    def _build_reputation_profile(self, make_model: str, sentiment_data: dict) -> dict:
        """Build comprehensive reputation profile"""
        
        profile = {
            "overall_reputation": "neutral",
            "key_attributes": [],
            "market_perception": "",
            "owner_loyalty": 0.0,
            "expert_consensus": "",
            "social_buzz": "moderate"
        }
        
        # Determine overall reputation
        forum_sentiment = sentiment_data["forum_posts"]["average_sentiment"]
        review_sentiment = sentiment_data["review_sites"]["average_sentiment"]
        
        avg_sentiment = (forum_sentiment + review_sentiment) / 2
        
        if avg_sentiment > 0.4:
            profile["overall_reputation"] = "excellent"
        elif avg_sentiment > 0.2:
            profile["overall_reputation"] = "good"
        elif avg_sentiment > -0.2:
            profile["overall_reputation"] = "neutral"
        else:
            profile["overall_reputation"] = "poor"
        
        # Key attributes based on model characteristics
        model_lower = make_model.lower()
        
        if any(brand in model_lower for brand in ["toyota", "honda", "mazda"]):
            profile["key_attributes"] = ["Fiabilité", "Économie", "Revente"]
        elif any(brand in model_lower for brand in ["bmw", "mercedes", "audi"]):
            profile["key_attributes"] = ["Prestige", "Performance", "Technologie"]
        elif any(brand in model_lower for brand in ["renault", "peugeot", "citroën"]):
            profile["key_attributes"] = ["Prix abordable", "Réseau service", "Design"]
        else:
            profile["key_attributes"] = ["Rapport qualité-prix", "Praticité", "Confort"]
        
        # Owner loyalty (based on testimonials)
        testimonials = sentiment_data["owner_testimonials"]["sentiment_distribution"]
        total_testimonials = sum(testimonials.values())
        if total_testimonials > 0:
            profile["owner_loyalty"] = testimonials["positive"] / total_testimonials
        
        # Social buzz level
        mention_count = sentiment_data["social_mentions"]["total_mentions"]
        if mention_count > 600:
            profile["social_buzz"] = "high"
        elif mention_count > 300:
            profile["social_buzz"] = "moderate"
        else:
            profile["social_buzz"] = "low"
        
        return profile

    def _extract_common_issues(self, make_model: str, sentiment_data: dict) -> list:
        """Extract common issues mentioned in forums and reviews"""
        
        issues = []
        model_lower = make_model.lower()
        
        # Simulate issue extraction based on brand characteristics
        if any(brand in model_lower for brand in ["bmw", "mercedes", "audi"]):
            issues = [
                {"issue": "Coûts d'entretien élevés", "frequency": 65, "severity": "medium"},
                {"issue": "Électronique complexe", "frequency": 45, "severity": "high"},
                {"issue": "Pièces détachées chères", "frequency": 70, "severity": "medium"}
            ]
        elif any(brand in model_lower for brand in ["renault", "peugeot", "citroën"]):
            issues = [
                {"issue": "Problèmes électroniques", "frequency": 55, "severity": "medium"},
                {"issue": "Finition intérieure", "frequency": 40, "severity": "low"},
                {"issue": "Fiabilité moteur", "frequency": 30, "severity": "high"}
            ]
        elif any(brand in model_lower for brand in ["fiat", "alfa romeo"]):
            issues = [
                {"issue": "Fiabilité générale", "frequency": 75, "severity": "high"},
                {"issue": "Rouille carrosserie", "frequency": 50, "severity": "medium"},
                {"issue": "Pannes récurrentes", "frequency": 60, "severity": "high"}
            ]
        else:
            # Default issues for other brands
            issues = [
                {"issue": "Usure normale", "frequency": 25, "severity": "low"},
                {"issue": "Entretien périodique", "frequency": 20, "severity": "low"}
            ]
        
        return issues

    def _calculate_owner_satisfaction(self, sentiment_data: dict) -> float:
        """Calculate owner satisfaction score (0-100)"""
        
        testimonials = sentiment_data["owner_testimonials"]["sentiment_distribution"]
        total = sum(testimonials.values())
        
        if total == 0:
            return 50.0  # Neutral default
        
        # Weight the sentiments
        satisfaction = (
            testimonials["positive"] * 100 +
            testimonials["mixed"] * 60 +
            testimonials["negative"] * 20
        ) / total
        
        return round(satisfaction, 1)

    def _calculate_reliability_score(self, sentiment_data: dict, common_issues: list) -> float:
        """Calculate reliability score (0-100)"""
        
        base_score = 70  # Base reliability
        
        # Adjust based on common issues
        for issue in common_issues:
            severity_penalty = {"low": 2, "medium": 5, "high": 10}[issue["severity"]]
            frequency_multiplier = issue["frequency"] / 100
            base_score -= severity_penalty * frequency_multiplier
        
        # Adjust based on forum sentiment
        forum_sentiment = sentiment_data["forum_posts"]["average_sentiment"]
        base_score += forum_sentiment * 20  # -20 to +20 adjustment
        
        # Adjust based on owner satisfaction
        testimonials = sentiment_data["owner_testimonials"]["sentiment_distribution"]
        total_testimonials = sum(testimonials.values())
        if total_testimonials > 0:
            positive_ratio = testimonials["positive"] / total_testimonials
            base_score += (positive_ratio - 0.5) * 30  # Adjust by up to ±15 points
        
        return max(0, min(100, base_score))

    def _generate_analysis_summary(self, sentiment: float, reputation: dict, reliability: float) -> str:
        """Generate human-readable analysis summary"""
        
        # Sentiment description
        if sentiment > 0.3:
            sentiment_desc = "très positive"
        elif sentiment > 0.1:
            sentiment_desc = "positive"
        elif sentiment > -0.1:
            sentiment_desc = "neutre"
        elif sentiment > -0.3:
            sentiment_desc = "négative"
        else:
            sentiment_desc = "très négative"
        
        # Reliability description
        if reliability > 80:
            reliability_desc = "excellente"
        elif reliability > 65:
            reliability_desc = "bonne"
        elif reliability > 50:
            reliability_desc = "moyenne"
        else:
            reliability_desc = "faible"
        
        summary = f"L'opinion générale est {sentiment_desc} avec une réputation {reputation['overall_reputation']} "
        summary += f"et une fiabilité {reliability_desc} ({reliability:.0f}/100). "
        summary += f"Les propriétaires apprécient particulièrement: {', '.join(reputation['key_attributes'][:2])}."
        
        return summary

    def _generate_recommendations(self, sentiment: float, common_issues: list, reliability: float) -> list:
        """Generate recommendations based on sentiment analysis"""
        
        recommendations = []
        
        # Sentiment-based recommendations
        if sentiment > 0.2:
            recommendations.append("✅ Modèle généralement apprécié par les propriétaires")
        elif sentiment < -0.2:
            recommendations.append("⚠️ Modèle avec des avis mitigés - inspection recommandée")
        
        # Reliability-based recommendations
        if reliability > 75:
            recommendations.append("🔧 Fiabilité excellente - bon choix long terme")
        elif reliability < 50:
            recommendations.append("🔧 Fiabilité préoccupante - budget entretien à prévoir")
        
        # Issue-based recommendations
        high_severity_issues = [i for i in common_issues if i["severity"] == "high" and i["frequency"] > 50]
        if high_severity_issues:
            issue_names = [i["issue"] for i in high_severity_issues[:2]]
            recommendations.append(f"⚠️ Attention aux problèmes fréquents: {', '.join(issue_names)}")
        
        # Cost recommendations
        if any("coût" in issue["issue"].lower() for issue in common_issues):
            recommendations.append("💰 Coûts d'entretien potentiellement élevés")
        
        return recommendations

    def _format_sentiment_response(self, sentiment_record: SocialSentiment) -> dict:
        """Format existing sentiment record for response"""
        
        return {
            "make_model": sentiment_record.make_model,
            "overall_sentiment": sentiment_record.sentiment_score,
            "reputation_profile": sentiment_record.reputation_data,
            "common_issues": sentiment_record.common_issues,
            "owner_satisfaction": sentiment_record.owner_satisfaction,
            "reliability_score": sentiment_record.reliability_score,
            "analyzed_at": sentiment_record.analyzed_at.isoformat(),
            "cached": True
        }

    def get_sentiment_insights(self, make_model: str, db: Session) -> dict:
        """Get sentiment insights for a specific make/model"""
        
        sentiment = db.query(SocialSentiment).filter(
            SocialSentiment.make_model == make_model
        ).first()
        
        if not sentiment:
            return {"message": "No sentiment analysis available"}
        
        return self._format_sentiment_response(sentiment)

    def get_top_rated_models(self, db: Session, limit: int = 10) -> list:
        """Get top-rated models by sentiment"""
        
        top_models = db.query(SocialSentiment).filter(
            SocialSentiment.sentiment_score > 0.2,
            SocialSentiment.reliability_score > 70
        ).order_by(
            SocialSentiment.sentiment_score.desc(),
            SocialSentiment.owner_satisfaction.desc()
        ).limit(limit).all()
        
        return [
            {
                "make_model": model.make_model,
                "sentiment_score": model.sentiment_score,
                "reliability_score": model.reliability_score,
                "owner_satisfaction": model.owner_satisfaction,
                "overall_reputation": model.reputation_data.get("overall_reputation", "unknown") if model.reputation_data else "unknown"
            }
            for model in top_models
        ]

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    analyzer = SocialSentimentAnalyzer()
    db = SessionLocal()
    
    # Test with popular models
    test_models = ["Toyota Yaris", "BMW Série 3", "Renault Clio", "Peugeot 308"]
    
    for model in test_models:
        print(f"\nAnalyzing social sentiment for: {model}")
        sentiment = analyzer.analyze_social_sentiment(model, db)
        
        if "error" not in sentiment:
            print(f"Overall sentiment: {sentiment['overall_sentiment']:.2f}")
            print(f"Owner satisfaction: {sentiment['owner_satisfaction']}%")
            print(f"Reliability score: {sentiment['reliability_score']:.1f}")
            print(f"Reputation: {sentiment['reputation_profile']['overall_reputation']}")
            print(f"Summary: {sentiment['analysis_summary']}")
        else:
            print(f"Error: {sentiment['error']}")
    
    # Get top-rated models
    print(f"\nTop-rated models:")
    top_models = analyzer.get_top_rated_models(db, 5)
    for i, model in enumerate(top_models, 1):
        print(f"{i}. {model['make_model']} - Sentiment: {model['sentiment_score']:.2f}, Fiabilité: {model['reliability_score']:.0f}")
    
    db.close()