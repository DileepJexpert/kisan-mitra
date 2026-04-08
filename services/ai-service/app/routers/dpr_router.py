from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas import DPRGenerateRequest, DPRGenerateResponse

router = APIRouter()


@router.post("/dpr/generate", response_model=DPRGenerateResponse)
async def generate_dpr(request: DPRGenerateRequest):
    """Generate a Detailed Project Report (DPR) for a business plan."""
    return JSONResponse(
        status_code=501,
        content={"detail": "DPR generation endpoint not yet implemented"},
    )


@router.get("/dpr/templates")
async def list_dpr_templates():
    """List available DPR templates by business type."""
    return JSONResponse(
        status_code=501,
        content={"detail": "DPR templates listing endpoint not yet implemented"},
    )
