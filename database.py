from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cars.db")

# Handle PostgreSQL URL format for production
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)