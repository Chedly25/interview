import json
import re
from datetime import datetime, timedelta
from statistics import mean, median
import anthropic
import os
from sqlalchemy.orm import Session
from enhanced_database import Car, MaintenancePrediction
import uuid

class MaintenanceCostProphet:
    def __init__(self):
        try:
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            ) if os.getenv("ANTHROPIC_API_KEY") else None
        except Exception as e:
            print(f"Warning: Anthropic client initialization failed in maintenance_cost_prophet: {e}")
            self.anthropic_client = None
        
        # Maintenance cost data by brand (average annual costs in euros)
        self.brand_maintenance_costs = {
            "renault": {"base": 800, "multiplier": 1.0, "reliability": "B"},
            "peugeot": {"base": 850, "multiplier": 1.1, "reliability": "B"},
            "citroën": {"base": 900, "multiplier": 1.2, "reliability": "B-"},
            "bmw": {"base": 1400, "multiplier": 1.8, "reliability": "C+"},
            "mercedes": {"base": 1600, "multiplier": 2.0, "reliability": "C+"},
            "audi": {"base": 1350, "multiplier": 1.7, "reliability": "C+"},
            "volkswagen": {"base": 1100, "multiplier": 1.4, "reliability": "B"},
            "toyota": {"base": 700, "multiplier": 0.8, "reliability": "A"},
            "honda": {"base": 750, "multiplier": 0.9, "reliability": "A-"},
            "nissan": {"base": 900, "multiplier": 1.1, "reliability": "B"},
            "fiat": {"base": 950, "multiplier": 1.3, "reliability": "C"},
            "ford": {"base": 900, "multiplier": 1.2, "reliability": "B-"},
            "opel": {"base": 850, "multiplier": 1.1, "reliability": "B"},
            "volvo": {"base": 1200, "multiplier": 1.5, "reliability": "B+"},
            "alfa romeo": {"base": 1300, "multiplier": 1.7, "reliability": "C"}
        }
        
        # Common maintenance schedules by component
        self.maintenance_schedule = {
            "oil_change": {"interval_km": 15000, "cost": 80, "description": "Vidange moteur"},
            "oil_filter": {"interval_km": 15000, "cost": 25, "description": "Filtre à huile"},
            "air_filter": {"interval_km": 30000, "cost": 40, "description": "Filtre à air"},
            "spark_plugs": {"interval_km": 60000, "cost": 120, "description": "Bougies d'allumage"},
            "brake_pads_front": {"interval_km": 40000, "cost": 180, "description": "Plaquettes frein avant"},
            "brake_pads_rear": {"interval_km": 60000, "cost": 150, "description": "Plaquettes frein arrière"},
            "brake_discs": {"interval_km": 80000, "cost": 350, "description": "Disques de frein"},
            "timing_belt": {"interval_km": 120000, "cost": 600, "description": "Courroie de distribution"},
            "shock_absorbers": {"interval_km": 100000, "cost": 400, "description": "Amortisseurs"},
            "clutch": {"interval_km": 150000, "cost": 800, "description": "Embrayage"},
            "battery": {"interval_years": 4, "cost": 120, "description": "Batterie"},
            "tires": {"interval_km": 45000, "cost": 400, "description": "Pneumatiques"}
        }
        
        # Age-based deterioration factors
        self.age_deterioration = {
            0: 1.0,   # New car
            3: 1.1,   # 3 years
            5: 1.3,   # 5 years
            8: 1.6,   # 8 years
            10: 2.0,  # 10 years
            15: 2.8,  # 15+ years
        }
        
        # Mileage-based wear factors
        self.mileage_factors = {
            50000: 1.0,
            100000: 1.3,
            150000: 1.7,
            200000: 2.2,
            250000: 3.0
        }
        
        # Common issues by brand and age
        self.common_issues = {
            "bmw": {
                "3-7_years": [
                    {"issue": "Système de refroidissement", "probability": 0.3, "cost": 800},
                    {"issue": "Capteurs électroniques", "probability": 0.4, "cost": 400},
                    {"issue": "Système d'injection", "probability": 0.2, "cost": 1200}
                ],
                "8-15_years": [
                    {"issue": "Suspension pneumatique", "probability": 0.5, "cost": 1500},
                    {"issue": "Boîte automatique", "probability": 0.3, "cost": 3000},
                    {"issue": "Turbocompresseur", "probability": 0.4, "cost": 2000}
                ]
            },
            "mercedes": {
                "3-7_years": [
                    {"issue": "Système électronique", "probability": 0.4, "cost": 600},
                    {"issue": "Climatisation", "probability": 0.3, "cost": 500}
                ],
                "8-15_years": [
                    {"issue": "Suspension Airmatic", "probability": 0.6, "cost": 2000},
                    {"issue": "Électronique complexe", "probability": 0.5, "cost": 1200}
                ]
            },
            "audi": {
                "3-7_years": [
                    {"issue": "Système Quattro", "probability": 0.25, "cost": 1000},
                    {"issue": "Électronique", "probability": 0.35, "cost": 500}
                ],
                "8-15_years": [
                    {"issue": "DSG/S-Tronic", "probability": 0.4, "cost": 2500},
                    {"issue": "Turbo", "probability": 0.3, "cost": 1800}
                ]
            },
            "renault": {
                "3-7_years": [
                    {"issue": "Électronique", "probability": 0.3, "cost": 300},
                    {"issue": "Injection diesel", "probability": 0.2, "cost": 800}
                ],
                "8-15_years": [
                    {"issue": "Boîte de vitesses", "probability": 0.3, "cost": 1500},
                    {"issue": "Moteur (joints)", "probability": 0.25, "cost": 1200}
                ]
            },
            "peugeot": {
                "3-7_years": [
                    {"issue": "FAP (filtre à particules)", "probability": 0.4, "cost": 600},
                    {"issue": "Électronique", "probability": 0.3, "cost": 350}
                ],
                "8-15_years": [
                    {"issue": "Distribution", "probability": 0.35, "cost": 800},
                    {"issue": "Suspension arrière", "probability": 0.3, "cost": 600}
                ]
            }
        }

    def predict_maintenance_costs(self, car: Car, db: Session) -> dict:
        """Predict maintenance costs for the next 5 years"""
        
        # Extract brand from title
        brand = self._extract_brand(car.title)
        
        # Get brand maintenance profile
        brand_profile = self.brand_maintenance_costs.get(brand, {
            "base": 1000, "multiplier": 1.3, "reliability": "C"
        })
        
        # Calculate current vehicle profile
        current_age = datetime.now().year - (car.year or 2010)
        current_mileage = car.mileage or 100000
        
        # Generate yearly predictions
        yearly_predictions = []
        cumulative_cost = 0
        
        for year in range(1, 6):  # Next 5 years
            future_age = current_age + year
            future_mileage = current_mileage + (15000 * year)  # Assume 15k km/year
            
            yearly_cost = self._calculate_yearly_cost(
                brand_profile, future_age, future_mileage, year
            )
            
            cumulative_cost += yearly_cost["total_cost"]
            
            yearly_predictions.append({
                "year": year,
                "vehicle_age": future_age,
                "expected_mileage": future_mileage,
                "routine_maintenance": yearly_cost["routine"],
                "wear_items": yearly_cost["wear_items"],
                "potential_repairs": yearly_cost["repairs"],
                "total_cost": yearly_cost["total_cost"],
                "cumulative_cost": cumulative_cost,
                "major_services": yearly_cost["major_services"]
            })
        
        # Generate maintenance schedule
        maintenance_schedule = self._generate_maintenance_schedule(
            car, current_mileage, current_age
        )
        
        # Identify common repairs for this brand/age
        common_repairs = self._get_common_repairs(brand, current_age + 2)  # Average over prediction period
        
        # Calculate parts availability
        parts_availability = self._assess_parts_availability(brand, current_age)
        
        # Generate AI insights
        ai_insights = self._generate_ai_maintenance_insights(car, yearly_predictions, brand_profile)
        
        return {
            "car_info": {
                "id": car.id,
                "title": car.title,
                "brand": brand,
                "current_age": current_age,
                "current_mileage": current_mileage
            },
            "predicted_costs": yearly_predictions,
            "total_5year_cost": cumulative_cost,
            "maintenance_schedule": maintenance_schedule,
            "common_repairs": common_repairs,
            "parts_availability": parts_availability,
            "reliability_grade": brand_profile["reliability"],
            "cost_category": self._categorize_costs(cumulative_cost),
            "ai_insights": ai_insights,
            "recommendations": self._generate_maintenance_recommendations(
                yearly_predictions, brand_profile, parts_availability
            )
        }

    def _extract_brand(self, title: str) -> str:
        """Extract car brand from title"""
        title_lower = title.lower()
        
        # Check each brand
        for brand in self.brand_maintenance_costs.keys():
            if brand in title_lower:
                return brand
        
        # Default to generic if not found
        return "generic"

    def _calculate_yearly_cost(self, brand_profile: dict, age: int, mileage: int, year: int) -> dict:
        """Calculate maintenance cost for a specific year"""
        
        base_cost = brand_profile["base"]
        multiplier = brand_profile["multiplier"]
        
        # Age deterioration factor
        age_factor = 1.0
        for age_threshold in sorted(self.age_deterioration.keys(), reverse=True):
            if age >= age_threshold:
                age_factor = self.age_deterioration[age_threshold]
                break
        
        # Mileage wear factor
        mileage_factor = 1.0
        for mileage_threshold in sorted(self.mileage_factors.keys(), reverse=True):
            if mileage >= mileage_threshold:
                mileage_factor = self.mileage_factors[mileage_threshold]
                break
        
        # Calculate component costs
        routine_cost = base_cost * 0.4  # 40% routine maintenance
        wear_items_cost = base_cost * 0.3 * age_factor  # 30% wear items, age adjusted
        repair_cost = base_cost * 0.3 * multiplier * mileage_factor  # 30% repairs, brand & mileage adjusted
        
        # Major services (timing belt, clutch, etc.)
        major_services = self._get_major_services_for_year(mileage, year)
        major_services_cost = sum(service["cost"] for service in major_services)
        
        total_cost = int(routine_cost + wear_items_cost + repair_cost + major_services_cost)
        
        return {
            "routine": int(routine_cost),
            "wear_items": int(wear_items_cost),
            "repairs": int(repair_cost),
            "major_services": major_services,
            "total_cost": total_cost
        }

    def _get_major_services_for_year(self, mileage: int, year: int) -> list:
        """Get major services needed in a specific year"""
        services = []
        
        # Check each maintenance item
        for item_name, item_data in self.maintenance_schedule.items():
            if "interval_km" in item_data:
                # Check if service is due this year (within 15k km range)
                if (mileage - 7500) <= item_data["interval_km"] <= (mileage + 7500):
                    # Check if it's a major service (cost > 200)
                    if item_data["cost"] > 200:
                        services.append({
                            "service": item_data["description"],
                            "cost": item_data["cost"],
                            "mileage": item_data["interval_km"]
                        })
            elif "interval_years" in item_data:
                # Time-based service
                if year == item_data["interval_years"]:
                    services.append({
                        "service": item_data["description"],
                        "cost": item_data["cost"],
                        "reason": f"Every {item_data['interval_years']} years"
                    })
        
        return services

    def _generate_maintenance_schedule(self, car: Car, current_mileage: int, current_age: int) -> list:
        """Generate detailed maintenance schedule"""
        schedule = []
        
        for item_name, item_data in self.maintenance_schedule.items():
            if "interval_km" in item_data:
                # Calculate when next service is due
                next_service_km = ((current_mileage // item_data["interval_km"]) + 1) * item_data["interval_km"]
                km_until_service = next_service_km - current_mileage
                
                # Estimate when this will occur (assuming 15k km/year)
                years_until_service = km_until_service / 15000
                
                schedule.append({
                    "item": item_data["description"],
                    "current_mileage": current_mileage,
                    "next_service_km": next_service_km,
                    "km_until_service": km_until_service,
                    "estimated_years": round(years_until_service, 1),
                    "cost": item_data["cost"],
                    "priority": "high" if km_until_service < 10000 else "medium" if km_until_service < 30000 else "low"
                })
            elif "interval_years" in item_data:
                # Time-based maintenance
                years_until_service = item_data["interval_years"] - (current_age % item_data["interval_years"])
                
                schedule.append({
                    "item": item_data["description"],
                    "interval_years": item_data["interval_years"],
                    "years_until_service": years_until_service,
                    "cost": item_data["cost"],
                    "priority": "high" if years_until_service <= 1 else "medium"
                })
        
        # Sort by priority and time until service
        priority_order = {"high": 1, "medium": 2, "low": 3}
        schedule.sort(key=lambda x: (priority_order.get(x["priority"], 3), 
                                   x.get("years_until_service", x.get("estimated_years", 5))))
        
        return schedule

    def _get_common_repairs(self, brand: str, avg_age: int) -> list:
        """Get common repairs for brand and age range"""
        
        if brand not in self.common_issues:
            return []
        
        brand_issues = self.common_issues[brand]
        
        # Determine age category
        if 3 <= avg_age <= 7:
            age_category = "3-7_years"
        elif 8 <= avg_age <= 15:
            age_category = "8-15_years"
        else:
            return []
        
        if age_category not in brand_issues:
            return []
        
        issues = brand_issues[age_category]
        
        # Sort by probability (most likely first)
        return sorted(issues, key=lambda x: x["probability"], reverse=True)

    def _assess_parts_availability(self, brand: str, age: int) -> str:
        """Assess parts availability based on brand and age"""
        
        # Premium brands generally have better parts availability
        premium_brands = ["bmw", "mercedes", "audi", "volvo"]
        mainstream_brands = ["renault", "peugeot", "citroën", "volkswagen", "toyota", "honda"]
        
        if age < 5:
            return "excellent"
        elif age < 10:
            if brand in premium_brands:
                return "very_good"
            elif brand in mainstream_brands:
                return "good"
            else:
                return "fair"
        elif age < 15:
            if brand in mainstream_brands:
                return "good"
            elif brand in premium_brands:
                return "fair"
            else:
                return "limited"
        else:
            if brand in ["renault", "peugeot", "citroën"]:
                return "fair"
            else:
                return "limited"

    def _categorize_costs(self, total_5year_cost: int) -> str:
        """Categorize maintenance costs"""
        if total_5year_cost < 5000:
            return "low"
        elif total_5year_cost < 8000:
            return "moderate"
        elif total_5year_cost < 12000:
            return "high"
        else:
            return "very_high"

    def _generate_ai_maintenance_insights(self, car: Car, predictions: list, brand_profile: dict) -> dict:
        """Generate AI insights about maintenance costs"""
        
        if not self.anthropic_client:
            return {"error": "AI analysis not available"}
        
        try:
            total_cost = predictions[-1]["cumulative_cost"]
            avg_annual_cost = total_cost / 5
            
            prompt = f"""
            Analysez les coûts de maintenance prévus pour cette voiture française:
            
            Voiture: {car.title}
            Année: {car.year}
            Kilométrage: {car.mileage} km
            Coût total 5 ans: {total_cost}€
            Coût annuel moyen: {avg_annual_cost:.0f}€
            Fiabilité marque: {brand_profile["reliability"]}
            
            Coûts par année:
            {chr(10).join([f"Année {p['year']}: {p['total_cost']}€" for p in predictions[:3]])}
            
            Fournissez une analyse en JSON avec:
            1. cost_assessment: évaluation des coûts (abordable/élevé/très élevé)
            2. peak_years: années avec coûts les plus élevés et pourquoi
            3. cost_optimization: conseils pour réduire les coûts
            4. reliability_outlook: perspective de fiabilité
            5. budget_planning: conseils de planification budgétaire
            6. resale_impact: impact sur la valeur de revente
            
            Répondez uniquement en JSON français.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=700,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return json.loads(message.content[0].text)
            
        except Exception as e:
            return {"error": f"AI insights failed: {str(e)}"}

    def _generate_maintenance_recommendations(self, predictions: list, brand_profile: dict, parts_availability: str) -> list:
        """Generate maintenance recommendations"""
        
        recommendations = []
        total_cost = predictions[-1]["cumulative_cost"]
        avg_annual = total_cost / 5
        
        # Cost-based recommendations
        if avg_annual > 2000:
            recommendations.append("💰 Coûts élevés - Négociez le prix d'achat en conséquence")
        elif avg_annual < 1000:
            recommendations.append("✅ Coûts de maintenance raisonnables")
        
        # Reliability-based recommendations  
        if brand_profile["reliability"] in ["A", "A-"]:
            recommendations.append("🔧 Excellente fiabilité - Maintenance préventive suffisante")
        elif brand_profile["reliability"] in ["C", "C-", "D"]:
            recommendations.append("⚠️ Fiabilité moyenne - Budget réparations imprévisibles")
        
        # Parts availability recommendations
        if parts_availability == "limited":
            recommendations.append("🔍 Pièces difficiles à trouver - Vérifiez disponibilité avant achat")
        elif parts_availability == "excellent":
            recommendations.append("🔧 Pièces facilement disponibles")
        
        # Age-based recommendations
        current_age = datetime.now().year - (predictions[0].get("vehicle_age", 10) - 1)
        if current_age > 10:
            recommendations.append("📅 Véhicule ancien - Inspectez état avant achat")
        
        # Peak cost years
        peak_years = sorted(predictions, key=lambda x: x["total_cost"], reverse=True)[:2]
        if peak_years[0]["total_cost"] > avg_annual * 1.5:
            recommendations.append(f"📈 Année {peak_years[0]['year']}: coûts élevés prévus ({peak_years[0]['total_cost']}€)")
        
        return recommendations

    def save_maintenance_prediction(self, car: Car, prediction_data: dict, db: Session) -> str:
        """Save maintenance prediction to database"""
        
        prediction = MaintenancePrediction(
            id=str(uuid.uuid4()),
            car_id=car.id,
            make_model=car.title.split()[0:2] if car.title else ["Unknown"],
            predicted_costs=prediction_data["predicted_costs"],
            maintenance_schedule=prediction_data["maintenance_schedule"],
            common_repairs=prediction_data["common_repairs"],
            parts_availability=prediction_data["parts_availability"],
            total_5year_cost=prediction_data["total_5year_cost"],
            reliability_grade=prediction_data["reliability_grade"]
        )
        
        db.add(prediction)
        db.commit()
        
        return prediction.id

    def get_maintenance_insights(self, car_id: str, db: Session) -> dict:
        """Get maintenance insights for a specific car"""
        
        prediction = db.query(MaintenancePrediction).filter(
            MaintenancePrediction.car_id == car_id
        ).first()
        
        if not prediction:
            return {"message": "No maintenance prediction available"}
        
        return {
            "car_id": prediction.car_id,
            "predicted_costs": prediction.predicted_costs,
            "total_5year_cost": prediction.total_5year_cost,
            "maintenance_schedule": prediction.maintenance_schedule,
            "common_repairs": prediction.common_repairs,
            "parts_availability": prediction.parts_availability,
            "reliability_grade": prediction.reliability_grade,
            "calculated_at": prediction.calculated_at.isoformat()
        }

    def get_cost_comparison_by_brand(self, db: Session) -> dict:
        """Get maintenance cost comparison by brand"""
        
        predictions = db.query(MaintenancePrediction).all()
        
        brand_costs = {}
        
        for prediction in predictions:
            if prediction.make_model and len(prediction.make_model) > 0:
                brand = prediction.make_model[0].lower()
                
                if brand not in brand_costs:
                    brand_costs[brand] = {
                        "costs": [],
                        "reliability_grades": [],
                        "count": 0
                    }
                
                brand_costs[brand]["costs"].append(prediction.total_5year_cost)
                brand_costs[brand]["reliability_grades"].append(prediction.reliability_grade)
                brand_costs[brand]["count"] += 1
        
        # Calculate averages
        comparison = {}
        for brand, data in brand_costs.items():
            if data["count"] > 0:
                comparison[brand] = {
                    "average_5year_cost": int(mean(data["costs"])),
                    "median_5year_cost": int(median(data["costs"])),
                    "sample_count": data["count"],
                    "common_reliability_grade": max(set(data["reliability_grades"]), key=data["reliability_grades"].count) if data["reliability_grades"] else "Unknown"
                }
        
        # Sort by average cost
        sorted_comparison = dict(sorted(comparison.items(), key=lambda x: x[1]["average_5year_cost"]))
        
        return {
            "brand_comparison": sorted_comparison,
            "analysis_date": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    prophet = MaintenanceCostProphet()
    db = SessionLocal()
    
    # Test with first car
    car = db.query(Car).filter(Car.year.isnot(None)).first()
    if car:
        print(f"Predicting maintenance costs for: {car.title}")
        prediction = prophet.predict_maintenance_costs(car, db)
        
        print(f"Total 5-year cost: {prediction['total_5year_cost']}€")
        print(f"Reliability grade: {prediction['reliability_grade']}")
        print(f"Cost category: {prediction['cost_category']}")
        print(f"Parts availability: {prediction['parts_availability']}")
        
        # Show upcoming maintenance
        upcoming = [item for item in prediction['maintenance_schedule'] if item['priority'] == 'high']
        if upcoming:
            print(f"Upcoming maintenance: {upcoming[0]['item']} - {upcoming[0]['cost']}€")
        
        # Save prediction
        prediction_id = prophet.save_maintenance_prediction(car, prediction, db)
        print(f"Prediction saved with ID: {prediction_id}")
    else:
        print("No cars with year information found")
    
    db.close()