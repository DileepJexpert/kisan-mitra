from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas import DisputeAnalyzeRequest, DisputeAnalyzeResponse

router = APIRouter()


@router.post("/dispute/analyze", response_model=DisputeAnalyzeResponse)
async def analyze_dispute(request: DisputeAnalyzeRequest):
    """Analyze an invoice/dispute and calculate interest owed."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Dispute analysis endpoint not yet implemented"},
    )


@router.post("/dispute/generate-notice")
async def generate_legal_notice(request: DisputeAnalyzeRequest):
    """Generate a legal notice draft for a dispute."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Legal notice generation endpoint not yet implemented"},
    )
