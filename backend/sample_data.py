import json
import uuid
from datetime import datetime, timedelta
from database import SessionLocal, Car, create_tables
import random

def create_sample_cars():
    """Create 20 sample cars for testing"""
    
    create_tables()
    db = SessionLocal()
    
    sample_cars_data = [
        {
            "title": "Renault Clio IV 1.5 dCi 90 Business",
            "price": 12500,
            "year": 2018,
            "mileage": 65000,
            "fuel_type": "diesel",
            "description": "Véhicule en excellent état, première main, entretien suivi en concession. Non fumeur. Carnet d'entretien complet. Pneus récents. Contrôle technique OK.",
            "seller_type": "particulier",
            "department": "69"
        },
        {
            "title": "Peugeot 208 1.2 PureTech 82 Allure",
            "price": 15800,
            "year": 2019,
            "mileage": 42000,
            "fuel_type": "essence",
            "description": "Véhicule de seconde main en parfait état. Garantie constructeur restante. Toutes révisions faites en temps et en heure. Véhicule non accidenté.",
            "seller_type": "professionnel",
            "department": "69"
        },
        {
            "title": "Volkswagen Golf VII 1.6 TDI 105 Confortline",
            "price": 18900,
            "year": 2017,
            "mileage": 85000,
            "fuel_type": "diesel",
            "description": "Golf en très bon état général. Entretien régulier. Climatisation, GPS, sièges chauffants. Quelques rayures sur la carrosserie mais rien de grave.",
            "seller_type": "particulier",
            "department": "75"
        },
        {
            "title": "BMW Serie 3 320d 163ch Efficientdynamics Edition",
            "price": 24500,
            "year": 2016,
            "mileage": 120000,
            "fuel_type": "diesel",
            "description": "BMW Série 3 en excellent état. Entretien BMW uniquement. Cuir, navigation, phares xenon. Véhicule très bien entretenu, aucun souci mécanique.",
            "seller_type": "professionnel",
            "department": "13"
        },
        {
            "title": "Ford Fiesta 1.0 EcoBoost 100ch ST-Line",
            "price": 13200,
            "year": 2018,
            "mileage": 52000,
            "fuel_type": "essence",
            "description": "Fiesta ST-Line en parfait état. Première main, carnet d'entretien. Jantes alliage, écran tactile, caméra de recul. Très économique.",
            "seller_type": "particulier",
            "department": "33"
        },
        {
            "title": "Audi A3 Sportback 2.0 TDI 150ch S Line",
            "price": 22800,
            "year": 2017,
            "mileage": 78000,
            "fuel_type": "diesel",
            "description": "A3 S-Line impeccable. Entretien Audi. Cuir, GPS, phares LED. Quelques options supplémentaires. Véhicule de garage, jamais eu de problème.",
            "seller_type": "professionnel",
            "department": "69"
        },
        {
            "title": "Citroën C3 1.2 PureTech 82ch Feel",
            "price": 11900,
            "year": 2019,
            "mileage": 35000,
            "fuel_type": "essence",
            "description": "C3 Feel comme neuve. Garantie jusqu'en 2024. Toujours garée au garage. Entretien Citroën. Écran tactile, aide au stationnement.",
            "seller_type": "particulier",
            "department": "59"
        },
        {
            "title": "Mercedes Classe A 180 CDI Intuition",
            "price": 16500,
            "year": 2016,
            "mileage": 95000,
            "fuel_type": "diesel",
            "description": "Classe A en bon état général. Entretien Mercedes. Quelques traces d'usure normales. Climatisation, régulateur de vitesse, Bluetooth.",
            "seller_type": "professionnel",
            "department": "31"
        },
        {
            "title": "Opel Corsa 1.4 90ch Design 120 ans",
            "price": 9800,
            "year": 2019,
            "mileage": 28000,
            "fuel_type": "essence",
            "description": "Corsa édition spéciale 120 ans. Peu de kilomètres, parfait état. Écran IntelliLink, caméra, climatisation automatique. Idéale première voiture.",
            "seller_type": "particulier",
            "department": "44"
        },
        {
            "title": "Toyota Yaris 1.5 Hybrid 100h Dynamic Business",
            "price": 17200,
            "year": 2018,
            "mileage": 67000,
            "fuel_type": "hybride",
            "description": "Yaris hybride économique. Consommation 3.5L/100km. Entretien Toyota. Caméra de recul, écran tactile, climatisation automatique.",
            "seller_type": "professionnel",
            "department": "67"
        },
        {
            "title": "Seat Ibiza 1.0 TSI 95ch Start/Stop",
            "price": 12200,
            "year": 2018,
            "mileage": 58000,
            "fuel_type": "essence",
            "description": "Ibiza en très bon état. Moteur TSI fiable et économique. Entretien régulier. Climatisation, Bluetooth, USB. Pneus neufs à l'avant.",
            "seller_type": "particulier",
            "department": "06"
        },
        {
            "title": "Dacia Sandero Stepway 0.9 TCe 90ch",
            "price": 8900,
            "year": 2017,
            "mileage": 72000,
            "fuel_type": "essence",
            "description": "Sandero Stepway pratique et économique. Entretien suivi. Barres de toit, écran MediaNav, climatisation. Parfait pour la famille.",
            "seller_type": "particulier",
            "department": "69"
        },
        {
            "title": "Nissan Qashqai 1.5 dCi 110ch N-Connecta",
            "price": 19500,
            "year": 2017,
            "mileage": 89000,
            "fuel_type": "diesel",
            "description": "Qashqai N-Connecta très équipé. GPS, caméra 360°, sièges chauffants. Entretien Nissan. Véhicule familial idéal, très confortable.",
            "seller_type": "professionnel",
            "department": "75"
        },
        {
            "title": "Skoda Fabia 1.0 TSI 95ch Monte Carlo",
            "price": 13800,
            "year": 2018,
            "mileage": 48000,
            "fuel_type": "essence",
            "description": "Fabia Monte Carlo sportive. Finition haut de gamme. Jantes 17', intérieur sport, écran tactile. Entretien Skoda, parfait état.",
            "seller_type": "particulier",
            "department": "13"
        },
        {
            "title": "Hyundai i20 1.2 84ch Intuitive",
            "price": 10500,
            "year": 2018,
            "mileage": 61000,
            "fuel_type": "essence",
            "description": "i20 Intuitive bien équipée. Garantie 5 ans constructeur. Écran tactile, climatisation, aide au stationnement. Entretien Hyundai.",
            "seller_type": "professionnel",
            "department": "33"
        },
        {
            "title": "Kia Picanto 1.0 67ch Active",
            "price": 7800,
            "year": 2017,
            "mileage": 45000,
            "fuel_type": "essence",
            "description": "Picanto Active parfaite pour la ville. Très économique, facile à garer. Entretien Kia. Garantie 7 ans constructeur. Climatisation, Bluetooth.",
            "seller_type": "particulier",
            "department": "59"
        },
        {
            "title": "Mazda CX-3 2.0 SKYACTIV-G 121ch Dynamique",
            "price": 16800,
            "year": 2017,
            "mileage": 76000,
            "fuel_type": "essence",
            "description": "CX-3 Dynamique en excellent état. SUV compact idéal. Intérieur cuir, GPS, caméra de recul. Entretien Mazda. Très fiable.",
            "seller_type": "professionnel",
            "department": "31"
        },
        {
            "title": "Fiat 500 1.2 8v 69ch Pop",
            "price": 9200,
            "year": 2018,
            "mileage": 38000,
            "fuel_type": "essence",
            "description": "500 Pop iconique. Parfait état, toujours garée au garage. Climatisation, écran Uconnect. Idéale pour la ville. Entretien Fiat.",
            "seller_type": "particulier",
            "department": "44"
        },
        {
            "title": "Honda Civic 1.0 VTEC Turbo 126ch Executive",
            "price": 18500,
            "year": 2017,
            "mileage": 82000,
            "fuel_type": "essence",
            "description": "Civic Executive haut de gamme. Finition cuir, navigation Honda CONNECT, toit ouvrant. Entretien Honda. Véhicule très fiable.",
            "seller_type": "professionnel",
            "department": "67"
        },
        {
            "title": "Suzuki Swift 1.2 Dualjet 90ch Pack",
            "price": 11200,
            "year": 2018,
            "mileage": 55000,
            "fuel_type": "essence",
            "description": "Swift Pack bien équipée. Très maniable et économique. Écran tactile, climatisation, régulateur. Entretien Suzuki. Parfait état général.",
            "seller_type": "particulier",
            "department": "06"
        }
    ]
    
    try:
        for i, car_data in enumerate(sample_cars_data):
            car_id = str(uuid.uuid4())
            
            # Generate random images URLs (placeholder)
            images = [
                f"https://via.placeholder.com/800x600/0066cc/ffffff?text=Car+{i+1}+Photo+1",
                f"https://via.placeholder.com/800x600/cc6600/ffffff?text=Car+{i+1}+Photo+2",
                f"https://via.placeholder.com/800x600/009966/ffffff?text=Car+{i+1}+Photo+3"
            ]
            
            # Random date in the last 30 days
            days_ago = random.randint(1, 30)
            first_seen = datetime.utcnow() - timedelta(days=days_ago)
            last_seen = datetime.utcnow() - timedelta(days=random.randint(0, days_ago))
            
            existing = db.query(Car).filter(Car.id == car_id).first()
            if not existing:
                new_car = Car(
                    id=car_id,
                    source="leboncoin",
                    title=car_data["title"],
                    price=car_data["price"],
                    year=car_data["year"],
                    mileage=car_data["mileage"],
                    fuel_type=car_data["fuel_type"],
                    description=car_data["description"],
                    images=json.dumps(images),
                    url=f"https://www.leboncoin.fr/voitures/{car_id}.htm",
                    seller_type=car_data["seller_type"],
                    department=car_data["department"],
                    first_seen=first_seen,
                    last_seen=last_seen,
                    is_active=True
                )
                db.add(new_car)
        
        db.commit()
        print(f"✅ Successfully created {len(sample_cars_data)} sample cars")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚗 Creating sample car data...")
    create_sample_cars()
    print("✨ Sample data creation completed!")