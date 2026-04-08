from fastapi import APIRouter, Query

from app.db.postgres_client import PostgresClient
from app.tools.price_predictor import predict_price

router = APIRouter()


@router.get("/predict/price")
async def predict_price_endpoint(
    commodity: str = Query(..., description="Commodity name"),
    market: str = Query(..., description="Market/mandi name"),
    days: int = Query(7, ge=1, le=30, description="Days ahead to predict"),
):
    """Predict commodity prices using Prophet / moving average models."""
    db = PostgresClient()
    result = await predict_price(db, commodity, market, days)
    return result
