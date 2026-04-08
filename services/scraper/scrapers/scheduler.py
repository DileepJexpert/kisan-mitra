"""
Scraper Scheduler
Runs all scrapers on a schedule using the 'schedule' library.
This is the main entry point for the scraper Docker container.
"""

import signal
import sys
import time

import schedule

from agmarknet_scraper import scrape_daily_prices
from myscheme_scraper import load_schemes
from weather_scraper import scrape_weather


def graceful_shutdown(signum, frame):
    """Handle graceful shutdown on SIGTERM/SIGINT."""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    sys.exit(0)


def run_with_error_handling(func, name: str):
    """Wrapper to catch and log errors without crashing the scheduler."""
    def wrapper():
        try:
            print(f"\n{'='*50}")
            print(f"Running: {name}")
            print(f"{'='*50}")
            func()
        except Exception as e:
            print(f"ERROR in {name}: {e}")
    return wrapper


def main():
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)

    print("=" * 60)
    print("KisanMitra Scraper Scheduler Starting")
    print("=" * 60)

    # Schedule scrapers
    schedule.every(2).hours.do(
        run_with_error_handling(scrape_daily_prices, "Agmarknet Mandi Price Scraper")
    )

    schedule.every().day.at("00:00").do(
        run_with_error_handling(load_schemes, "Government Scheme Loader")
    )

    schedule.every(6).hours.do(
        run_with_error_handling(scrape_weather, "Weather Data Scraper")
    )

    # Run once on startup
    print("\nRunning initial scrape on startup...")
    run_with_error_handling(scrape_daily_prices, "Agmarknet (startup)")()
    run_with_error_handling(scrape_weather, "Weather (startup)")()

    print("\nScheduler running. Waiting for next scheduled tasks...")
    print("  - Mandi prices: every 2 hours")
    print("  - Scheme data: daily at midnight")
    print("  - Weather data: every 6 hours")

    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
