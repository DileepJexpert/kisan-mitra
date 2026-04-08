from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.schemas import MandiPriceResponse

router = APIRouter()


@router.get("/mandi/price")
async def get_mandi_price(
    commodity: str = Query(..., description="Commodity name"),
    market: str = Query(..., description="Market/mandi name"),
):
    """Get current mandi price for a commodity."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Mandi price endpoint not yet implemented"},
    )


@router.get("/mandi/predict")
async def predict_mandi_price(
    commodity: str = Query(..., description="Commodity name"),
    market: str = Query(..., description="Market/mandi name"),
    days: int = Query(30, description="Number of days to predict"),
):
    """Predict future mandi prices using ML models."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Mandi price prediction endpoint not yet implemented"},
    )


@router.get("/mandi/compare")
async def compare_mandi_prices(
    commodity: str = Query(..., description="Commodity name"),
    markets: str = Query(..., description="Comma-separated list of markets"),
):
    """Compare prices across multiple mandis."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Mandi price comparison endpoint not yet implemented"},
    )
