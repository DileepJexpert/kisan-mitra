from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/predict/price")
async def predict_price(
    commodity: str = Query(..., description="Commodity name"),
    market: str = Query(None, description="Market/mandi name"),
    days: int = Query(30, description="Number of days to predict"),
):
    """Predict commodity prices using Prophet / scikit-learn models."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Price prediction endpoint not yet implemented"},
    )
