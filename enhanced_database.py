from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cars.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Original tables
class Car(Base):
    __tablename__ = "cars"
    
    id = Column(String, primary_key=True, index=True)
    source = Column(String, default="leboncoin")
    title = Column(String, nullable=False)
    price = Column(Integer)
    year = Column(Integer)
    mileage = Column(Integer)
    fuel_type = Column(String)
    description = Column(Text)
    images = Column(Text)  # JSON array as string
    url = Column(String, unique=True)
    seller_type = Column(String)
    department = Column(String)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(String, primary_key=True, index=True)
    car_id = Column(String, nullable=False)
    analysis_data = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 1: Hidden Gem Detector
class GemScore(Base):
    __tablename__ = "gem_scores"
    
    car_id = Column(String, primary_key=True)
    gem_score = Column(Integer)  # 0-100
    reasons = Column(JSON)
    profit_potential = Column(Integer)
    risk_factors = Column(JSON)
    market_position = Column(String)  # "undervalued", "fair", "overpriced"
    confidence_level = Column(Float)  # 0.0-1.0
    created_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 2: AI Photo Analyzer
class PhotoAnalysis(Base):
    __tablename__ = "photo_analysis"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    photo_url = Column(String, nullable=False)
    analysis_result = Column(JSON)
    damage_detected = Column(JSON)
    features_detected = Column(JSON)
    condition_score = Column(Float)  # 0.0-10.0
    honesty_score = Column(Float)  # How honest the photos are
    analyzed_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 3: Intelligent Description Parser
class ParsedListing(Base):
    __tablename__ = "parsed_listings"
    
    car_id = Column(String, primary_key=True)
    raw_description = Column(Text)
    parsed_data = Column(JSON)
    service_history = Column(JSON)
    detected_options = Column(JSON)
    red_flags = Column(JSON)
    positive_signals = Column(JSON)
    seller_credibility = Column(Float)  # 0-100
    missing_information = Column(JSON)
    parser_version = Column(String)
    parsed_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 4: Negotiation Assistant
class NegotiationStrategy(Base):
    __tablename__ = "negotiation_strategies"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    strategy_data = Column(JSON)
    seller_psychology = Column(JSON)
    price_points = Column(JSON)
    scripts = Column(JSON)
    success_probability = Column(Float)
    cultural_approach = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class NegotiationOutcome(Base):
    __tablename__ = "negotiation_outcomes"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    strategy_id = Column(String)
    outcome = Column(String)  # "success", "failed", "pending"
    final_price = Column(Integer)
    discount_achieved = Column(Integer)
    approach_used = Column(String)
    lessons_learned = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 5: VIN Decoder & History
class VinData(Base):
    __tablename__ = "vin_data"
    
    vin = Column(String, primary_key=True)
    decoded_data = Column(JSON)
    equipment_list = Column(JSON)
    recall_status = Column(JSON)
    theft_check = Column(JSON)
    import_history = Column(JSON)
    verified_at = Column(DateTime, default=datetime.utcnow)

class VehicleHistory(Base):
    __tablename__ = "vehicle_history"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    vin = Column(String)
    history_timeline = Column(JSON)
    ownership_count = Column(Integer)
    accident_history = Column(JSON)
    service_records = Column(JSON)
    authenticity_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 6: Market Pulse Predictor
class MarketPulse(Base):
    __tablename__ = "market_pulse"
    
    id = Column(String, primary_key=True)
    make_model = Column(String, nullable=False)
    current_trend = Column(String)  # "rising", "stable", "falling"
    price_prediction = Column(JSON)  # 3, 6, 12 month forecasts
    seasonal_factors = Column(JSON)
    market_saturation = Column(Float)
    demand_score = Column(Integer)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)

# FEATURE 7: Social Sentiment Analyzer
class SocialSentiment(Base):
    __tablename__ = "social_sentiment"
    
    id = Column(String, primary_key=True)
    make_model = Column(String, nullable=False)
    platform = Column(String)  # "forums", "social", "reviews"
    sentiment_score = Column(Float)  # -1.0 to 1.0
    reputation_data = Column(JSON)
    common_issues = Column(JSON)
    owner_satisfaction = Column(Float)
    reliability_score = Column(Float)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 8: Smart Comparison Engine
class CarComparison(Base):
    __tablename__ = "car_comparisons"
    
    id = Column(String, primary_key=True)
    base_car_id = Column(String, nullable=False)
    similar_cars = Column(JSON)  # Array of similar car IDs with similarity scores
    comparison_matrix = Column(JSON)
    value_ranking = Column(JSON)
    recommendation_reason = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 9: Maintenance Cost Prophet
class MaintenancePrediction(Base):
    __tablename__ = "maintenance_predictions"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    make_model = Column(String, nullable=False)
    predicted_costs = Column(JSON)  # 1-5 year projections
    maintenance_schedule = Column(JSON)
    common_repairs = Column(JSON)
    parts_availability = Column(String)
    total_5year_cost = Column(Integer)
    reliability_grade = Column(String)  # A, B, C, D, F
    calculated_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 10: Investment Grade Scorer
class InvestmentScore(Base):
    __tablename__ = "investment_scores"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    investment_grade = Column(String)  # "A+", "A", "B+", "B", "C+", "C", "D"
    appreciation_potential = Column(Float)  # Expected % appreciation
    liquidity_score = Column(Integer)  # How easy to sell
    rarity_factor = Column(Float)
    collector_interest = Column(Integer)
    historical_performance = Column(JSON)
    risk_assessment = Column(JSON)
    hold_recommendation = Column(String)  # "short", "medium", "long"
    calculated_at = Column(DateTime, default=datetime.utcnow)

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_all_tables():
    """Create all tables including new AI features"""
    Base.metadata.create_all(bind=engine)
    print("✅ All AI feature tables created successfully!")

if __name__ == "__main__":
    create_all_tables()