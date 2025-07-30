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
import logging

logger = logging.getLogger(__name__)

from enhanced_database import SessionLocal, Car, Analysis, create_all_tables
from scraper import LeBonCoinScraper
from scrapfly_scraper import ScrapflyLeboncoinScraper
from enhanced_database import GemScore, PhotoAnalysis, ParsedListing, NegotiationStrategy, VinData, VehicleHistory, MarketPulse, SocialSentiment, CarComparison, MaintenancePrediction, InvestmentScore
from gem_detector import HiddenGemDetector
from photo_analyzer import AIPhotoAnalyzer  
from description_parser import IntelligentDescriptionParser
from negotiation_assistant import NegotiationAssistantPro
from vin_decoder import VINDecoderHistoryBuilder
from market_pulse_predictor import MarketPulsePredictor
from social_sentiment_analyzer import SocialSentimentAnalyzer
from smart_comparison_engine import SmartComparisonEngine
from maintenance_cost_prophet import MaintenanceCostProphet
from investment_grade_scorer import InvestmentGradeScorer

app = FastAPI(title="Automotive Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_database():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

create_all_tables()

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
    Analysez cette annonce de voiture franaise:
    
    Titre: {car.title}
    Prix: {car.price}
    Anne: {car.year}
    Kilomtrage: {car.mileage} km
    Carburant: {car.fuel_type}
    Description: {car.description}
    Type de vendeur: {car.seller_type}
    Dpartement: {car.department}
    
    Fournissez une analyse structure en JSON avec:
    1. price_assessment: valuation du prix (correct/lev/bas)
    2. red_flags: signaux d'alarme potentiels
    3. negotiation_tips: conseils de ngociation
    4. overall_score: note sur 10
    5. recommendation: recommandation d'achat
    
    Rpondez uniquement en JSON valide.
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
    """Run scraper in background with fallback strategy"""
    try:
        # Try Scrapfly-enhanced scraper first
        logger.info("Attempting Scrapfly-enhanced scraping...")
        scrapfly_scraper = ScrapflyLeboncoinScraper(department="69", max_cars=100)
        scrapfly_scraper.run()
        return {"status": "success", "message": "Scrapfly scraper completed successfully"}
    except Exception as e:
        logger.warning(f"Scrapfly scraper failed: {e}")
        try:
            # Fallback to original scraper
            logger.info("Falling back to original scraper...")
            original_scraper = LeBonCoinScraper(department="69", max_cars=100)
            original_scraper.run()
            return {"status": "success", "message": "Original scraper completed successfully"}
        except Exception as e2:
            logger.error(f"Both scrapers failed: {e2}")
            # Final fallback - ensure sample data exists
            try:
                logger.info("Creating sample data as final fallback...")
                from create_sample_data import create_sample_data
                count = create_sample_data()
                logger.info(f"Sample data created: {count} cars")
                return {"status": "success", "message": f"Sample data created as fallback: {count} cars"}
            except Exception as e3:
                logger.error(f"Sample data creation failed: {e3}")
                return {"status": "error", "message": f"All fallback methods failed"}

@app.post("/api/scrape")
def trigger_scraper(background_tasks: BackgroundTasks):
    """Manually trigger the scraper"""
    background_tasks.add_task(run_scraper_background)
    return {"status": "started", "message": "Scraper started in background"}

@app.post("/api/scrape/create-sample-data")
def create_sample_data_endpoint(db: Session = Depends(get_database)):
    """Create sample car data for testing"""
    try:
        from create_sample_data import create_sample_data
        count = create_sample_data()
        
        # Count cars after creation
        car_count = db.query(Car).count()
        
        return {
            "status": "success", 
            "message": f"Sample data created successfully. Created {count} cars, total: {car_count}",
            "created_cars": count,
            "total_cars": car_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create sample data: {str(e)}")

@app.get("/")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Automotive Assistant API is running"}

@app.post("/api/scrape/scrapfly")
def trigger_scrapfly_scraper(background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Test the new Scrapfly-based scraper"""
    def run_scrapfly_scraper():
        try:
            logger.info(" Testing Scrapfly scraper...")
            scraper = ScrapflyLeboncoinScraper(department="69", max_cars=20)  # Smaller batch for testing
            scraper.run()
            logger.info(" Scrapfly scraper test completed")
        except Exception as e:
            logger.error(f" Scrapfly scraper test failed: {e}")
    
    background_tasks.add_task(run_scrapfly_scraper)
    
    # Get current car count
    current_count = db.query(Car).count()
    
    return {
        "status": "started", 
        "message": "Scrapfly scraper test started in background",
        "current_cars": current_count,
        "scraper_type": "scrapfly_enhanced"
    }

@app.get("/api/scrape/status")
def scraper_status(db: Session = Depends(get_database)):
    """Get scraper status and car count"""
    total_cars = db.query(Car).count()
    active_cars = db.query(Car).filter(Car.is_active == True).count()
    recent_cars = db.query(Car).filter(
        Car.first_seen > datetime.utcnow() - timedelta(hours=24)
    ).count()
    latest_car = db.query(Car).order_by(Car.first_seen.desc()).first()
    
    return {
        "total_cars": total_cars,
        "active_cars": active_cars,
        "recent_cars_24h": recent_cars,
        "last_scrape": latest_car.first_seen.isoformat() if latest_car else None,
        "status": "healthy" if total_cars > 0 else "needs_data"
    }

def automatic_scraper():
    """Run scraper every 30 minutes with fallback strategy"""
    while True:
        try:
            print("Running automatic scraper...")
            
            # Try Scrapfly scraper first
            try:
                print("Using Scrapfly-enhanced scraper...")
                scraper = ScrapflyLeboncoinScraper(department="69", max_cars=100)
                scraper.run()
                print("Scrapfly automatic scraper completed")
            except Exception as e:
                print(f"Scrapfly scraper failed: {e}")
                print("Falling back to original scraper...")
                
                # Fallback to original scraper
                original_scraper = LeBonCoinScraper(department="69", max_cars=100)
                original_scraper.run()
                print("Original automatic scraper completed")
                
        except Exception as e:
            print(f"All automatic scrapers failed: {e}")
        
        # Wait 30 minutes
        time.sleep(1800)

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("Starting Automotive Assistant API...")
    create_all_tables()
    
    # Ensure we have data on startup
    db = SessionLocal()
    try:
        car_count = db.query(Car).count()
        if car_count == 0:
            print("No cars found, creating sample data...")
            from create_sample_data import create_sample_data
            create_sample_data()
            print("Sample data created!")
        else:
            print(f"Found {car_count} cars in database")
    except Exception as e:
        print(f"Error checking/creating data: {e}")
    finally:
        db.close()
    
    # Run scraper immediately on startup
    threading.Thread(target=run_scraper_background, daemon=True).start()
    
    # Start automatic scraper in background
    threading.Thread(target=automatic_scraper, daemon=True).start()
    
    print("API started with automatic scraping enabled")

# Initialize AI analyzers
gem_detector = HiddenGemDetector()
photo_analyzer = AIPhotoAnalyzer()
description_parser = IntelligentDescriptionParser()
negotiation_assistant = NegotiationAssistantPro()
vin_decoder = VINDecoderHistoryBuilder()
market_predictor = MarketPulsePredictor()
sentiment_analyzer = SocialSentimentAnalyzer()
comparison_engine = SmartComparisonEngine()
maintenance_prophet = MaintenanceCostProphet()
investment_scorer = InvestmentGradeScorer()

# FEATURE 1: Hidden Gem Detector Endpoints
@app.get("/api/cars/{car_id}/gem-analysis")
def get_gem_analysis(car_id: str, db: Session = Depends(get_database)):
    """Get hidden gem analysis for a specific car"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    # Check for existing analysis
    existing = db.query(GemScore).filter(GemScore.car_id == car_id).first()
    if existing:
        return {
            "gem_score": existing.gem_score,
            "reasons": existing.reasons,
            "profit_potential": existing.profit_potential,
            "risk_factors": existing.risk_factors,
            "market_position": existing.market_position,
            "confidence_level": existing.confidence_level,
            "analyzed_at": existing.created_at.isoformat()
        }
    
    # Generate new analysis
    analysis = gem_detector.calculate_gem_score(car, db)
    
    # Save analysis
    gem_score = GemScore(
        car_id=car_id,
        gem_score=analysis["gem_score"],
        reasons=analysis["reasons"],
        profit_potential=analysis["profit_potential"],
        risk_factors=analysis["risk_factors"],
        market_position=analysis["market_position"],
        confidence_level=analysis["confidence_level"]
    )
    db.add(gem_score)
    db.commit()
    
    return analysis

@app.get("/api/gems/top")
def get_top_gems(limit: int = 20, db: Session = Depends(get_database)):
    """Get top hidden gems with highest scores"""
    top_gems = db.query(GemScore).join(Car).filter(
        Car.is_active == True
    ).order_by(GemScore.gem_score.desc()).limit(limit).all()
    
    result = []
    for gem in top_gems:
        car = db.query(Car).filter(Car.id == gem.car_id).first()
        if car:
            result.append({
                "car": {
                    "id": car.id,
                    "title": car.title,
                    "price": car.price,
                    "year": car.year,
                    "mileage": car.mileage,
                    "department": car.department,
                    "images": json.loads(car.images) if car.images else []
                },
                "gem_analysis": {
                    "gem_score": gem.gem_score,
                    "reasons": gem.reasons,
                    "profit_potential": gem.profit_potential,
                    "market_position": gem.market_position
                }
            })
    
    return {"top_gems": result}

# FEATURE 2: Photo Analyzer Endpoints
@app.post("/api/cars/{car_id}/analyze-photos")
def analyze_car_photos(car_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Analyze car photos with AI vision"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    background_tasks.add_task(photo_analyzer.analyze_and_save, car, db)
    return {"status": "started", "message": "Photo analysis started in background"}

@app.get("/api/cars/{car_id}/photo-insights")
def get_photo_insights(car_id: str, db: Session = Depends(get_database)):
    """Get photo analysis insights for a car"""
    return photo_analyzer.get_photo_insights(car_id, db)

# FEATURE 3: Description Parser Endpoints
@app.post("/api/cars/{car_id}/parse-description")
def parse_car_description(car_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Parse car description with AI"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    background_tasks.add_task(description_parser.parse_and_save, car, db) 
    return {"status": "started", "message": "Description parsing started in background"}

@app.get("/api/cars/{car_id}/parsed-description")
def get_parsed_description(car_id: str, db: Session = Depends(get_database)):
    """Get parsed description data"""
    parsed = db.query(ParsedListing).filter(ParsedListing.car_id == car_id).first()
    if not parsed:
        return {"message": "Description not yet parsed. Use POST /parse-description first."}
    
    return {
        "service_history": parsed.service_history,
        "detected_options": parsed.detected_options,
        "red_flags": parsed.red_flags,
        "positive_signals": parsed.positive_signals,
        "seller_credibility": parsed.seller_credibility,
        "missing_information": parsed.missing_information,
        "parsed_at": parsed.parsed_at.isoformat()
    }

# COMPREHENSIVE CAR ANALYSIS ENDPOINT
@app.get("/api/cars/{car_id}/full-analysis")
def get_full_car_analysis(car_id: str, db: Session = Depends(get_database)):
    """Get comprehensive analysis combining all AI features"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    # Get all analyses
    gem_analysis = db.query(GemScore).filter(GemScore.car_id == car_id).first()
    photo_insights = photo_analyzer.get_photo_insights(car_id, db)
    parsed_desc = db.query(ParsedListing).filter(ParsedListing.car_id == car_id).first()
    claude_analysis = db.query(Analysis).filter(Analysis.car_id == car_id).first()
    
    return {
        "car_info": {
            "id": car.id,
            "title": car.title,
            "price": car.price,
            "year": car.year,
            "mileage": car.mileage,
            "fuel_type": car.fuel_type,
            "description": car.description,
            "images": json.loads(car.images) if car.images else [],
            "seller_type": car.seller_type,
            "department": car.department
        },
        "gem_analysis": {
            "gem_score": gem_analysis.gem_score if gem_analysis else None,
            "reasons": gem_analysis.reasons if gem_analysis else [],
            "profit_potential": gem_analysis.profit_potential if gem_analysis else 0,
            "market_position": gem_analysis.market_position if gem_analysis else "unknown"
        } if gem_analysis else None,
        "photo_analysis": photo_insights if "message" not in photo_insights else None,
        "description_analysis": {
            "service_history": parsed_desc.service_history if parsed_desc else [],
            "detected_options": parsed_desc.detected_options if parsed_desc else [],
            "red_flags": parsed_desc.red_flags if parsed_desc else [],
            "positive_signals": parsed_desc.positive_signals if parsed_desc else [],
            "seller_credibility": parsed_desc.seller_credibility if parsed_desc else None
        } if parsed_desc else None,
        "claude_analysis": json.loads(claude_analysis.analysis_data) if claude_analysis else None
    }

# BATCH ANALYSIS ENDPOINTS
@app.post("/api/analyze-all-active-cars")
def analyze_all_active_cars(background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Trigger analysis of all active cars"""
    def run_all_analyses():
        # Run gem detection
        import asyncio
        asyncio.run(gem_detector.analyze_all_active_cars(db))
        
        # Run description parsing for cars without parsed data
        cars_to_parse = db.query(Car).filter(
            Car.is_active == True,
            ~Car.id.in_(db.query(ParsedListing.car_id))
        ).limit(50).all()
        
        for car in cars_to_parse:
            try:
                description_parser.parse_and_save(car, db)
            except Exception as e:
                print(f"Error parsing car {car.id}: {e}")
    
    background_tasks.add_task(run_all_analyses)
    return {"status": "started", "message": "Batch analysis of all active cars started"}

# FEATURE 4: Negotiation Assistant Endpoints
@app.post("/api/cars/{car_id}/generate-negotiation-strategy")
def generate_negotiation_strategy(car_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Generate negotiation strategy for a car"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    def generate_and_save_strategy():
        strategy = negotiation_assistant.generate_negotiation_strategy(car, db)
        strategy_id = negotiation_assistant.save_strategy(car, strategy, db)
        print(f" Generated negotiation strategy {strategy_id} for car {car_id}")
    
    background_tasks.add_task(generate_and_save_strategy)
    return {"status": "started", "message": "Negotiation strategy generation started"}

@app.get("/api/cars/{car_id}/negotiation-insights")
def get_negotiation_insights(car_id: str, db: Session = Depends(get_database)):
    """Get negotiation insights for a car"""
    return negotiation_assistant.get_negotiation_insights(car_id, db)

@app.post("/api/negotiations/{strategy_id}/record-outcome")
def record_negotiation_outcome(
    strategy_id: str,
    outcome: str,
    final_price: Optional[int] = None,
    approach_used: Optional[str] = None,
    db: Session = Depends(get_database)
):
    """Record negotiation outcome"""
    strategy = db.query(NegotiationStrategy).filter(NegotiationStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    result = negotiation_assistant.record_outcome(
        strategy.car_id, strategy_id, outcome, final_price, approach_used, {}, db
    )
    return result

# FEATURE 5: VIN Decoder & History Endpoints
@app.post("/api/cars/{car_id}/build-vehicle-history")
def build_vehicle_history(car_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Build comprehensive vehicle history from VIN"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    def build_and_save_history():
        try:
            history = vin_decoder.build_vehicle_history(car, db)
            print(f" Built vehicle history for car {car_id}")
        except Exception as e:
            print(f" Error building history for car {car_id}: {e}")
    
    background_tasks.add_task(build_and_save_history)
    return {"status": "started", "message": "VIN analysis and history building started"}

@app.get("/api/cars/{car_id}/vin-insights")
def get_vin_insights(car_id: str, db: Session = Depends(get_database)):
    """Get VIN insights and vehicle history"""
    return vin_decoder.get_vin_insights(car_id, db)

@app.post("/api/vin/decode")
def decode_vin_manual(vin: str):
    """Manually decode a VIN number"""
    if len(vin) != 17:
        raise HTTPException(status_code=400, detail="VIN must be 17 characters")
    
    decoded = vin_decoder.decode_vin(vin)
    recall_status = vin_decoder.check_recall_status(vin, decoded.get("manufacturer", "Unknown"))
    theft_check = vin_decoder.check_theft_status(vin)
    
    return {
        "vin": vin,
        "decoded_info": decoded,
        "recall_status": recall_status,
        "theft_check": theft_check
    }

# FEATURE 6: Market Pulse Predictor Endpoints
@app.post("/api/market/analyze/{make_model}")
def analyze_market_pulse(make_model: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Analyze market pulse for a make/model"""
    def analyze_and_save():
        try:
            pulse = market_predictor.analyze_market_pulse(make_model, db)
            if "error" not in pulse:
                pulse_id = market_predictor.save_market_pulse(make_model, pulse, db)
                print(f" Analyzed market pulse for {make_model}, saved as {pulse_id}")
        except Exception as e:
            print(f" Error analyzing market pulse for {make_model}: {e}")
    
    background_tasks.add_task(analyze_and_save)
    return {"status": "started", "message": f"Market analysis started for {make_model}"}

@app.get("/api/market/insights/{make_model}")
def get_market_insights(make_model: str, db: Session = Depends(get_database)):
    """Get market insights for a make/model"""
    return market_predictor.get_market_insights(make_model, db)

@app.get("/api/market/trending")
def get_trending_models(limit: int = 20, db: Session = Depends(get_database)):
    """Get currently trending car models"""
    return {"trending_models": market_predictor.get_trending_models(db, limit)}

# FEATURE 7: Social Sentiment Analyzer Endpoints
@app.post("/api/sentiment/analyze/{make_model}")
def analyze_social_sentiment(make_model: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Analyze social sentiment for a make/model"""
    def analyze_and_save():
        try:
            sentiment = sentiment_analyzer.analyze_social_sentiment(make_model, db)
            print(f" Analyzed social sentiment for {make_model}")
        except Exception as e:
            print(f" Error analyzing sentiment for {make_model}: {e}")
    
    background_tasks.add_task(analyze_and_save)
    return {"status": "started", "message": f"Sentiment analysis started for {make_model}"}

@app.get("/api/sentiment/insights/{make_model}")
def get_sentiment_insights(make_model: str, db: Session = Depends(get_database)):
    """Get sentiment insights for a make/model"""
    return sentiment_analyzer.get_sentiment_insights(make_model, db)

@app.get("/api/sentiment/top-rated")
def get_top_rated_models(limit: int = 10, db: Session = Depends(get_database)):
    """Get top-rated models by social sentiment"""
    return {"top_rated_models": sentiment_analyzer.get_top_rated_models(db, limit)}

# COMPREHENSIVE AI DASHBOARD ENDPOINT
@app.get("/api/cars/{car_id}/ai-dashboard")
def get_ai_dashboard(car_id: str, db: Session = Depends(get_database)):
    """Get comprehensive AI dashboard for a car"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    # Get all AI analyses
    gem_analysis = db.query(GemScore).filter(GemScore.car_id == car_id).first()
    photo_insights = photo_analyzer.get_photo_insights(car_id, db)
    parsed_desc = db.query(ParsedListing).filter(ParsedListing.car_id == car_id).first()
    negotiation_insights = negotiation_assistant.get_negotiation_insights(car_id, db)
    vin_insights = vin_decoder.get_vin_insights(car_id, db)
    
    # Get market and sentiment data for the model
    make_model = car.title.split()[0:2]  # Approximate make/model extraction
    make_model_str = " ".join(make_model)
    market_insights = market_predictor.get_market_insights(make_model_str, db)
    sentiment_insights = sentiment_analyzer.get_sentiment_insights(make_model_str, db)
    
    return {
        "car_info": {
            "id": car.id,
            "title": car.title,
            "price": car.price,
            "year": car.year,
            "mileage": car.mileage,
            "fuel_type": car.fuel_type,
            "seller_type": car.seller_type,
            "department": car.department,
            "url": car.url
        },
        "ai_analyses": {
            "gem_analysis": {
                "gem_score": gem_analysis.gem_score if gem_analysis else None,
                "reasons": gem_analysis.reasons if gem_analysis else [],
                "profit_potential": gem_analysis.profit_potential if gem_analysis else 0,
                "market_position": gem_analysis.market_position if gem_analysis else "unknown"
            } if gem_analysis else None,
            "photo_analysis": photo_insights if "message" not in photo_insights else None,
            "description_analysis": {
                "service_history": parsed_desc.service_history if parsed_desc else [],
                "detected_options": parsed_desc.detected_options if parsed_desc else [],
                "red_flags": parsed_desc.red_flags if parsed_desc else [],
                "seller_credibility": parsed_desc.seller_credibility if parsed_desc else None
            } if parsed_desc else None,
            "negotiation_strategy": negotiation_insights if "message" not in negotiation_insights else None,
            "vin_history": vin_insights if "message" not in vin_insights else None
        },
        "market_context": {
            "market_pulse": market_insights if "message" not in market_insights else None,
            "social_sentiment": sentiment_insights if "message" not in sentiment_insights else None
        },
        "ai_summary": self._generate_ai_summary(car, gem_analysis, parsed_desc, market_insights, sentiment_insights)
    }

def _generate_ai_summary(car, gem_analysis, parsed_desc, market_insights, sentiment_insights):
    """Generate AI summary for the dashboard"""
    summary = {
        "overall_recommendation": "neutral",
        "key_insights": [],
        "risk_factors": [],
        "opportunities": []
    }
    
    # Gem analysis insights
    if gem_analysis:
        if gem_analysis.gem_score > 75:
            summary["key_insights"].append(f" Ppite dtecte - Score: {gem_analysis.gem_score}/100")
            summary["overall_recommendation"] = "buy"
        elif gem_analysis.gem_score < 40:
            summary["risk_factors"].append("Prix potentiellement lev pour le march")
    
    # Description analysis insights
    if parsed_desc:
        if parsed_desc.seller_credibility and parsed_desc.seller_credibility > 80:
            summary["key_insights"].append(" Vendeur crdible avec description dtaille")
        elif parsed_desc.seller_credibility and parsed_desc.seller_credibility < 50:
            summary["risk_factors"].append(" Description peu crdible ou incomplte")
        
        if parsed_desc.red_flags and len(parsed_desc.red_flags) > 2:
            summary["risk_factors"].append(f" {len(parsed_desc.red_flags)} signaux d'alarme dtects")
    
    # Market insights
    if market_insights and "message" not in market_insights:
        if market_insights.get("current_trend") == "falling":
            summary["opportunities"].append(" March en baisse - Opportunit d'achat")
        elif market_insights.get("current_trend") == "rising":
            summary["risk_factors"].append(" March en hausse - Prix pourraient augmenter")
    
    # Sentiment insights
    if sentiment_insights and "message" not in sentiment_insights:
        if sentiment_insights.get("overall_sentiment", 0) > 0.3:
            summary["key_insights"].append(" Modle trs apprci par les propritaires")
        elif sentiment_insights.get("overall_sentiment", 0) < -0.2:
            summary["risk_factors"].append(" Modle avec des avis mitigs")
    
    # Overall recommendation logic
    if len(summary["risk_factors"]) > len(summary["key_insights"]) + len(summary["opportunities"]):
        summary["overall_recommendation"] = "avoid"
    elif len(summary["key_insights"]) + len(summary["opportunities"]) > len(summary["risk_factors"]):
        summary["overall_recommendation"] = "consider" if summary["overall_recommendation"] != "buy" else "buy"
    
    return summary

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("Starting Automotive Assistant API...")
    create_all_tables()  # Create AI feature tables
    
    # Run scraper immediately on startup
    threading.Thread(target=run_scraper_background, daemon=True).start()
    
    # Start automatic scraper in background
    threading.Thread(target=automatic_scraper, daemon=True).start()
    
    print("API started with all 10 AI features enabled")

# FEATURE 8: Smart Comparison Engine Endpoints
@app.post("/api/cars/{car_id}/generate-comparison")
def generate_car_comparison(car_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Generate smart comparison report for a car"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    def generate_and_save_comparison():
        try:
            comparison = comparison_engine.generate_comparison_report(car, db)
            if "error" not in comparison:
                comparison_id = comparison_engine.save_comparison(car, comparison, db)
                print(f" Generated comparison {comparison_id} for car {car_id}")
        except Exception as e:
            print(f" Error generating comparison for car {car_id}: {e}")
    
    background_tasks.add_task(generate_and_save_comparison)
    return {"status": "started", "message": "Smart comparison generation started"}

@app.get("/api/cars/{car_id}/comparison-insights")
def get_comparison_insights(car_id: str, db: Session = Depends(get_database)):
    """Get smart comparison insights for a car"""
    return comparison_engine.get_comparison_insights(car_id, db)

# FEATURE 9: Maintenance Cost Prophet Endpoints
@app.post("/api/cars/{car_id}/predict-maintenance")
def predict_maintenance_costs(car_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Predict maintenance costs for a car"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    def predict_and_save():
        try:
            prediction = maintenance_prophet.predict_maintenance_costs(car, db)
            prediction_id = maintenance_prophet.save_maintenance_prediction(car, prediction, db)
            print(f" Generated maintenance prediction {prediction_id} for car {car_id}")
        except Exception as e:
            print(f" Error predicting maintenance for car {car_id}: {e}")
    
    background_tasks.add_task(predict_and_save)
    return {"status": "started", "message": "Maintenance cost prediction started"}

@app.get("/api/cars/{car_id}/maintenance-insights")
def get_maintenance_insights(car_id: str, db: Session = Depends(get_database)):
    """Get maintenance cost insights for a car"""
    return maintenance_prophet.get_maintenance_insights(car_id, db)

@app.get("/api/maintenance/brand-comparison")
def get_maintenance_brand_comparison(db: Session = Depends(get_database)):
    """Get maintenance cost comparison by brand"""
    return maintenance_prophet.get_cost_comparison_by_brand(db)

# FEATURE 10: Investment Grade Scorer Endpoints
@app.post("/api/cars/{car_id}/calculate-investment-grade")
def calculate_investment_grade(car_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Calculate investment grade for a car"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    def calculate_and_save():
        try:
            investment_analysis = investment_scorer.calculate_investment_grade(car, db)
            score_id = investment_scorer.save_investment_score(car, investment_analysis, db)
            print(f" Generated investment score {score_id} for car {car_id}")
        except Exception as e:
            print(f" Error calculating investment grade for car {car_id}: {e}")
    
    background_tasks.add_task(calculate_and_save)
    return {"status": "started", "message": "Investment grade calculation started"}

@app.get("/api/cars/{car_id}/investment-insights")
def get_investment_insights(car_id: str, db: Session = Depends(get_database)):
    """Get investment insights for a car"""
    return investment_scorer.get_investment_insights(car_id, db)

@app.get("/api/investment/top-opportunities")
def get_top_investment_opportunities(limit: int = 10, db: Session = Depends(get_database)):
    """Get top investment opportunities"""
    return {"top_opportunities": investment_scorer.get_top_investment_opportunities(db, limit)}

# COMPREHENSIVE AI ANALYSIS TRIGGER
@app.post("/api/cars/{car_id}/full-ai-analysis")
def trigger_full_ai_analysis(car_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_database)):
    """Trigger all AI analyses for a car"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    def run_full_analysis():
        """Run all AI analyses in sequence"""
        try:
            print(f" Starting full AI analysis for car {car_id}")
            
            # 1. Gem Detection
            gem_analysis = gem_detector.calculate_gem_score(car, db)
            gem_score = GemScore(
                car_id=car_id,
                gem_score=gem_analysis["gem_score"],
                reasons=gem_analysis["reasons"],
                profit_potential=gem_analysis["profit_potential"],
                risk_factors=gem_analysis["risk_factors"],
                market_position=gem_analysis["market_position"],
                confidence_level=gem_analysis["confidence_level"]
            )
            db.add(gem_score)
            
            # 2. Description Parsing
            description_parser.parse_and_save(car, db)
            
            # 3. Photo Analysis (if images available)
            if car.images:
                photo_analyzer.analyze_and_save(car, db)
            
            # 4. Negotiation Strategy
            strategy = negotiation_assistant.generate_negotiation_strategy(car, db)
            negotiation_assistant.save_strategy(car, strategy, db)
            
            # 5. VIN Analysis (if VIN found)
            vin_decoder.build_vehicle_history(car, db)
            
            # 6. Market Analysis
            make_model = " ".join(car.title.split()[:2])
            market_pulse = market_predictor.analyze_market_pulse(make_model, db)
            if "error" not in market_pulse:
                market_predictor.save_market_pulse(make_model, market_pulse, db)
            
            # 7. Sentiment Analysis
            sentiment_analyzer.analyze_social_sentiment(make_model, db)
            
            # 8. Smart Comparison
            comparison = comparison_engine.generate_comparison_report(car, db)
            if "error" not in comparison:
                comparison_engine.save_comparison(car, comparison, db)
            
            # 9. Maintenance Prediction
            maintenance_prediction = maintenance_prophet.predict_maintenance_costs(car, db)
            maintenance_prophet.save_maintenance_prediction(car, maintenance_prediction, db)
            
            # 10. Investment Score
            investment_analysis = investment_scorer.calculate_investment_grade(car, db)
            investment_scorer.save_investment_score(car, investment_analysis, db)
            
            db.commit()
            print(f" Completed full AI analysis for car {car_id}")
            
        except Exception as e:
            print(f" Error in full AI analysis for car {car_id}: {e}")
            db.rollback()
    
    background_tasks.add_task(run_full_analysis)
    return {
        "status": "started", 
        "message": "Full AI analysis started - all 10 features will be processed",
        "estimated_time": "2-5 minutes"
    }

# SCRAPER ENDPOINTS
@app.get("/api/scrape/status")
def get_scraper_status(db: Session = Depends(get_database)):
    """Get scraper status and car count"""
    total_cars = db.query(Car).count()
    active_cars = db.query(Car).filter(Car.is_active == True).count()
    recent_cars = db.query(Car).filter(
        Car.first_seen > datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    return {
        "total_cars": total_cars,
        "active_cars": active_cars,
        "recent_cars_24h": recent_cars,
        "last_scrape": "auto-running",
        "status": "healthy" if total_cars > 0 else "needs_data"
    }

@app.post("/api/scrape/run")
def run_scraper_manual(background_tasks: BackgroundTasks):
    """Manually trigger scraper run"""
    def run_scraper_background():
        """Run scraper in background with fallback strategy"""
        try:
            logger.info(" Attempting Scrapfly-enhanced scraping...")
            scrapfly_scraper = ScrapflyLeboncoinScraper(department="69", max_cars=100)
            scrapfly_scraper.run()
            logger.info(" Scrapfly scraper completed successfully")
            return {"status": "success", "message": "Scrapfly scraper completed successfully"}
        except Exception as e:
            logger.warning(f"Scrapfly scraper failed: {e}")
            logger.info(" Falling back to original scraper...")
            try:
                # Fallback to original scraper
                scraper = LeBonCoinScraper(department="69", max_cars=50)
                cars = scraper.scrape_cars()
                if cars:
                    scraper.save_to_database(cars)
                    logger.info(f" Fallback scraper saved {len(cars)} cars")
                else:
                    logger.warning(" Fallback scraper found no cars - creating sample data")
                    from sample_data import create_sample_data
                    create_sample_data()
                return {"status": "success", "message": "Fallback scraper completed"}
            except Exception as fallback_error:
                logger.error(f" Both scrapers failed: {fallback_error}")
                # Ensure we have sample data
                try:
                    from sample_data import create_sample_data
                    create_sample_data()
                    logger.info(" Sample data created as final fallback")
                except Exception as sample_error:
                    logger.error(f" Sample data creation failed: {sample_error}")
                return {"status": "error", "message": "All scrapers failed, sample data attempted"}
    
    background_tasks.add_task(run_scraper_background)
    return {"status": "started", "message": "Scraper started in background"}

@app.get("/api/scrape/scrapfly")
def test_scrapfly_scraper(background_tasks: BackgroundTasks):
    """Test Scrapfly scraper specifically"""
    def run_scrapfly_test():
        try:
            logger.info(" Testing Scrapfly scraper...")
            scrapfly_scraper = ScrapflyLeboncoinScraper(department="69", max_cars=10)
            scrapfly_scraper.run()
            logger.info(" Scrapfly test completed")
        except Exception as e:
            logger.error(f" Scrapfly test failed: {e}")
    
    background_tasks.add_task(run_scrapfly_test)
    return {"status": "started", "message": "Scrapfly test started"}

# AUTO-SCRAPER BACKGROUND TASK
def start_background_scraper():
    """Start background scraper that runs every 30 minutes"""
    def scraper_loop():
        while True:
            try:
                logger.info(" Auto-scraper starting...")
                # Try Scrapfly first
                try:
                    scrapfly_scraper = ScrapflyLeboncoinScraper(department="69", max_cars=50)
                    scrapfly_scraper.run()
                    logger.info(" Auto-scraper (Scrapfly) completed")
                except Exception as e:
                    logger.warning(f"Auto-scraper Scrapfly failed: {e}, trying fallback...")
                    # Fallback to original
                    scraper = LeBonCoinScraper(department="69", max_cars=30)
                    cars = scraper.scrape_cars()
                    if cars:
                        scraper.save_to_database(cars)
                        logger.info(f" Auto-scraper (fallback) saved {len(cars)} cars")
                
                # Wait 30 minutes before next run
                time.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f" Auto-scraper error: {e}")
                time.sleep(300)  # Wait 5 minutes on error before retry
    
    # Start scraper thread
    scraper_thread = threading.Thread(target=scraper_loop, daemon=True)
    scraper_thread.start()
    logger.info(" Background auto-scraper started")

# Start background scraper on app startup
start_background_scraper()

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "features": [
            "scraping", "gem_detection", "photo_analysis", "description_parsing",
            "negotiation_assistant", "vin_decoder", "market_predictor", "sentiment_analyzer",
            "smart_comparison", "maintenance_prophet", "investment_scorer"
        ],
        "ai_features_count": 10,
        "version": "3.0.0 - Complete AI Suite"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)