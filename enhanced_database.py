from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, Float
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
    reasons = Column(Text)  # JSON as text
    profit_potential = Column(Integer)
    risk_factors = Column(Text)  # JSON as text
    market_position = Column(String)  # "undervalued", "fair", "overpriced"
    confidence_level = Column(Float)  # 0.0-1.0
    created_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 2: AI Photo Analyzer
class PhotoAnalysis(Base):
    __tablename__ = "photo_analysis"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    photo_url = Column(String, nullable=False)
    analysis_result = Column(Text)  # JSON as text
    damage_detected = Column(Text)  # JSON as text
    features_detected = Column(Text)  # JSON as text
    condition_score = Column(Float)  # 0.0-10.0
    honesty_score = Column(Float)  # How honest the photos are
    analyzed_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 3: Intelligent Description Parser
class ParsedListing(Base):
    __tablename__ = "parsed_listings"
    
    car_id = Column(String, primary_key=True)
    raw_description = Column(Text)
    parsed_data = Column(Text)  # JSON as text
    service_history = Column(Text)  # JSON as text
    detected_options = Column(Text)  # JSON as text
    red_flags = Column(Text)  # JSON as text
    positive_signals = Column(Text)  # JSON as text
    seller_credibility = Column(Float)  # 0-100
    missing_information = Column(Text)  # JSON as text
    parser_version = Column(String)
    parsed_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 4: Negotiation Assistant
class NegotiationStrategy(Base):
    __tablename__ = "negotiation_strategies"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    strategy_data = Column(Text)  # JSON as text
    seller_psychology = Column(Text)  # JSON as text
    price_points = Column(Text)  # JSON as text
    scripts = Column(Text)  # JSON as text
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
    lessons_learned = Column(Text)  # JSON as text
    created_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 5: VIN Decoder & History
class VinData(Base):
    __tablename__ = "vin_data"
    
    vin = Column(String, primary_key=True)
    decoded_data = Column(Text)  # JSON as text
    equipment_list = Column(Text)  # JSON as text
    recall_status = Column(Text)  # JSON as text
    theft_check = Column(Text)  # JSON as text
    import_history = Column(Text)  # JSON as text
    verified_at = Column(DateTime, default=datetime.utcnow)

class VehicleHistory(Base):
    __tablename__ = "vehicle_history"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    vin = Column(String)
    history_timeline = Column(Text)  # JSON as text
    ownership_count = Column(Integer)
    accident_history = Column(Text)  # JSON as text
    service_records = Column(Text)  # JSON as text
    authenticity_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 6: Market Pulse Predictor
class MarketPulse(Base):
    __tablename__ = "market_pulse"
    
    id = Column(String, primary_key=True)
    make_model = Column(String, nullable=False)
    current_trend = Column(String)  # "rising", "stable", "falling"
    price_prediction = Column(Text)  # JSON as text  # 3, 6, 12 month forecasts
    seasonal_factors = Column(Text)  # JSON as text
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
    reputation_data = Column(Text)  # JSON as text
    common_issues = Column(Text)  # JSON as text
    owner_satisfaction = Column(Float)
    reliability_score = Column(Float)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 8: Smart Comparison Engine
class CarComparison(Base):
    __tablename__ = "car_comparisons"
    
    id = Column(String, primary_key=True)
    base_car_id = Column(String, nullable=False)
    similar_cars = Column(Text)  # JSON as text  # Array of similar car IDs with similarity scores
    comparison_matrix = Column(Text)  # JSON as text
    value_ranking = Column(Text)  # JSON as text
    recommendation_reason = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

# FEATURE 9: Maintenance Cost Prophet
class MaintenancePrediction(Base):
    __tablename__ = "maintenance_predictions"
    
    id = Column(String, primary_key=True)
    car_id = Column(String, nullable=False)
    make_model = Column(String, nullable=False)
    predicted_costs = Column(Text)  # JSON as text  # 1-5 year projections
    maintenance_schedule = Column(Text)  # JSON as text
    common_repairs = Column(Text)  # JSON as text
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
    historical_performance = Column(Text)  # JSON as text
    risk_assessment = Column(Text)  # JSON as text
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