"""
Enhanced LeBonCoin Scraper using Scrapfly methodology
Adapted from: https://github.com/scrapfly/scrapfly-scrapers/tree/main/leboncoin-scraper
"""

import requests
import json
import re
import time
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, Car
import logging
from typing import Dict, List, Optional
import asyncio
import concurrent.futures
from urllib.parse import urlencode, urlparse, parse_qs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapflyLeboncoinScraper:
    def __init__(self, department="69", max_cars=100):
        self.department = department
        self.max_cars = max_cars
        self.base_url = "https://www.leboncoin.fr"
        self.session = requests.Session()
        
        # Enhanced headers based on Scrapfly approach
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
    def build_search_url(self, page: int = 1) -> str:
        """Build LeBonCoin search URL for cars with filters"""
        
        # Base search parameters for cars
        params = {
            'category': '2',  # Cars category
            'locations': f'd_{self.department}',  # Department filter
            'page': str(page),
            'shippable': '1',
            'sort': 'time',  # Sort by newest
            'order': 'desc'
        }
        
        # Build the search URL
        search_url = f"{self.base_url}/voitures/occasions/offres?"
        search_url += urlencode(params)
        
        return search_url
    
    def parse_nextjs_data(self, html_content: str) -> Optional[Dict]:
        """Extract data from NextJS __NEXT_DATA__ script tag"""
        try:
            # Find the __NEXT_DATA__ script tag
            next_data_pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
            match = re.search(next_data_pattern, html_content, re.DOTALL)
            
            if not match:
                logger.warning("Could not find __NEXT_DATA__ script tag")
                return None
            
            # Parse the JSON data
            json_data = json.loads(match.group(1))
            
            # Navigate to the search data
            try:
                search_data = json_data["props"]["pageProps"]["searchData"]
                return search_data
            except KeyError as e:
                logger.warning(f"Could not find search data in NextJS data: {e}")
                # Try alternative paths
                try:
                    return json_data["props"]["pageProps"]["ads"]
                except KeyError:
                    logger.warning("Could not find ads data either")
                    return json_data["props"]["pageProps"]  # Return whatever we can find
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse NextJS JSON data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing NextJS data: {e}")
            return None
    
    def extract_ads_from_search_data(self, search_data: Dict) -> List[Dict]:
        """Extract ads from search data"""
        ads = []
        
        try:
            # Try different possible locations for ads data
            ads_data = None
            
            if "ads" in search_data:
                ads_data = search_data["ads"]
            elif "results" in search_data:
                ads_data = search_data["results"]
            elif "items" in search_data:
                ads_data = search_data["items"]
            else:
                # If it's a list itself
                if isinstance(search_data, list):
                    ads_data = search_data
                else:
                    logger.warning(f"Could not find ads in search data. Keys: {search_data.keys()}")
                    return ads
            
            if not ads_data:
                logger.warning("No ads data found")
                return ads
            
            logger.info(f"Found {len(ads_data)} potential ads")
            
            for ad_data in ads_data:
                try:
                    car_data = self.extract_car_data_from_ad(ad_data)
                    if car_data:
                        ads.append(car_data)
                except Exception as e:
                    logger.warning(f"Failed to extract car data from ad: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting ads from search data: {e}")
            
        return ads
    
    def extract_car_data_from_ad(self, ad: Dict) -> Optional[Dict]:
        """Extract car data from a single ad"""
        try:
            # Handle different possible data structures
            ad_id = str(ad.get("list_id") or ad.get("id") or ad.get("ad_id") or uuid.uuid4())
            title = ad.get("subject") or ad.get("title") or ""
            
            # Extract price
            price = None
            if "price" in ad:
                price_data = ad["price"]
                if isinstance(price_data, list) and len(price_data) > 0:
                    price = price_data[0]
                elif isinstance(price_data, (int, float)):
                    price = int(price_data)
                elif isinstance(price_data, str):
                    # Try to extract number from string
                    price_match = re.search(r'\d+', price_data.replace(' ', ''))
                    if price_match:
                        price = int(price_match.group())
            
            # Extract attributes
            attributes = {}
            if "attributes" in ad:
                for attr in ad["attributes"]:
                    if isinstance(attr, dict) and "key" in attr and "value" in attr:
                        attributes[attr["key"]] = attr["value"]
            elif "specs" in ad:
                attributes = ad["specs"]
            elif "properties" in ad:
                attributes = ad["properties"]
            
            # Extract specific car attributes
            year = None
            mileage = None
            fuel_type = ""
            
            # Try different attribute names
            for year_key in ["regdate", "year", "model_year", "registration_year"]:
                if year_key in attributes:
                    try:
                        year = int(attributes[year_key])
                        break
                    except (ValueError, TypeError):
                        continue
            
            for mileage_key in ["mileage", "kilometers", "km"]:
                if mileage_key in attributes:
                    try:
                        mileage = int(attributes[mileage_key])
                        break
                    except (ValueError, TypeError):
                        continue
            
            for fuel_key in ["fuel", "fuel_type", "energy", "carburant"]:
                if fuel_key in attributes:
                    fuel_type = str(attributes[fuel_key])
                    break
            
            # Extract images
            images = []
            if "images" in ad:
                img_data = ad["images"]
                if isinstance(img_data, dict):
                    # Try different image size keys
                    for size_key in ["urls_large", "urls_medium", "urls", "large", "medium"]:
                        if size_key in img_data:
                            images = img_data[size_key]
                            break
                elif isinstance(img_data, list):
                    images = img_data
            elif "photos" in ad:
                images = ad["photos"]
            
            # Extract description
            description = ad.get("body") or ad.get("description") or ""
            
            # Extract URL
            url = ad.get("url") or f"{self.base_url}/ad/{ad_id}"
            
            # Extract seller info
            seller_info = ad.get("owner", {}) or ad.get("seller", {})
            seller_type = seller_info.get("type", "particulier")
            
            # Extract location
            location = ad.get("location", {})
            department = self.department  # Use configured department as fallback
            if isinstance(location, dict):
                department = location.get("department", department)
            
            car_data = {
                "id": ad_id,
                "title": title,
                "price": price,
                "year": year,
                "mileage": mileage,
                "fuel_type": fuel_type,
                "description": description,
                "images": json.dumps(images),
                "url": url,
                "seller_type": seller_type,
                "department": department,
                "first_seen": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "is_active": True
            }
            
            # Validate that we have minimum required data
            if not title or not price:
                logger.warning(f"Skipping ad {ad_id} - missing title or price")
                return None
                
            return car_data
            
        except Exception as e:
            logger.error(f"Error extracting car data from ad: {e}")
            return None
    
    def scrape_search_page(self, page: int = 1) -> List[Dict]:
        """Scrape a single search page"""
        url = self.build_search_url(page)
        logger.info(f"Scraping page {page}: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse NextJS data
            search_data = self.parse_nextjs_data(response.text)
            if not search_data:
                logger.warning(f"No search data found on page {page}")
                return []
            
            # Extract ads
            ads = self.extract_ads_from_search_data(search_data)
            logger.info(f"Extracted {len(ads)} cars from page {page}")
            
            return ads
            
        except requests.RequestException as e:
            logger.error(f"HTTP error scraping page {page}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error scraping page {page}: {e}")
            return []
    
    def search_cars(self) -> List[Dict]:
        """Search for cars across multiple pages"""
        all_cars = []
        page = 1
        max_pages = 10  # Limit to prevent infinite loops
        consecutive_empty_pages = 0
        
        while len(all_cars) < self.max_cars and page <= max_pages:
            logger.info(f"Scraping page {page} (found {len(all_cars)} cars so far)")
            
            page_cars = self.scrape_search_page(page)
            
            if not page_cars:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 3:
                    logger.info("Found 3 consecutive empty pages, stopping")
                    break
            else:
                consecutive_empty_pages = 0
                all_cars.extend(page_cars)
            
            page += 1
            
            # Rate limiting
            time.sleep(2)
            
            # Stop if we have enough cars
            if len(all_cars) >= self.max_cars:
                all_cars = all_cars[:self.max_cars]
                break
        
        logger.info(f"Total cars found: {len(all_cars)}")
        return all_cars
    
    def save_to_database(self, cars: List[Dict]):
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
            logger.info(f"✅ Saved {saved_count} new cars, updated {updated_count} existing cars")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            db.rollback()
        finally:
            db.close()
    
    def mark_inactive_cars(self):
        """Mark cars as inactive if not seen recently"""
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            inactive_count = db.query(Car).filter(
                Car.last_seen < cutoff_time,
                Car.is_active == True
            ).update({"is_active": False})
            
            db.commit()
            logger.info(f"Marked {inactive_count} cars as inactive")
            
        except Exception as e:
            logger.error(f"Error marking inactive cars: {e}")
            db.rollback()
        finally:
            db.close()
    
    def run(self):
        """Run the enhanced scraper"""
        logger.info(f"🚗 Starting Scrapfly-enhanced scraper for department {self.department}")
        
        try:
            cars = self.search_cars()
            
            if cars:
                self.save_to_database(cars)
                logger.info(f"✅ Successfully scraped and saved {len(cars)} cars")
            else:
                logger.warning("⚠️ No cars found - falling back to sample data")
                self.create_sample_data_if_empty()
            
            # Mark inactive cars
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
                from scraper import create_sample_data
                create_sample_data()
                logger.info("✅ Sample data created")
            else:
                logger.info(f"📊 Database has {car_count} cars")
        except Exception as e:
            logger.error(f"Error checking/creating sample data: {e}")
        finally:
            db.close()

def create_test_data():
    """Create test data to verify scraper integration"""
    logger.info("Creating test data for scraper validation...")
    
    test_cars = [
        {
            "id": str(uuid.uuid4()),
            "title": "Renault Clio V 1.0 TCe 100 Zen",
            "price": 16500,
            "year": 2020,
            "mileage": 35000,
            "fuel_type": "essence",
            "description": "Clio V en parfait état, première main, carnet d'entretien suivi. Climatisation, Bluetooth, régulateur de vitesse. Contrôle technique OK.",
            "images": json.dumps([
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/test1.jpg",
                "https://images.leboncoin.fr/api/v1/lbcpb1/images/test2.jpg"
            ]),
            "url": "https://www.leboncoin.fr/test1",
            "seller_type": "particulier",
            "department": "69",
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "is_active": True
        }
    ]
    
    db = SessionLocal()
    try:
        for car_data in test_cars:
            existing = db.query(Car).filter(Car.id == car_data["id"]).first()
            if not existing:
                new_car = Car(**car_data)
                db.add(new_car)
        
        db.commit()
        logger.info("✅ Test data created successfully")
        
    except Exception as e:
        logger.error(f"Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    scraper = ScrapflyLeboncoinScraper(department="69", max_cars=50)
    scraper.run()