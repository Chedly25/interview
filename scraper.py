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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Origin': 'https://www.leboncoin.fr',
            'Referer': 'https://www.leboncoin.fr/'
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
                },
                "keywords": {}
            },
            "owner_type": "all",
            "sort_by": "time",
            "sort_order": "desc"
        }
        
        cars = []
        offset = 0
        
        while len(cars) < self.max_cars:
            payload["offset"] = offset
            
            try:
                logger.info(f"Fetching cars with offset {offset}")
                response = self.session.post(self.base_url, json=payload)
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"API returned status {response.status_code}: {response.text}")
                    break
                
                data = response.json()
                ads = data.get("ads", [])
                logger.info(f"Found {len(ads)} ads in this batch")
                
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
        logger.info(f"🚗 Starting scraper for department {self.department}")
        
        try:
            cars = self.search_cars()
            logger.info(f"Found {len(cars)} cars")
            
            if cars:
                self.save_to_database(cars)
                logger.info(f"✅ Successfully scraped and saved {len(cars)} cars")
            else:
                logger.warning("⚠️ No cars found - falling back to sample data")
                # If no cars found, create sample data for testing
                self.create_sample_data_if_empty()
            
            # Mark inactive cars (not seen in this run)
            self.mark_inactive_cars()
            
        except Exception as e:
            logger.error(f"❌ Scraper failed: {e}")
            # If scraping fails completely, ensure we have sample data
            self.create_sample_data_if_empty()
    
    def create_sample_data_if_empty(self):
        """Create sample data if database is empty"""
        db = SessionLocal()
        try:
            car_count = db.query(Car).count()
            if car_count == 0:
                logger.info("📝 Creating sample data...")
                create_sample_data()
                logger.info("✅ Sample data created")
            else:
                logger.info(f"📊 Database has {car_count} cars")
        except Exception as e:
            logger.error(f"Error checking/creating sample data: {e}")
        finally:
            db.close()
    
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
            "description": "Véhicule en excellent état, entretien suivi en concession Renault. Non fumeur, toujours garé au garage. Révision faite à 60000 km. Climatisation, GPS, Bluetooth. Contrôle technique OK jusqu'en 2025.",
            "images": json.dumps([
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample1.jpg",
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample2.jpg"
            ]),
            "url": "https://www.leboncoin.fr/sample1",
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
            "description": "Première main, carnet d'entretien complet. Garantie constructeur jusqu'en 2024. Jantes alliage, régulateur de vitesse, caméra de recul. Parfait état.",
            "images": json.dumps([
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample3.jpg",
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample4.jpg"
            ]),
            "url": "https://www.leboncoin.fr/sample2",
            "seller_type": "professionnel",
            "department": "69",
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "title": "BMW Série 3 320d xDrive 190ch M Sport",
            "price": 28900,
            "year": 2017,
            "mileage": 89000,
            "fuel_type": "diesel",
            "description": "BMW Série 3 en très bon état. Pack M Sport complet, cuir, navigation professional, xDrive (4 roues motrices). Entretien BMW, jamais accidenté. Urgent déménagement.",
            "images": json.dumps([
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample5.jpg",
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample6.jpg"
            ]),
            "url": "https://www.leboncoin.fr/sample3",
            "seller_type": "particulier",
            "department": "69",
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Citroën C3 1.2 PureTech 82 Feel",
            "price": 11200,
            "year": 2018,
            "mileage": 78000,
            "fuel_type": "essence",
            "description": "Citroën C3 récente, climatisation automatique, écran tactile 7 pouces, radar de recul. Entretien Citroën suivi, factures disponibles.",
            "images": json.dumps([
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample7.jpg"
            ]),
            "url": "https://www.leboncoin.fr/sample4",
            "seller_type": "professionnel",
            "department": "69",
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Volkswagen Golf VII 1.6 TDI 110 Confortline",
            "price": 17500,
            "year": 2016,
            "mileage": 95000,
            "fuel_type": "diesel",
            "description": "Golf 7 diesel économique, très fiable. Boîte manuelle 5 vitesses, climatisation, ordinateur de bord. Pneus récents, distribution faite.",
            "images": json.dumps([
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample8.jpg",
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample9.jpg"
            ]),
            "url": "https://www.leboncoin.fr/sample5",
            "seller_type": "particulier",
            "department": "69",
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Mercedes Classe A 180d Business Edition",
            "price": 22900,
            "year": 2019,
            "mileage": 56000,
            "fuel_type": "diesel",
            "description": "Mercedes Classe A récente, Business Edition avec GPS, LED, caméra de recul. Garantie Mercedes jusqu'en 2025. État impeccable, première main.",
            "images": json.dumps([
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample10.jpg",
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/sample11.jpg"
            ]),
            "url": "https://www.leboncoin.fr/sample6",
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