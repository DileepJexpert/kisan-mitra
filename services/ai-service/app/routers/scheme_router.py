from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas import SchemeSearchRequest, SchemeSearchResponse

router = APIRouter()


@router.post("/schemes/search", response_model=SchemeSearchResponse)
async def search_schemes(request: SchemeSearchRequest):
    """Search government schemes using RAG."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Scheme search endpoint not yet implemented"},
    )


@router.get("/schemes/eligible/{user_id}")
async def get_eligible_schemes(user_id: str):
    """Get schemes a user is eligible for based on their profile."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Eligible schemes endpoint not yet implemented"},
    )


@router.get("/schemes/details/{scheme_code}")
async def get_scheme_details(scheme_code: str):
    """Get detailed information about a specific scheme."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Scheme details endpoint not yet implemented"},
    )
