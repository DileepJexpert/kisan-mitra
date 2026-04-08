"""
Weather Data Scraper
Fetches weather data from Open-Meteo API (free, no API key needed).
Used as features for price prediction models.
"""

import os
from datetime import datetime

import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql://admin:password@localhost:5432/kisanmitra")

# Coordinates for mandi locations
LOCATIONS = {
    "Kanpur": {"lat": 26.4499, "lon": 80.3319},
    "Lucknow": {"lat": 26.8467, "lon": 80.9462},
    "Varanasi": {"lat": 25.3176, "lon": 82.9739},
    "Agra": {"lat": 27.1767, "lon": 78.0081},
    "Prayagraj": {"lat": 25.4358, "lon": 81.8463},
    "Delhi Azadpur": {"lat": 28.7041, "lon": 77.1025},
    "Indore": {"lat": 22.7196, "lon": 75.8577},
    "Bhopal": {"lat": 23.2599, "lon": 77.4126},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873},
    "Patna": {"lat": 25.6093, "lon": 85.1376},
    "Pune": {"lat": 18.5204, "lon": 73.8567},
    "Nagpur": {"lat": 21.1458, "lon": 79.0882},
    "Ludhiana": {"lat": 30.9010, "lon": 75.8573},
    "Karnal": {"lat": 29.6857, "lon": 76.9905},
    "Hisar": {"lat": 29.1492, "lon": 75.7217},
}


def fetch_weather(location_name: str, lat: float, lon: float) -> dict | None:
    """Fetch current weather from Open-Meteo API."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,rain,wind_speed_10m"
            f"&daily=temperature_2m_max,temperature_2m_min,rain_sum"
            f"&timezone=Asia/Kolkata&forecast_days=1"
        )
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            return {
                "location": location_name,
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "rain_mm": current.get("rain", 0),
                "wind_speed": current.get("wind_speed_10m"),
                "fetched_at": datetime.now(),
            }
        else:
            print(f"Weather API returned {response.status_code} for {location_name}")
            return None
    except Exception as e:
        print(f"Error fetching weather for {location_name}: {e}")
        return None


def scrape_weather():
    """Fetch weather for all mandi locations."""
    print(f"Fetching weather data at {datetime.now()}")
    weather_data = []

    for location, coords in LOCATIONS.items():
        data = fetch_weather(location, coords["lat"], coords["lon"])
        if data:
            weather_data.append(data)

    print(f"Fetched weather for {len(weather_data)}/{len(LOCATIONS)} locations")
    # Weather data is used by prediction models at query time.
    # For now, just log it. In production, store in a weather_data table.
    for w in weather_data:
        print(f"  {w['location']}: {w['temperature']}°C, "
              f"humidity {w['humidity']}%, rain {w['rain_mm']}mm")

    return weather_data


if __name__ == "__main__":
    scrape_weather()
