from fastapi import APIRouter

from app.schemas import SchemeSearchRequest, SchemeSearchResponse
from app.db.postgres_client import PostgresClient
from app.db.chroma_client import ChromaClient
from app.tools.scheme_tools import (
    check_eligibility,
    get_document_checklist,
    get_eligible_schemes_for_user,
    search_schemes,
)

router = APIRouter()


@router.post("/schemes/search", response_model=SchemeSearchResponse)
async def search_schemes_endpoint(request: SchemeSearchRequest):
    """Search government schemes using RAG."""
    chroma = ChromaClient()
    results = await search_schemes(
        chroma, request.query,
        sector=request.sector,
        state=request.state,
    )
    return SchemeSearchResponse(schemes=results)


@router.get("/schemes/eligible/{user_id}")
async def get_eligible_schemes(user_id: str, sector: str | None = None):
    """Get schemes a user is eligible for based on their profile."""
    db = PostgresClient()
    chroma = ChromaClient()
    results = await get_eligible_schemes_for_user(db, chroma, user_id, sector)
    return {"schemes": results}


@router.get("/schemes/details/{scheme_code}")
async def get_scheme_details(scheme_code: str):
    """Get detailed information about a specific scheme."""
    db = PostgresClient()
    scheme = await db.fetch_one("SELECT * FROM schemes WHERE scheme_code = $1", scheme_code)
    if not scheme:
        return {"error": "Scheme not found"}
    docs = await get_document_checklist(db, scheme_code)
    result = dict(scheme)
    result["documents_required"] = docs
    return result
