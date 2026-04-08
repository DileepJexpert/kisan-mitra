from fastapi import APIRouter, Query

from app.db.postgres_client import PostgresClient
from app.tools.mandi_tools import (
    compare_nearby_markets,
    get_current_price,
    get_price_history,
)

router = APIRouter()


@router.get("/mandi/price")
async def get_mandi_price(
    commodity: str = Query(..., description="Commodity name (Hindi or English)"),
    market: str = Query(..., description="Market/mandi name"),
):
    """Get current mandi price for a commodity."""
    db = PostgresClient()
    price = await get_current_price(db, commodity, market)
    if price:
        return price
    return {"error": "Price data not available", "commodity": commodity, "market": market}


@router.get("/mandi/history")
async def get_mandi_history(
    commodity: str = Query(...),
    market: str = Query(...),
    days: int = Query(30, ge=1, le=365),
):
    """Get price history for a commodity in a market."""
    db = PostgresClient()
    history = await get_price_history(db, commodity, market, days)
    return {"commodity": commodity, "market": market, "history": history}


@router.get("/mandi/compare")
async def compare_mandi_prices(
    commodity: str = Query(..., description="Commodity name"),
    state: str = Query(..., description="State name"),
    max_markets: int = Query(5, ge=1, le=20),
):
    """Compare prices across markets in a state."""
    db = PostgresClient()
    results = await compare_nearby_markets(db, commodity, state, max_markets)
    return {"commodity": commodity, "state": state, "markets": results}
