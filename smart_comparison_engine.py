import json
import re
from datetime import datetime, timedelta
from statistics import mean, median
from collections import Counter
import math
import anthropic
import os
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from enhanced_database import Car, CarComparison, GemScore, ParsedListing
import uuid

class SmartComparisonEngine:
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ) if os.getenv("ANTHROPIC_API_KEY") else None
        
        # Comparison weights for different factors
        self.comparison_weights = {
            "price": 0.25,
            "year": 0.20,
            "mileage": 0.20,
            "features": 0.15,
            "condition": 0.10,
            "seller_type": 0.05,
            "location": 0.05
        }
        
        # Similarity thresholds
        self.similarity_thresholds = {
            "very_similar": 0.85,
            "similar": 0.70,
            "somewhat_similar": 0.55,
            "different": 0.40
        }
        
        # Feature importance for different car categories
        self.category_weights = {
            "luxury": {"features": 0.3, "year": 0.25, "condition": 0.2, "price": 0.15, "mileage": 0.1},
            "economy": {"price": 0.35, "mileage": 0.25, "year": 0.2, "condition": 0.15, "features": 0.05},
            "sport": {"year": 0.3, "features": 0.25, "condition": 0.2, "price": 0.15, "mileage": 0.1},
            "utility": {"condition": 0.3, "mileage": 0.25, "price": 0.2, "year": 0.15, "features": 0.1}
        }

    def find_similar_cars(self, base_car: Car, db: Session, limit: int = 10) -> list:
        """Find cars similar to the base car"""
        
        # Get potential matches based on basic criteria
        candidates = self._get_candidate_cars(base_car, db, limit * 3)
        
        if not candidates:
            return []
        
        # Calculate similarity scores
        similar_cars = []
        
        for candidate in candidates:
            if candidate.id == base_car.id:
                continue
                
            similarity_score = self._calculate_similarity_score(base_car, candidate, db)
            
            if similarity_score > 0.4:  # Minimum similarity threshold
                similar_cars.append({
                    "car": candidate,
                    "similarity_score": similarity_score,
                    "similarity_factors": self._get_similarity_factors(base_car, candidate),
                    "value_comparison": self._compare_value_proposition(base_car, candidate, db)
                })
        
        # Sort by similarity and return top matches
        similar_cars.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_cars[:limit]

    def _get_candidate_cars(self, base_car: Car, db: Session, limit: int) -> list:
        """Get candidate cars for comparison"""
        
        # Start with cars in similar price range (±30%)
        price_range = 0.3
        if base_car.price:
            min_price = int(base_car.price * (1 - price_range))
            max_price = int(base_car.price * (1 + price_range))
        else:
            min_price = max_price = None
        
        # Build query
        query = db.query(Car).filter(
            Car.is_active == True,
            Car.id != base_car.id
        )
        
        # Price filter
        if min_price and max_price:
            query = query.filter(Car.price.between(min_price, max_price))
        
        # Year filter (±3 years)
        if base_car.year:
            query = query.filter(Car.year.between(base_car.year - 3, base_car.year + 3))
        
        # Fuel type filter
        if base_car.fuel_type:
            query = query.filter(Car.fuel_type == base_car.fuel_type)
        
        # Try to find cars with similar keywords in title
        base_keywords = self._extract_keywords(base_car.title)
        
        # Use text similarity for initial filtering
        if base_keywords:
            conditions = []
            for keyword in base_keywords[:3]:  # Use top 3 keywords
                conditions.append(Car.title.ilike(f"%{keyword}%"))
            
            if conditions:
                query = query.filter(or_(*conditions))
        
        return query.limit(limit).all()

    def _extract_keywords(self, title: str) -> list:
        """Extract important keywords from car title"""
        
        # Remove common stop words
        stop_words = {
            "de", "du", "le", "la", "les", "un", "une", "des", "et", "ou", "à", "au", "aux",
            "avec", "sans", "pour", "par", "sur", "dans", "très", "bon", "bonne", "excellent",
            "voiture", "auto", "véhicule", "occasion"
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{2,}\b', title.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Prioritize brand and model names
        priority_keywords = []
        normal_keywords = []
        
        brands = ["renault", "peugeot", "citroën", "bmw", "mercedes", "audi", "volkswagen", 
                 "toyota", "honda", "nissan", "ford", "opel", "fiat", "volvo", "alfa"]
        
        for keyword in keywords:
            if any(brand in keyword for brand in brands):
                priority_keywords.append(keyword)
            else:
                normal_keywords.append(keyword)
        
        return priority_keywords + normal_keywords

    def _calculate_similarity_score(self, car1: Car, car2: Car, db: Session) -> float:
        """Calculate overall similarity score between two cars"""
        
        scores = {}
        
        # Price similarity (0-1)
        if car1.price and car2.price:
            price_diff = abs(car1.price - car2.price)
            max_price = max(car1.price, car2.price)
            scores["price"] = max(0, 1 - (price_diff / max_price))
        else:
            scores["price"] = 0.5
        
        # Year similarity (0-1)
        if car1.year and car2.year:
            year_diff = abs(car1.year - car2.year)
            scores["year"] = max(0, 1 - (year_diff / 10))  # 10 years = 0 similarity
        else:
            scores["year"] = 0.5
        
        # Mileage similarity (0-1)
        if car1.mileage and car2.mileage:
            mileage_diff = abs(car1.mileage - car2.mileage)
            max_mileage = max(car1.mileage, car2.mileage)
            if max_mileage > 0:
                scores["mileage"] = max(0, 1 - (mileage_diff / max_mileage))
            else:
                scores["mileage"] = 1.0
        else:
            scores["mileage"] = 0.5
        
        # Text similarity (title + description)
        scores["features"] = self._calculate_text_similarity(car1, car2)
        
        # Condition similarity (based on parsed listings if available)
        scores["condition"] = self._calculate_condition_similarity(car1, car2, db)
        
        # Seller type similarity
        if car1.seller_type and car2.seller_type:
            scores["seller_type"] = 1.0 if car1.seller_type == car2.seller_type else 0.3
        else:
            scores["seller_type"] = 0.5
        
        # Location similarity (department)
        if car1.department and car2.department:
            scores["location"] = 1.0 if car1.department == car2.department else 0.2
        else:
            scores["location"] = 0.5
        
        # Calculate weighted average
        total_score = 0
        for factor, score in scores.items():
            weight = self.comparison_weights.get(factor, 0)
            total_score += score * weight
        
        return min(1.0, total_score)

    def _calculate_text_similarity(self, car1: Car, car2: Car) -> float:
        """Calculate text similarity between car titles and descriptions using cosine similarity"""
        
        try:
            text1 = f"{car1.title} {car1.description or ''}".lower()
            text2 = f"{car2.title} {car2.description or ''}".lower()
            
            # Handle empty texts
            if not text1.strip() or not text2.strip():
                return 0.3
            
            # Simple cosine similarity implementation
            similarity = self._cosine_similarity(text1, text2)
            return float(similarity)
            
        except Exception:
            # Fallback: simple keyword matching
            keywords1 = set(self._extract_keywords(car1.title))
            keywords2 = set(self._extract_keywords(car2.title))
            
            if not keywords1 or not keywords2:
                return 0.3
            
            intersection = len(keywords1.intersection(keywords2))
            union = len(keywords1.union(keywords2))
            
            return intersection / union if union > 0 else 0
    
    def _cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        
        # Tokenize and count words
        words1 = re.findall(r'\b[a-zA-ZÀ-ÿ]{2,}\b', text1)
        words2 = re.findall(r'\b[a-zA-ZÀ-ÿ]{2,}\b', text2)
        
        # Create word frequency vectors
        counter1 = Counter(words1)
        counter2 = Counter(words2)
        
        # Get all unique words
        all_words = set(counter1.keys()) | set(counter2.keys())
        
        if not all_words:
            return 0.0
        
        # Create vectors
        vector1 = [counter1.get(word, 0) for word in all_words]
        vector2 = [counter2.get(word, 0) for word in all_words]
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vector1))
        magnitude2 = math.sqrt(sum(b * b for b in vector2))
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        return dot_product / (magnitude1 * magnitude2)

    def _calculate_condition_similarity(self, car1: Car, car2: Car, db: Session) -> float:
        """Calculate condition similarity based on parsed listings"""
        
        parsed1 = db.query(ParsedListing).filter(ParsedListing.car_id == car1.id).first()
        parsed2 = db.query(ParsedListing).filter(ParsedListing.car_id == car2.id).first()
        
        if not parsed1 or not parsed2:
            return 0.5  # Neutral if no data
        
        # Compare seller credibility
        cred_diff = abs((parsed1.seller_credibility or 50) - (parsed2.seller_credibility or 50)) / 100
        credibility_sim = 1 - cred_diff
        
        # Compare number of red flags
        flags1 = len(parsed1.red_flags or [])
        flags2 = len(parsed2.red_flags or [])
        flag_sim = 1 - min(1, abs(flags1 - flags2) / 5)  # Max 5 flags difference
        
        # Compare positive signals
        signals1 = len(parsed1.positive_signals or [])
        signals2 = len(parsed2.positive_signals or [])
        signal_sim = 1 - min(1, abs(signals1 - signals2) / 5)
        
        return (credibility_sim + flag_sim + signal_sim) / 3

    def _get_similarity_factors(self, car1: Car, car2: Car) -> dict:
        """Get detailed similarity factors"""
        
        factors = {}
        
        # Price comparison
        if car1.price and car2.price:
            price_diff_pct = abs(car1.price - car2.price) / max(car1.price, car2.price) * 100
            factors["price_difference"] = f"{price_diff_pct:.1f}%"
        
        # Year comparison
        if car1.year and car2.year:
            factors["year_difference"] = abs(car1.year - car2.year)
        
        # Mileage comparison
        if car1.mileage and car2.mileage:
            mileage_diff = abs(car1.mileage - car2.mileage)
            factors["mileage_difference"] = f"{mileage_diff:,} km"
        
        # Common keywords
        keywords1 = set(self._extract_keywords(car1.title))
        keywords2 = set(self._extract_keywords(car2.title))
        common_keywords = keywords1.intersection(keywords2)
        factors["common_features"] = list(common_keywords)[:5]
        
        return factors

    def _compare_value_proposition(self, base_car: Car, candidate_car: Car, db: Session) -> dict:
        """Compare value proposition between cars"""
        
        comparison = {
            "price_advantage": "neutral",
            "feature_advantage": "neutral", 
            "condition_advantage": "neutral",
            "overall_recommendation": "neutral"
        }
        
        # Price comparison
        if base_car.price and candidate_car.price:
            price_diff = candidate_car.price - base_car.price
            price_diff_pct = (price_diff / base_car.price) * 100
            
            if price_diff_pct < -10:
                comparison["price_advantage"] = "candidate_better"
            elif price_diff_pct > 10:
                comparison["price_advantage"] = "base_better"
        
        # Get gem scores if available
        base_gem = db.query(GemScore).filter(GemScore.car_id == base_car.id).first()
        candidate_gem = db.query(GemScore).filter(GemScore.car_id == candidate_car.id).first()
        
        if base_gem and candidate_gem:
            gem_diff = candidate_gem.gem_score - base_gem.gem_score
            if gem_diff > 10:
                comparison["overall_recommendation"] = "candidate_better"
            elif gem_diff < -10:
                comparison["overall_recommendation"] = "base_better"
        
        # Feature comparison (based on descriptions)
        base_features = len(self._extract_keywords(f"{base_car.title} {base_car.description or ''}"))
        candidate_features = len(self._extract_keywords(f"{candidate_car.title} {candidate_car.description or ''}"))
        
        if candidate_features > base_features * 1.2:
            comparison["feature_advantage"] = "candidate_better"
        elif base_features > candidate_features * 1.2:
            comparison["feature_advantage"] = "base_better"
        
        return comparison

    def generate_comparison_report(self, base_car: Car, db: Session) -> dict:
        """Generate comprehensive comparison report"""
        
        # Find similar cars
        similar_cars = self.find_similar_cars(base_car, db, 5)
        
        if not similar_cars:
            return {"error": "No similar cars found"}
        
        # Create comparison matrix
        comparison_matrix = self._create_comparison_matrix(base_car, similar_cars, db)
        
        # Rank by value
        value_ranking = self._rank_by_value(base_car, similar_cars, db)
        
        # Generate AI insights if available
        ai_insights = self._generate_ai_comparison_insights(base_car, similar_cars)
        
        # Generate recommendation
        recommendation = self._generate_comparison_recommendation(base_car, similar_cars, value_ranking)
        
        return {
            "base_car": {
                "id": base_car.id,
                "title": base_car.title,
                "price": base_car.price,
                "year": base_car.year,
                "mileage": base_car.mileage
            },
            "similar_cars": [
                {
                    "id": item["car"].id,
                    "title": item["car"].title,
                    "price": item["car"].price,
                    "year": item["car"].year,
                    "mileage": item["car"].mileage,
                    "similarity_score": item["similarity_score"],
                    "similarity_factors": item["similarity_factors"],
                    "value_comparison": item["value_comparison"]
                }
                for item in similar_cars
            ],
            "comparison_matrix": comparison_matrix,
            "value_ranking": value_ranking,
            "ai_insights": ai_insights,
            "recommendation": recommendation,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _create_comparison_matrix(self, base_car: Car, similar_cars: list, db: Session) -> dict:
        """Create detailed comparison matrix"""
        
        all_cars = [base_car] + [item["car"] for item in similar_cars]
        
        matrix = {
            "criteria": ["Prix", "Année", "Kilométrage", "État", "Vendeur", "Localisation"],
            "cars": []
        }
        
        for i, car in enumerate(all_cars):
            car_data = {
                "id": car.id,
                "title": car.title,
                "is_base": i == 0,
                "scores": {
                    "Prix": self._normalize_price_score(car.price, all_cars),
                    "Année": self._normalize_year_score(car.year, all_cars),
                    "Kilométrage": self._normalize_mileage_score(car.mileage, all_cars),
                    "État": self._get_condition_score(car, db),
                    "Vendeur": 1.0 if car.seller_type == "particulier" else 0.7,
                    "Localisation": 0.8  # Neutral score
                }
            }
            matrix["cars"].append(car_data)
        
        return matrix

    def _normalize_price_score(self, price: int, all_cars: list) -> float:
        """Normalize price score (lower is better)"""
        if not price:
            return 0.5
        
        prices = [car.price for car in all_cars if car.price]
        if not prices:
            return 0.5
        
        min_price = min(prices)
        max_price = max(prices)
        
        if max_price == min_price:
            return 1.0
        
        # Invert score (lower price = higher score)
        return 1.0 - ((price - min_price) / (max_price - min_price))

    def _normalize_year_score(self, year: int, all_cars: list) -> float:
        """Normalize year score (newer is better)"""
        if not year:
            return 0.5
        
        years = [car.year for car in all_cars if car.year]
        if not years:
            return 0.5
        
        min_year = min(years)
        max_year = max(years)
        
        if max_year == min_year:
            return 1.0
        
        return (year - min_year) / (max_year - min_year)

    def _normalize_mileage_score(self, mileage: int, all_cars: list) -> float:
        """Normalize mileage score (lower is better)"""
        if not mileage:
            return 0.5
        
        mileages = [car.mileage for car in all_cars if car.mileage]
        if not mileages:
            return 0.5
        
        min_mileage = min(mileages)
        max_mileage = max(mileages)
        
        if max_mileage == min_mileage:
            return 1.0
        
        # Invert score (lower mileage = higher score)
        return 1.0 - ((mileage - min_mileage) / (max_mileage - min_mileage))

    def _get_condition_score(self, car: Car, db: Session) -> float:
        """Get condition score from parsed listing"""
        parsed = db.query(ParsedListing).filter(ParsedListing.car_id == car.id).first()
        
        if not parsed:
            return 0.6  # Neutral default
        
        # Base score from credibility
        base_score = (parsed.seller_credibility or 50) / 100
        
        # Adjust for red flags and positive signals
        red_flag_penalty = len(parsed.red_flags or []) * 0.05
        positive_bonus = len(parsed.positive_signals or []) * 0.03
        
        return max(0, min(1, base_score - red_flag_penalty + positive_bonus))

    def _rank_by_value(self, base_car: Car, similar_cars: list, db: Session) -> list:
        """Rank cars by overall value proposition"""
        
        all_cars_data = []
        
        # Include base car
        base_gem = db.query(GemScore).filter(GemScore.car_id == base_car.id).first()
        all_cars_data.append({
            "car": base_car,
            "gem_score": base_gem.gem_score if base_gem else 50,
            "is_base": True,
            "similarity_score": 1.0
        })
        
        # Include similar cars
        for item in similar_cars:
            car = item["car"]
            gem = db.query(GemScore).filter(GemScore.car_id == car.id).first()
            all_cars_data.append({
                "car": car,
                "gem_score": gem.gem_score if gem else 50,
                "is_base": False,
                "similarity_score": item["similarity_score"]
            })
        
        # Calculate value scores
        for item in all_cars_data:
            car = item["car"]
            value_score = 0
            
            # Price value (lower price = higher value)
            if car.price:
                price_score = max(0, 100 - (car.price / 1000))  # Simplified price scoring
                value_score += price_score * 0.3
            
            # Gem score
            value_score += item["gem_score"] * 0.4
            
            # Similarity bonus (for non-base cars)
            if not item["is_base"]:
                value_score += item["similarity_score"] * 30  # 0-30 points
            
            # Age penalty
            if car.year:
                age = datetime.now().year - car.year
                age_penalty = min(30, age * 2)  # Max 30 point penalty
                value_score = max(0, value_score - age_penalty)
            
            item["value_score"] = value_score
        
        # Sort by value score
        ranked = sorted(all_cars_data, key=lambda x: x["value_score"], reverse=True)
        
        return [
            {
                "rank": i + 1,
                "car_id": item["car"].id,
                "title": item["car"].title,
                "price": item["car"].price,
                "value_score": round(item["value_score"], 1),
                "gem_score": item["gem_score"],
                "is_base": item["is_base"],
                "recommendation": self._get_ranking_recommendation(i + 1, item["is_base"])
            }
            for i, item in enumerate(ranked)
        ]

    def _get_ranking_recommendation(self, rank: int, is_base: bool) -> str:
        """Get recommendation based on ranking"""
        if is_base:
            if rank == 1:
                return "Votre choix est le meilleur rapport qualité-prix"
            elif rank <= 3:
                return "Bon choix, mais il existe de meilleures alternatives"
            else:
                return "Considérez les alternatives mieux classées"
        else:
            if rank == 1:
                return "Meilleure alternative - fortement recommandé"
            elif rank <= 3:
                return "Bonne alternative à considérer"
            else:
                return "Alternative correcte mais pas optimale"

    def _generate_ai_comparison_insights(self, base_car: Car, similar_cars: list) -> dict:
        """Generate AI insights for comparison"""
        
        if not self.anthropic_client:
            return {"error": "AI analysis not available"}
        
        try:
            # Prepare comparison data
            comparison_data = f"""
            Voiture de base: {base_car.title} - {base_car.price}€ - {base_car.year} - {base_car.mileage} km
            
            Alternatives similaires:
            """
            
            for i, item in enumerate(similar_cars[:3], 1):
                car = item["car"]
                comparison_data += f"{i}. {car.title} - {car.price}€ - {car.year} - {car.mileage} km (similarité: {item['similarity_score']:.1%})\n"
            
            prompt = f"""
            Analysez cette comparaison de voitures françaises et fournissez des insights:
            
            {comparison_data}
            
            Fournissez une analyse en JSON avec:
            1. market_position: position de la voiture de base sur le marché
            2. best_alternatives: 2 meilleures alternatives avec raisons
            3. negotiation_opportunities: opportunités de négociation détectées
            4. hidden_advantages: avantages cachés de chaque option
            5. risk_assessment: évaluation des risques pour chaque choix
            6. decision_framework: cadre de décision pour l'acheteur
            
            Répondez uniquement en JSON français.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return json.loads(message.content[0].text)
            
        except Exception as e:
            return {"error": f"AI insights failed: {str(e)}"}

    def _generate_comparison_recommendation(self, base_car: Car, similar_cars: list, value_ranking: list) -> dict:
        """Generate overall comparison recommendation"""
        
        base_rank = next((item["rank"] for item in value_ranking if item["is_base"]), None)
        
        recommendation = {
            "overall_advice": "neutral",
            "confidence": "medium",
            "key_points": [],
            "next_steps": []
        }
        
        if base_rank == 1:
            recommendation["overall_advice"] = "keep_choice"
            recommendation["key_points"].append("Votre choix actuel offre le meilleur rapport qualité-prix")
            recommendation["next_steps"].append("Procéder à l'inspection et négociation")
        elif base_rank <= 3:
            recommendation["overall_advice"] = "consider_alternatives"
            better_alternatives = [item for item in value_ranking if not item["is_base"] and item["rank"] < base_rank]
            if better_alternatives:
                best_alt = better_alternatives[0]
                recommendation["key_points"].append(f"Considérez {best_alt['title']} (rang #{best_alt['rank']})")
            recommendation["next_steps"].append("Comparer en détail avec les alternatives mieux classées")
        else:
            recommendation["overall_advice"] = "reconsider"
            recommendation["key_points"].append("Plusieurs alternatives semblent offrir un meilleur rapport qualité-prix")
            recommendation["next_steps"].append("Étudier sérieusement les options mieux classées")
        
        # Confidence based on number of similar cars found
        if len(similar_cars) >= 3:
            recommendation["confidence"] = "high"
        elif len(similar_cars) >= 2:
            recommendation["confidence"] = "medium"
        else:
            recommendation["confidence"] = "low"
        
        return recommendation

    def save_comparison(self, base_car: Car, comparison_data: dict, db: Session) -> str:
        """Save comparison report to database"""
        
        similar_car_ids = [car["id"] for car in comparison_data["similar_cars"]]
        
        comparison = CarComparison(
            id=str(uuid.uuid4()),
            base_car_id=base_car.id,
            similar_cars=similar_car_ids,
            comparison_matrix=comparison_data["comparison_matrix"],
            value_ranking=comparison_data["value_ranking"],
            recommendation_reason=comparison_data["recommendation"]["overall_advice"]
        )
        
        db.add(comparison)
        db.commit()
        
        return comparison.id

    def get_comparison_insights(self, car_id: str, db: Session) -> dict:
        """Get saved comparison insights for a car"""
        
        comparison = db.query(CarComparison).filter(
            CarComparison.base_car_id == car_id
        ).first()
        
        if not comparison:
            return {"message": "No comparison available"}
        
        return {
            "base_car_id": comparison.base_car_id,
            "similar_cars": comparison.similar_cars,
            "comparison_matrix": comparison.comparison_matrix,
            "value_ranking": comparison.value_ranking,
            "recommendation": comparison.recommendation_reason,
            "generated_at": comparison.generated_at.isoformat()
        }

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    engine = SmartComparisonEngine()
    db = SessionLocal()
    
    # Test with first car
    car = db.query(Car).filter(Car.price.isnot(None)).first()
    if car:
        print(f"Generating comparison for: {car.title}")
        comparison = engine.generate_comparison_report(car, db)
        
        if "error" not in comparison:
            print(f"Found {len(comparison['similar_cars'])} similar cars")
            print(f"Value ranking position: {next((item['rank'] for item in comparison['value_ranking'] if item['is_base']), 'N/A')}")
            print(f"Recommendation: {comparison['recommendation']['overall_advice']}")
            
            # Save comparison
            comparison_id = engine.save_comparison(car, comparison, db)
            print(f"Comparison saved with ID: {comparison_id}")
        else:
            print(f"Error: {comparison['error']}")
    else:
        print("No cars with prices found")
    
    db.close()