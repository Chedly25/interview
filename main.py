from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import uuid
from datetime import datetime, timedelta
import os
import anthropic
import threading
import time

from database import get_database, Car, Analysis, create_tables
from scraper import LeBonCoinScraper

app = FastAPI(title="Automotive Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

@app.get("/api/cars")
def get_cars(
    max_price: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(20),
    db: Session = Depends(get_database)
):
    query = db.query(Car).filter(Car.is_active == True)
    
    if max_price:
        query = query.filter(Car.price <= max_price)
    if department:
        query = query.filter(Car.department == department)
    
    cars = query.offset(skip).limit(limit).all()
    
    result = []
    for car in cars:
        car_dict = {
            "id": car.id,
            "title": car.title,
            "price": car.price,
            "year": car.year,
            "mileage": car.mileage,
            "fuel_type": car.fuel_type,
            "description": car.description,
            "images": json.loads(car.images) if car.images else [],
            "url": car.url,
            "seller_type": car.seller_type,
            "department": car.department,
            "first_seen": car.first_seen.isoformat() if car.first_seen else None,
            "last_seen": car.last_seen.isoformat() if car.last_seen else None
        }
        result.append(car_dict)
    
    return {"cars": result, "total": query.count()}

@app.get("/api/cars/{car_id}")
def get_car(car_id: str, db: Session = Depends(get_database)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    return {
        "id": car.id,
        "title": car.title,
        "price": car.price,
        "year": car.year,
        "mileage": car.mileage,
        "fuel_type": car.fuel_type,
        "description": car.description,
        "images": json.loads(car.images) if car.images else [],
        "url": car.url,
        "seller_type": car.seller_type,
        "department": car.department,
        "first_seen": car.first_seen.isoformat() if car.first_seen else None,
        "last_seen": car.last_seen.isoformat() if car.last_seen else None
    }

@app.post("/api/cars/{car_id}/analyze")
def analyze_car(car_id: str, db: Session = Depends(get_database)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    # Check for cached analysis (within 7 days)
    cached_analysis = db.query(Analysis).filter(
        Analysis.car_id == car_id,
        Analysis.created_at > datetime.utcnow() - timedelta(days=7)
    ).first()
    
    if cached_analysis:
        return json.loads(cached_analysis.analysis_data)
    
    # Generate new analysis with Claude
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable.")
    
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    prompt = f"""
    Analysez cette annonce de voiture française:
    
    Titre: {car.title}
    Prix: {car.price}€
    Année: {car.year}
    Kilométrage: {car.mileage} km
    Carburant: {car.fuel_type}
    Description: {car.description}
    Type de vendeur: {car.seller_type}
    Département: {car.department}
    
    Fournissez une analyse structurée en JSON avec:
    1. price_assessment: évaluation du prix (correct/élevé/bas)
    2. red_flags: signaux d'alarme potentiels
    3. negotiation_tips: conseils de négociation
    4. overall_score: note sur 10
    5. recommendation: recommandation d'achat
    
    Répondez uniquement en JSON valide.
    """
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis_text = message.content[0].text
        analysis_data = json.loads(analysis_text)
        
        # Cache the analysis
        new_analysis = Analysis(
            id=str(uuid.uuid4()),
            car_id=car_id,
            analysis_data=json.dumps(analysis_data)
        )
        db.add(new_analysis)
        db.commit()
        
        return analysis_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

def run_scraper_background():
    """Run scraper in background"""
    try:
        scraper = LeBonCoinScraper(department="69", max_cars=100)
        scraper.run()
        return {"status": "success", "message": "Scraper completed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/scrape")
def trigger_scraper(background_tasks: BackgroundTasks):
    """Manually trigger the scraper"""
    background_tasks.add_task(run_scraper_background)
    return {"status": "started", "message": "Scraper started in background"}

@app.get("/api/scrape/status")
def scraper_status(db: Session = Depends(get_database)):
    """Get scraper status and car count"""
    total_cars = db.query(Car).count()
    active_cars = db.query(Car).filter(Car.is_active == True).count()
    latest_car = db.query(Car).order_by(Car.first_seen.desc()).first()
    
    return {
        "total_cars": total_cars,
        "active_cars": active_cars,
        "latest_scrape": latest_car.first_seen.isoformat() if latest_car else None
    }

def automatic_scraper():
    """Run scraper every 30 minutes"""
    while True:
        try:
            print("🚗 Running automatic scraper...")
            scraper = LeBonCoinScraper(department="69", max_cars=100)
            scraper.run()
            print("✅ Automatic scraper completed")
        except Exception as e:
            print(f"❌ Automatic scraper error: {e}")
        
        # Wait 30 minutes
        time.sleep(1800)

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Starting Automotive Assistant API...")
    create_tables()
    
    # Run scraper immediately on startup
    threading.Thread(target=run_scraper_background, daemon=True).start()
    
    # Start automatic scraper in background
    threading.Thread(target=automatic_scraper, daemon=True).start()
    
    print("✅ API started with automatic scraping enabled")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)