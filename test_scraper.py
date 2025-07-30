#!/usr/bin/env python3
import requests
import json
from database import create_tables

# Test the LeBonCoin API
def test_leboncoin_api():
    print("🔍 Testing LeBonCoin API...")
    
    url = "https://api.leboncoin.fr/finder/classified"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Origin': 'https://www.leboncoin.fr',
        'Referer': 'https://www.leboncoin.fr/'
    }
    
    payload = {
        "limit": 5,
        "filters": {
            "category": {"id": "2"},
            "enums": {
                "ad_type": ["offer"]
            },
            "location": {
                "departments": ["69"]
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            ads = data.get("ads", [])
            print(f"✅ Found {len(ads)} cars!")
            
            if ads:
                print(f"First car: {ads[0].get('subject', 'No title')}")
                return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return False

# Test database connection
def test_database():
    print("🗄️  Testing database...")
    try:
        create_tables()
        print("✅ Database connection OK!")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    print("🚗 Automotive Assistant - Connection Test")
    print("=" * 50)
    
    db_ok = test_database()
    api_ok = test_leboncoin_api()
    
    if db_ok and api_ok:
        print("\n✅ All systems ready! Run 'python scraper.py' to get data.")
    else:
        print("\n❌ Issues detected. Check the errors above.")