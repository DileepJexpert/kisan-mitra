"""
Agmarknet Mandi Price Scraper
Scrapes daily commodity prices from agmarknet.gov.in
Falls back to mock data generator for development/testing.
"""

import os
import random
import math
from datetime import datetime, date, timedelta
from typing import Optional

import psycopg2
import psycopg2.extras
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql://admin:password@localhost:5432/kisanmitra")

# Commodities and their base prices (Rs. per quintal)
COMMODITIES = {
    "Tomato": {"base_price": 2000, "seasonal_amplitude": 1500, "peak_month": 5},
    "Onion": {"base_price": 1800, "seasonal_amplitude": 1200, "peak_month": 11},
    "Potato": {"base_price": 1200, "seasonal_amplitude": 600, "peak_month": 3},
    "Wheat": {"base_price": 2200, "seasonal_amplitude": 400, "peak_month": 4},
    "Rice (Paddy)": {"base_price": 2000, "seasonal_amplitude": 500, "peak_month": 10},
    "Soybean": {"base_price": 4500, "seasonal_amplitude": 1000, "peak_month": 11},
    "Mustard": {"base_price": 5000, "seasonal_amplitude": 800, "peak_month": 3},
    "Chana (Gram)": {"base_price": 4800, "seasonal_amplitude": 700, "peak_month": 4},
    "Moong": {"base_price": 7000, "seasonal_amplitude": 1500, "peak_month": 10},
    "Maize": {"base_price": 1800, "seasonal_amplitude": 500, "peak_month": 9},
}

# Markets with state and district info
MARKETS = [
    {"market": "Kanpur", "state": "Uttar Pradesh", "district": "Kanpur Nagar"},
    {"market": "Lucknow", "state": "Uttar Pradesh", "district": "Lucknow"},
    {"market": "Varanasi", "state": "Uttar Pradesh", "district": "Varanasi"},
    {"market": "Agra", "state": "Uttar Pradesh", "district": "Agra"},
    {"market": "Prayagraj", "state": "Uttar Pradesh", "district": "Prayagraj"},
    {"market": "Delhi Azadpur", "state": "Delhi", "district": "North Delhi"},
    {"market": "Indore", "state": "Madhya Pradesh", "district": "Indore"},
    {"market": "Bhopal", "state": "Madhya Pradesh", "district": "Bhopal"},
    {"market": "Jaipur", "state": "Rajasthan", "district": "Jaipur"},
    {"market": "Patna", "state": "Bihar", "district": "Patna"},
    {"market": "Pune", "state": "Maharashtra", "district": "Pune"},
    {"market": "Nagpur", "state": "Maharashtra", "district": "Nagpur"},
    {"market": "Ludhiana", "state": "Punjab", "district": "Ludhiana"},
    {"market": "Karnal", "state": "Haryana", "district": "Karnal"},
    {"market": "Hisar", "state": "Haryana", "district": "Hisar"},
]


def generate_mock_price(commodity_info: dict, day: date, market_idx: int) -> dict:
    """Generate a realistic mock price for a commodity on a given day."""
    base = commodity_info["base_price"]
    amplitude = commodity_info["seasonal_amplitude"]
    peak_month = commodity_info["peak_month"]

    # Seasonal variation (sinusoidal)
    day_of_year = day.timetuple().tm_yday
    peak_day = (peak_month - 1) * 30 + 15
    seasonal = amplitude * math.sin(2 * math.pi * (day_of_year - peak_day) / 365)

    # Weekly variation (higher prices on Friday/Saturday)
    weekday = day.weekday()
    weekly = base * 0.03 * (weekday - 3)  # peaks on Saturday (5)

    # Market-specific offset (each market has slightly different prices)
    market_offset = (market_idx % 5 - 2) * base * 0.05

    # Random noise
    noise = random.gauss(0, base * 0.05)

    # Occasional spikes (5% chance of 20-40% spike)
    spike = 0
    if random.random() < 0.05:
        spike = base * random.uniform(0.2, 0.4) * random.choice([-1, 1])

    modal_price = max(base * 0.3, base + seasonal + weekly + market_offset + noise + spike)
    min_price = modal_price * random.uniform(0.80, 0.92)
    max_price = modal_price * random.uniform(1.08, 1.20)

    # Arrival in tonnes
    arrival = max(5, random.gauss(50, 20) + seasonal / base * 30)

    return {
        "min_price": round(min_price, 2),
        "max_price": round(max_price, 2),
        "modal_price": round(modal_price, 2),
        "arrival_tonnes": round(arrival, 2),
    }


