import json
import re
from datetime import datetime, timedelta
from statistics import median, mean, stdev
import anthropic
import os
from sqlalchemy.orm import Session
from sqlalchemy import func
from enhanced_database import Car, MarketPulse
import uuid

class MarketPulsePredictor:
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ) if os.getenv("ANTHROPIC_API_KEY") else None
        
        # Seasonal factors for different car types
        self.seasonal_multipliers = {
            "cabriolet": {
                1: 0.85, 2: 0.88, 3: 0.95, 4: 1.10, 5: 1.20, 6: 1.25,
                7: 1.30, 8: 1.25, 9: 1.15, 10: 1.05, 11: 0.90, 12: 0.85
            },
            "4x4": {
                1: 1.15, 2: 1.10, 3: 1.05, 4: 0.95, 5: 0.90, 6: 0.85,
                7: 0.85, 8: 0.85, 9: 0.95, 10: 1.10, 11: 1.20, 12: 1.25
            },
            "berline": {
                1: 1.02, 2: 1.00, 3: 1.05, 4: 1.08, 5: 1.10, 6: 1.05,
                7: 1.00, 8: 0.98, 9: 1.05, 10: 1.08, 11: 1.03, 12: 1.00
            },
            "utilitaire": {
                1: 1.05, 2: 1.08, 3: 1.15, 4: 1.20, 5: 1.15, 6: 1.10,
                7: 1.05, 8: 1.00, 9: 1.10, 10: 1.15, 11: 1.08, 12: 1.05
            }
        }
        
        # Market trend indicators
        self.trend_keywords = {
            "rising": ["recherché", "rare", "collection", "apprécié", "valorise", "monte"],
            "falling": ["dépréciation", "baisse", "difficile à vendre", "surplus", "saturé"],
            "stable": ["stable", "constant", "régulier", "équilibré"]
        }
        
        # Economic factors affecting car market
        self.economic_indicators = {
            "fuel_prices": {"high": 0.9, "normal": 1.0, "low": 1.1},
            "interest_rates": {"high": 0.85, "normal": 1.0, "low": 1.15},
            "inflation": {"high": 0.9, "normal": 1.0, "low": 1.05}
        }

    def analyze_market_pulse(self, make_model: str, db: Session) -> dict:
        """Analyze current market pulse for a specific make/model"""
        
        # Get historical data
        historical_data = self._get_historical_data(make_model, db)
        
        if not historical_data or len(historical_data) < 5:
            return {"error": "Insufficient historical data"}
        
        # Analyze current trends
        trend_analysis = self._analyze_current_trends(historical_data)
        
        # Calculate price predictions
        price_predictions = self._predict_future_prices(historical_data, make_model)
        
        # Assess seasonal factors
        seasonal_factors = self._calculate_seasonal_factors(make_model)
        
        # Calculate market saturation
        market_saturation = self._calculate_market_saturation(make_model, db)
        
        # Calculate demand score
        demand_score = self._calculate_demand_score(historical_data, market_saturation, seasonal_factors)
        
        # Generate insights with AI
        ai_insights = self._generate_ai_insights(make_model, trend_analysis, price_predictions)
        
        market_pulse = {
            "make_model": make_model,
            "current_trend": trend_analysis["trend_direction"],
            "trend_strength": trend_analysis["trend_strength"],
            "price_prediction": price_predictions,
            "seasonal_factors": seasonal_factors,
            "market_saturation": market_saturation,
            "demand_score": demand_score,
            "market_velocity": trend_analysis["market_velocity"],
            "volatility_index": trend_analysis["volatility"],
            "ai_insights": ai_insights,
            "recommendation": self._generate_market_recommendation(trend_analysis, demand_score, market_saturation),
            "confidence_level": self._calculate_prediction_confidence(historical_data, trend_analysis)
        }
        
        return market_pulse

    def _get_historical_data(self, make_model: str, db: Session, days: int = 90) -> list:
        """Get historical pricing data for make/model"""
        
        # Search for cars matching make/model
        search_terms = make_model.lower().split()
        
        query = db.query(Car).filter(
            Car.price.isnot(None),
            Car.first_seen >= datetime.utcnow() - timedelta(days=days)
        )
        
        # Add make/model filters
        for term in search_terms:
            query = query.filter(Car.title.ilike(f"%{term}%"))
        
        cars = query.order_by(Car.first_seen.asc()).all()
        
        # Group by time periods
        historical_data = []
        for car in cars:
            historical_data.append({
                "date": car.first_seen,
                "price": car.price,
                "mileage": car.mileage,
                "year": car.year,
                "seller_type": car.seller_type,
                "is_active": car.is_active,
                "department": car.department
            })
        
        return historical_data

    def _analyze_current_trends(self, historical_data: list) -> dict:
        """Analyze current market trends"""
        
        # Sort by date
        sorted_data = sorted(historical_data, key=lambda x: x["date"])
        
        # Calculate price trend over time
        prices = [item["price"] for item in sorted_data]
        dates = [item["date"] for item in sorted_data]
        
        if len(prices) < 5:
            return {"trend_direction": "insufficient_data", "trend_strength": 0}
        
        # Calculate trend using linear regression (simplified)
        recent_prices = prices[-30:] if len(prices) > 30 else prices
        older_prices = prices[:len(prices)//2] if len(prices) > 10 else prices[:len(prices)//2]
        
        if not older_prices or not recent_prices:
            return {"trend_direction": "stable", "trend_strength": 0}
        
        recent_avg = mean(recent_prices)
        older_avg = mean(older_prices) if older_prices else recent_avg
        
        price_change_pct = (recent_avg - older_avg) / older_avg * 100 if older_avg > 0 else 0
        
        # Determine trend direction
        if price_change_pct > 5:
            trend_direction = "rising"
            trend_strength = min(100, abs(price_change_pct) * 2)
        elif price_change_pct < -5:
            trend_direction = "falling" 
            trend_strength = min(100, abs(price_change_pct) * 2)
        else:
            trend_direction = "stable"
            trend_strength = max(0, 50 - abs(price_change_pct) * 10)
        
        # Calculate market velocity (how quickly cars sell)
        active_count = sum(1 for item in sorted_data if item["is_active"])
        total_count = len(sorted_data)
        market_velocity = (total_count - active_count) / total_count * 100 if total_count > 0 else 0
        
        # Calculate volatility
        volatility = stdev(prices) / mean(prices) * 100 if len(prices) > 1 and mean(prices) > 0 else 0
        
        return {
            "trend_direction": trend_direction,
            "trend_strength": trend_strength,
            "price_change_percentage": price_change_pct,
            "market_velocity": market_velocity,
            "volatility": volatility,
            "sample_size": len(historical_data)
        }

    def _predict_future_prices(self, historical_data: list, make_model: str) -> dict:
        """Predict future price movements"""
        
        current_prices = [item["price"] for item in historical_data if item["is_active"]]
        all_prices = [item["price"] for item in historical_data]
        
        if not current_prices:
            current_avg = mean(all_prices) if all_prices else 0
        else:
            current_avg = mean(current_prices)
        
        # Calculate depreciation rate
        if len(historical_data) > 10:
            old_data = [item for item in historical_data if item["date"] < datetime.utcnow() - timedelta(days=60)]
            new_data = [item for item in historical_data if item["date"] >= datetime.utcnow() - timedelta(days=60)]
            
            if old_data and new_data:
                old_avg = mean([item["price"] for item in old_data])
                new_avg = mean([item["price"] for item in new_data])
                monthly_change_rate = (new_avg - old_avg) / old_avg * 100 / 2 if old_avg > 0 else 0  # Per month
            else:
                monthly_change_rate = -1.5  # Default depreciation
        else:
            monthly_change_rate = -1.5  # Default depreciation
        
        # Apply seasonal factors
        current_month = datetime.now().month
        car_type = self._classify_car_type(make_model)
        seasonal_multiplier = self.seasonal_multipliers.get(car_type, self.seasonal_multipliers["berline"])
        
        predictions = {}
        
        # 3-month prediction
        future_month_3 = (current_month + 2) % 12 + 1
        seasonal_adj_3 = seasonal_multiplier.get(future_month_3, 1.0)
        price_3m = current_avg * (1 + monthly_change_rate/100 * 3) * seasonal_adj_3
        predictions["3_month"] = {
            "price": int(price_3m),
            "change_percentage": ((price_3m - current_avg) / current_avg * 100) if current_avg > 0 else 0,
            "seasonal_factor": seasonal_adj_3
        }
        
        # 6-month prediction
        future_month_6 = (current_month + 5) % 12 + 1
        seasonal_adj_6 = seasonal_multiplier.get(future_month_6, 1.0)
        price_6m = current_avg * (1 + monthly_change_rate/100 * 6) * seasonal_adj_6
        predictions["6_month"] = {
            "price": int(price_6m),
            "change_percentage": ((price_6m - current_avg) / current_avg * 100) if current_avg > 0 else 0,
            "seasonal_factor": seasonal_adj_6
        }
        
        # 12-month prediction
        price_12m = current_avg * (1 + monthly_change_rate/100 * 12)
        predictions["12_month"] = {
            "price": int(price_12m),
            "change_percentage": ((price_12m - current_avg) / current_avg * 100) if current_avg > 0 else 0,
            "seasonal_factor": 1.0  # Full year cycle
        }
        
        predictions["current_average"] = int(current_avg)
        predictions["monthly_change_rate"] = monthly_change_rate
        
        return predictions

    def _classify_car_type(self, make_model: str) -> str:
        """Classify car type for seasonal analysis"""
        make_model_lower = make_model.lower()
        
        if any(word in make_model_lower for word in ["cabriolet", "convertible", "cabrio", "roadster"]):
            return "cabriolet"
        elif any(word in make_model_lower for word in ["4x4", "suv", "crossover", "x-drive", "quattro", "4matic"]):
            return "4x4"
        elif any(word in make_model_lower for word in ["utilitaire", "van", "fourgon", "pickup"]):
            return "utilitaire"
        else:
            return "berline"

    def _calculate_seasonal_factors(self, make_model: str) -> dict:
        """Calculate seasonal factors affecting the model"""
        car_type = self._classify_car_type(make_model)
        current_month = datetime.now().month
        
        multipliers = self.seasonal_multipliers.get(car_type, self.seasonal_multipliers["berline"])
        current_factor = multipliers.get(current_month, 1.0)
        
        # Find best and worst months
        best_month = max(multipliers, key=multipliers.get)
        worst_month = min(multipliers, key=multipliers.get)
        
        return {
            "car_type": car_type,
            "current_month_factor": current_factor,
            "best_selling_month": best_month,
            "best_month_boost": multipliers[best_month],
            "worst_selling_month": worst_month,
            "worst_month_penalty": multipliers[worst_month],
            "seasonal_volatility": max(multipliers.values()) - min(multipliers.values()),
            "monthly_factors": multipliers
        }

    def _calculate_market_saturation(self, make_model: str, db: Session) -> float:
        """Calculate market saturation level (0-100)"""
        
        # Get current active listings for this model
        search_terms = make_model.lower().split()
        query = db.query(Car).filter(Car.is_active == True)
        
        for term in search_terms:
            query = query.filter(Car.title.ilike(f"%{term}%"))
        
        model_count = query.count()
        
        # Get total active car listings
        total_active = db.query(Car).filter(Car.is_active == True).count()
        
        if total_active == 0:
            return 50  # Neutral
        
        # Calculate saturation percentage
        saturation_pct = (model_count / total_active) * 100
        
        # Normalize to congestion level (0-100)
        if saturation_pct > 10:
            saturation_level = 90  # Very saturated
        elif saturation_pct > 5:
            saturation_level = 70  # Saturated
        elif saturation_pct > 2:
            saturation_level = 50  # Normal
        elif saturation_pct > 1:
            saturation_level = 30  # Low saturation
        else:
            saturation_level = 10  # Very low saturation
        
        return saturation_level

    def _calculate_demand_score(self, historical_data: list, market_saturation: float, seasonal_factors: dict) -> int:
        """Calculate overall demand score (0-100)"""
        
        base_score = 50
        
        # Market velocity factor
        active_count = sum(1 for item in historical_data if item["is_active"])
        total_count = len(historical_data)
        
        if total_count > 0:
            sell_through_rate = (total_count - active_count) / total_count
            velocity_bonus = sell_through_rate * 30  # Up to 30 points
            base_score += velocity_bonus
        
        # Saturation penalty
        saturation_penalty = (market_saturation - 50) * 0.5  # Penalty for high saturation
        base_score -= saturation_penalty
        
        # Seasonal bonus
        seasonal_bonus = (seasonal_factors["current_month_factor"] - 1.0) * 20
        base_score += seasonal_bonus
        
        # Price stability bonus
        prices = [item["price"] for item in historical_data]
        if len(prices) > 1:
            price_stability = 100 - (stdev(prices) / mean(prices) * 100)
            stability_bonus = max(0, price_stability - 80) * 0.5  # Bonus for low volatility
            base_score += stability_bonus
        
        return int(max(0, min(100, base_score)))

    def _generate_ai_insights(self, make_model: str, trend_analysis: dict, price_predictions: dict) -> dict:
        """Generate AI insights about market conditions"""
        
        if not self.anthropic_client:
            return {"error": "AI analysis not available"}
        
        try:
            prompt = f"""
            Analysez les conditions du marché automobile français pour {make_model}:
            
            Tendance actuelle: {trend_analysis["trend_direction"]} ({trend_analysis["trend_strength"]}% de force)
            Changement de prix: {trend_analysis.get("price_change_percentage", 0):.1f}%
            Vélocité marché: {trend_analysis.get("market_velocity", 0):.1f}%
            Volatilité: {trend_analysis.get("volatility", 0):.1f}%
            
            Prédictions prix:
            - 3 mois: {price_predictions.get("3_month", {}).get("price", 0)}€ ({price_predictions.get("3_month", {}).get("change_percentage", 0):.1f}%)
            - 6 mois: {price_predictions.get("6_month", {}).get("price", 0)}€ ({price_predictions.get("6_month", {}).get("change_percentage", 0):.1f}%)
            - 12 mois: {price_predictions.get("12_month", {}).get("price", 0)}€ ({price_predictions.get("12_month", {}).get("change_percentage", 0):.1f}%)
            
            Fournissez une analyse en JSON avec:
            1. market_health: santé du marché (excellent/bon/moyen/faible)
            2. key_factors: 3 facteurs clés influençant le marché
            3. risks: risques potentiels
            4. opportunities: opportunités d'achat/vente
            5. timing_advice: conseils de timing
            6. market_outlook: perspectives (6 mois)
            
            Répondez uniquement en JSON français.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return json.loads(message.content[0].text)
            
        except Exception as e:
            return {"error": f"AI analysis failed: {str(e)}"}

    def _generate_market_recommendation(self, trend_analysis: dict, demand_score: int, market_saturation: float) -> dict:
        """Generate market recommendations"""
        
        recommendations = {
            "buy_timing": "neutral",
            "sell_timing": "neutral", 
            "investment_advice": "hold",
            "confidence": "medium"
        }
        
        # Buy timing logic
        if trend_analysis["trend_direction"] == "falling" and demand_score > 60:
            recommendations["buy_timing"] = "excellent"
            recommendations["investment_advice"] = "buy"
        elif trend_analysis["trend_direction"] == "stable" and market_saturation < 40:
            recommendations["buy_timing"] = "good"
        elif trend_analysis["trend_direction"] == "rising" and trend_analysis["trend_strength"] > 70:
            recommendations["buy_timing"] = "poor"
        
        # Sell timing logic
        if trend_analysis["trend_direction"] == "rising" and demand_score > 70:
            recommendations["sell_timing"] = "excellent"
            recommendations["investment_advice"] = "sell"
        elif trend_analysis["trend_direction"] == "stable" and market_saturation > 60:
            recommendations["sell_timing"] = "good"
        elif trend_analysis["trend_direction"] == "falling":
            recommendations["sell_timing"] = "poor"
        
        # Confidence based on data quality
        sample_size = trend_analysis.get("sample_size", 0)
        if sample_size > 50:
            recommendations["confidence"] = "high"
        elif sample_size > 20:
            recommendations["confidence"] = "medium"
        else:
            recommendations["confidence"] = "low"
        
        return recommendations

    def _calculate_prediction_confidence(self, historical_data: list, trend_analysis: dict) -> float:
        """Calculate confidence in predictions (0-1)"""
        
        confidence = 0.5  # Base confidence
        
        # Data quantity factor
        data_count = len(historical_data)
        if data_count > 100:
            confidence += 0.2
        elif data_count > 50:
            confidence += 0.15
        elif data_count > 20:
            confidence += 0.1
        elif data_count < 10:
            confidence -= 0.2
        
        # Trend strength factor
        trend_strength = trend_analysis.get("trend_strength", 0)
        if trend_strength > 70:
            confidence += 0.15
        elif trend_strength < 30:
            confidence -= 0.1
        
        # Volatility factor (lower volatility = higher confidence)
        volatility = trend_analysis.get("volatility", 50)
        if volatility < 20:
            confidence += 0.1
        elif volatility > 50:
            confidence -= 0.15
        
        # Market velocity factor
        velocity = trend_analysis.get("market_velocity", 0)
        if 20 <= velocity <= 80:  # Healthy market velocity
            confidence += 0.05
        
        return max(0.1, min(1.0, confidence))

    def save_market_pulse(self, make_model: str, pulse_data: dict, db: Session) -> str:
        """Save market pulse analysis to database"""
        
        # Check if recent analysis exists
        existing = db.query(MarketPulse).filter(
            MarketPulse.make_model == make_model,
            MarketPulse.created_at > datetime.utcnow() - timedelta(hours=6)
        ).first()
        
        if existing:
            # Update existing record
            existing.current_trend = pulse_data["current_trend"]
            existing.price_prediction = pulse_data["price_prediction"]
            existing.seasonal_factors = pulse_data["seasonal_factors"]
            existing.market_saturation = pulse_data["market_saturation"]
            existing.demand_score = pulse_data["demand_score"]
            existing.valid_until = datetime.utcnow() + timedelta(hours=24)
            db.commit()
            return existing.id
        else:
            # Create new record
            market_pulse = MarketPulse(
                id=str(uuid.uuid4()),
                make_model=make_model,
                current_trend=pulse_data["current_trend"],
                price_prediction=pulse_data["price_prediction"],
                seasonal_factors=pulse_data["seasonal_factors"],
                market_saturation=pulse_data["market_saturation"],
                demand_score=pulse_data["demand_score"],
                valid_until=datetime.utcnow() + timedelta(hours=24)
            )
            
            db.add(market_pulse)
            db.commit()
            return market_pulse.id

    def get_market_insights(self, make_model: str, db: Session) -> dict:
        """Get saved market insights for a make/model"""
        
        pulse = db.query(MarketPulse).filter(
            MarketPulse.make_model == make_model,
            MarketPulse.valid_until > datetime.utcnow()
        ).first()
        
        if not pulse:
            return {"message": "No recent market analysis available"}
        
        return {
            "make_model": pulse.make_model,
            "current_trend": pulse.current_trend,
            "price_prediction": pulse.price_prediction,
            "seasonal_factors": pulse.seasonal_factors,
            "market_saturation": pulse.market_saturation,
            "demand_score": pulse.demand_score,
            "analyzed_at": pulse.created_at.isoformat(),
            "valid_until": pulse.valid_until.isoformat()
        }

    def get_trending_models(self, db: Session, limit: int = 20) -> list:
        """Get currently trending car models"""
        
        # Get recent market pulse data
        pulses = db.query(MarketPulse).filter(
            MarketPulse.valid_until > datetime.utcnow(),
            MarketPulse.current_trend == "rising"
        ).order_by(MarketPulse.demand_score.desc()).limit(limit).all()
        
        trending = []
        for pulse in pulses:
            trending.append({
                "make_model": pulse.make_model,
                "trend": pulse.current_trend,
                "demand_score": pulse.demand_score,
                "market_saturation": pulse.market_saturation,
                "price_change_3m": pulse.price_prediction.get("3_month", {}).get("change_percentage", 0) if pulse.price_prediction else 0
            })
        
        return trending

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    predictor = MarketPulsePredictor()
    db = SessionLocal()
    
    # Test with popular French models
    test_models = ["Renault Clio", "Peugeot 208", "Citroën C3"]
    
    for model in test_models:
        print(f"\nAnalyzing market pulse for: {model}")
        pulse = predictor.analyze_market_pulse(model, db)
        
        if "error" not in pulse:
            print(f"Current trend: {pulse['current_trend']}")
            print(f"Demand score: {pulse['demand_score']}")
            print(f"Market saturation: {pulse['market_saturation']:.1f}%")
            print(f"3-month prediction: {pulse['price_prediction'].get('3_month', {}).get('price', 'N/A')}€")
            
            # Save analysis
            pulse_id = predictor.save_market_pulse(model, pulse, db)
            print(f"Analysis saved with ID: {pulse_id}")
        else:
            print(f"Error: {pulse['error']}")
    
    db.close()