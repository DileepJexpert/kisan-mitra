"""
Mandi Agent Tools
- get_current_price, get_price_history, predict_price, compare_nearby_markets, set_price_alert
"""

import structlog
from datetime import date, timedelta
from app.db.postgres_client import PostgresClient

logger = structlog.get_logger(__name__)

# Hindi to English commodity mapping
HINDI_COMMODITY_MAP = {
    "tamatar": "Tomato", "टमाटर": "Tomato",
    "pyaz": "Onion", "प्याज": "Onion",
    "aloo": "Potato", "आलू": "Potato",
    "gehun": "Wheat", "गेहूं": "Wheat",
    "dhan": "Rice (Paddy)", "धान": "Rice (Paddy)",
    "soybean": "Soybean", "सोयाबीन": "Soybean",
    "sarson": "Mustard", "सरसों": "Mustard",
    "chana": "Chana (Gram)", "चना": "Chana (Gram)",
    "moong": "Moong", "मूंग": "Moong",
    "makka": "Maize", "मक्का": "Maize",
}


def normalize_commodity(name: str) -> str:
    """Convert Hindi commodity name to English standard name."""
    return HINDI_COMMODITY_MAP.get(name.lower().strip(), name)


async def get_current_price(db: PostgresClient, commodity: str, market: str) -> dict | None:
    """Get latest price for a commodity in a market."""
    commodity = normalize_commodity(commodity)
    row = await db.fetch_one(
        """SELECT commodity, market, state, district, min_price, max_price,
                  modal_price, arrival_tonnes, price_date
           FROM mandi_prices
           WHERE commodity = $1 AND market = $2
           ORDER BY price_date DESC LIMIT 1""",
        commodity, market)
    if row:
        return {k: (str(v) if isinstance(v, date) else float(v) if isinstance(v, (int, float)) else v)
                for k, v in dict(row).items()}
    return None


async def get_price_history(db: PostgresClient, commodity: str,
                             market: str, days: int = 30) -> list[dict]:
    """Get price history for last N days."""
    commodity = normalize_commodity(commodity)
    rows = await db.fetch_all(
        """SELECT price_date, modal_price, min_price, max_price, arrival_tonnes
           FROM mandi_prices
           WHERE commodity = $1 AND market = $2
             AND price_date >= CURRENT_DATE - $3
           ORDER BY price_date ASC""",
        commodity, market, days)
    return [
        {k: (str(v) if isinstance(v, date) else float(v) if isinstance(v, (int, float)) else v)
         for k, v in dict(r).items()}
        for r in rows
    ]


async def compare_nearby_markets(db: PostgresClient, commodity: str,
                                   state: str, max_markets: int = 5) -> list[dict]:
    """Get current prices across markets in a state for comparison."""
    commodity = normalize_commodity(commodity)
    rows = await db.fetch_all(
        """SELECT DISTINCT ON (market) market, state, district,
                  modal_price, min_price, max_price, price_date
           FROM mandi_prices
           WHERE commodity = $1 AND state = $2
           ORDER BY market, price_date DESC""",
        commodity, state)

    results = [
        {k: (str(v) if isinstance(v, date) else float(v) if isinstance(v, (int, float)) else v)
         for k, v in dict(r).items()}
        for r in rows
    ]
    results.sort(key=lambda x: float(x.get("modal_price", 0)), reverse=True)
    return results[:max_markets]


async def set_price_alert(db: PostgresClient, user_id: str, commodity: str,
                           market: str, alert_type: str, threshold: float) -> dict:
    """Create a price alert for a user."""
    commodity = normalize_commodity(commodity)
    await db.execute(
        """INSERT INTO price_alerts (user_id, commodity, market, alert_type, threshold_price)
           VALUES ($1, $2, $3, $4, $5)""",
        user_id, commodity, market, alert_type, threshold)
    return {"status": "created", "commodity": commodity, "market": market,
            "alert_type": alert_type, "threshold": threshold}
