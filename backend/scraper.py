import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, Car
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LeBonCoinScraper:
    def __init__(self, department="69", max_cars=100):
        self.department = department
        self.max_cars = max_cars
        self.base_url = "https://api.leboncoin.fr/finder/classified"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        })
        
    def search_cars(self):
        """Search for cars on LeBonCoin"""
        payload = {
            "limit": 35,
            "limit_alu": 3,
            "filters": {
                "category": {"id": "2"},
                "enums": {
                    "ad_type": ["offer"]
                },
                "location": {
                    "departments": [self.department]
                }
            }
        }
        
        cars = []
        offset = 0
        
        while len(cars) < self.max_cars:
            payload["offset"] = offset
            
            try:
                response = self.session.post(self.base_url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                ads = data.get("ads", [])
                
                if not ads:
                    break
                
                for ad in ads:
                    if len(cars) >= self.max_cars:
                        break
                        
                    car_data = self.extract_car_data(ad)
                    if car_data:
                        cars.append(car_data)
                
                offset += 35
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching cars: {e}")
                break
        
        return cars
    
    def extract_car_data(self, ad):
        """Extract car data from LeBonCoin ad"""
        try:
            attributes = {attr["key"]: attr["value"] for attr in ad.get("attributes", [])}
            
            images = []
            for image in ad.get("images", {}).get("urls_large", []):
                images.append(image)
            
            car_data = {
                "id": ad["list_id"],
                "title": ad.get("subject", ""),
                "price": ad.get("price", [0])[0] if ad.get("price") else None,
                "year": int(attributes.get("regdate", 0)) if attributes.get("regdate") else None,
                "mileage": int(attributes.get("mileage", 0)) if attributes.get("mileage") else None,
                "fuel_type": attributes.get("fuel", ""),
                "description": ad.get("body", ""),
                "images": json.dumps(images),
                "url": ad.get("url", ""),
                "seller_type": ad.get("owner", {}).get("type", ""),
                "department": self.department,
                "first_seen": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "is_active": True
            }
            
            return car_data
            
        except Exception as e:
            logger.error(f"Error extracting car data: {e}")
            return None
    
    def save_to_database(self, cars):
        """Save cars to database with deduplication"""
        db = SessionLocal()
        saved_count = 0
        updated_count = 0
        
        try:
            for car_data in cars:
                existing_car = db.query(Car).filter(Car.id == car_data["id"]).first()
                
                if existing_car:
                    # Update last_seen timestamp
                    existing_car.last_seen = datetime.utcnow()
                    existing_car.is_active = True
                    updated_count += 1
                else:
                    # Create new car entry
                    new_car = Car(**car_data)
                    db.add(new_car)
                    saved_count += 1
            
            db.commit()
            logger.info(f"Saved {saved_count} new cars, updated {updated_count} existing cars")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            db.rollback()
        finally:
            db.close()
    
    def run(self):
        """Run the scraper"""
        logger.info(f"Starting scraper for department {self.department}")
        cars = self.search_cars()
        logger.info(f"Found {len(cars)} cars")
        
        if cars:
            self.save_to_database(cars)
        
        # Mark inactive cars (not seen in this run)
        self.mark_inactive_cars()
    
    def mark_inactive_cars(self):
        """Mark cars as inactive if not seen recently"""
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            inactive_cars = db.query(Car).filter(
                Car.last_seen < cutoff_time,
                Car.is_active == True
            ).update({"is_active": False})
            
            db.commit()
            logger.info(f"Marked {inactive_cars} cars as inactive")
            
        except Exception as e:
            logger.error(f"Error marking inactive cars: {e}")
            db.rollback()
        finally:
            db.close()

def create_sample_data():
    """Create sample car data for testing"""
    db = SessionLocal()
    
    sample_cars = [
        {
            "id": str(uuid.uuid4()),
            "title": "Renault Clio IV 1.5 dCi 90 Business",
            "price": 12500,
            "year": 2018,
            "mileage": 65000,
            "fuel_type": "diesel",
            "description": "Véhicule en excellent état, entretien suivi, non fumeur",
            "images": json.dumps(["image1.jpg", "image2.jpg"]),
            "url": "https://leboncoin.fr/sample1",
            "seller_type": "particulier",
            "department": "69",
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Peugeot 208 1.2 PureTech 82 Allure",
            "price": 15800,
            "year": 2019,
            "mileage": 42000,
            "fuel_type": "essence",
            "description": "Première main, carnet d'entretien, garantie constructeur",
            "images": json.dumps(["image3.jpg", "image4.jpg"]),
            "url": "https://leboncoin.fr/sample2",
            "seller_type": "professionnel",
            "department": "69",
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "is_active": True
        }
    ]
    
    try:
        for car_data in sample_cars:
            existing = db.query(Car).filter(Car.id == car_data["id"]).first()
            if not existing:
                new_car = Car(**car_data)
                db.add(new_car)
        
        db.commit()
        logger.info("Sample data created successfully")
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    scraper = LeBonCoinScraper()
    scraper.run()