def generate_mock_data(days: int = 365) -> list[dict]:
    """Generate mock mandi price data for all commodity-market pairs."""
    records = []
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    for commodity_name, commodity_info in COMMODITIES.items():
        for market_idx, market_info in enumerate(MARKETS):
            current_date = start_date
            while current_date <= end_date:
                # Skip Sundays (most mandis are closed)
                if current_date.weekday() != 6:
                    price_data = generate_mock_price(commodity_info, current_date, market_idx)
                    records.append({
                        "commodity": commodity_name,
                        "market": market_info["market"],
                        "state": market_info["state"],
                        "district": market_info["district"],
                        "min_price": price_data["min_price"],
                        "max_price": price_data["max_price"],
                        "modal_price": price_data["modal_price"],
                        "arrival_tonnes": price_data["arrival_tonnes"],
                        "price_date": current_date,
                    })
                current_date += timedelta(days=1)

    print(f"Generated {len(records)} mock price records")
    return records


def try_scrape_agmarknet(commodity: str, state: Optional[str] = None) -> list[dict]:
    """
    Attempt to scrape real data from agmarknet.gov.in.
    Returns empty list if scraping fails (site uses ASP.NET ViewState).
    """
    try:
        session = requests.Session()
        url = "https://agmarknet.gov.in/SearchCmmMkt.aspx"
        response = session.get(url, timeout=15)

        if response.status_code != 200:
            print(f"Agmarknet returned status {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "lxml")

        # Extract ViewState tokens for ASP.NET form
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})
        viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
        event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})

        if not all([viewstate, viewstate_gen, event_validation]):
            print("Could not extract ASP.NET form tokens")
            return []

        # Note: Full implementation would submit the form with commodity/state selection.
        # This is a placeholder — Agmarknet's form is complex with cascading dropdowns.
        print("Real Agmarknet scraping not yet fully implemented. Using mock data.")
        return []

    except Exception as e:
        print(f"Agmarknet scraping error: {e}")
        return []


def save_prices_to_db(prices: list[dict]):
    """Bulk insert price records into PostgreSQL."""
    if not prices:
        print("No prices to save")
        return

    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            insert_sql = """
                INSERT INTO mandi_prices
                    (commodity, market, state, district, min_price, max_price,
                     modal_price, arrival_tonnes, price_date)
                VALUES (%(commodity)s, %(market)s, %(state)s, %(district)s,
                        %(min_price)s, %(max_price)s, %(modal_price)s,
                        %(arrival_tonnes)s, %(price_date)s)
                ON CONFLICT DO NOTHING
            """
            psycopg2.extras.execute_batch(cur, insert_sql, prices, page_size=500)
            conn.commit()
            print(f"Saved {len(prices)} price records to database")
    except Exception as e:
        conn.rollback()
        print(f"Error saving prices: {e}")
    finally:
        conn.close()


def scrape_daily_prices():
    """Main scraper function — tries real scraping, falls back to mock."""
    print(f"Starting mandi price scrape at {datetime.now()}")

    # Try real scraping first
    real_data = try_scrape_agmarknet("Tomato")
    if real_data:
        save_prices_to_db(real_data)
        return

    # Fallback: generate today's mock data
    today = date.today()
    records = []
    for commodity_name, commodity_info in COMMODITIES.items():
        for market_idx, market_info in enumerate(MARKETS):
            if today.weekday() != 6:  # Skip Sundays
                price_data = generate_mock_price(commodity_info, today, market_idx)
                records.append({
                    "commodity": commodity_name,
                    "market": market_info["market"],
                    "state": market_info["state"],
                    "district": market_info["district"],
                    "min_price": price_data["min_price"],
                    "max_price": price_data["max_price"],
                    "modal_price": price_data["modal_price"],
                    "arrival_tonnes": price_data["arrival_tonnes"],
                    "price_date": today,
                })

    save_prices_to_db(records)
    print(f"Generated and saved {len(records)} mock prices for {today}")


def seed_historical_data(days: int = 365):
    """Generate and save historical mock data for initial setup."""
    print(f"Generating {days} days of historical mock data...")
    records = generate_mock_data(days)
    save_prices_to_db(records)
    print("Historical data seeding complete")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--seed":
        seed_historical_data(365)
    else:
        scrape_daily_prices()
