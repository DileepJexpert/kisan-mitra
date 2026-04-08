"""
Scheme Agent Tools
- search_schemes: RAG search over ChromaDB
- check_eligibility: rule engine match
- get_document_checklist: list of required documents
- get_eligible_schemes_for_user: main function
"""

import json
import structlog
from app.db.postgres_client import PostgresClient
from app.db.chroma_client import ChromaClient

logger = structlog.get_logger(__name__)


async def search_schemes(chroma: ChromaClient, query: str,
                          sector: str | None = None, state: str | None = None,
                          n_results: int = 10) -> list[dict]:
    """Semantic search over schemes in ChromaDB."""
    where_filter = {}
    if sector:
        where_filter["sector"] = sector
    if state:
        where_filter["state"] = state

    results = chroma.search(
        collection_name="schemes",
        query_text=query,
        n_results=n_results,
        where=where_filter if where_filter else None,
    )
    return results


async def check_eligibility(db: PostgresClient, user_id: str, scheme_code: str) -> dict:
    """Check if user is eligible for a specific scheme."""
    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
    if not user:
        return {"eligible": False, "reason": "User not found"}

    scheme = await db.fetch_one("SELECT * FROM schemes WHERE scheme_code = $1", scheme_code)
    if not scheme:
        return {"eligible": False, "reason": "Scheme not found"}

    criteria = json.loads(scheme["eligibility_criteria"]) if isinstance(scheme["eligibility_criteria"], str) else scheme["eligibility_criteria"]

    matched = []
    failed = []

    # Income check
    if criteria.get("income_max") and user.get("income_annual"):
        if float(user["income_annual"]) <= criteria["income_max"]:
            matched.append("income")
        else:
            failed.append(f"income exceeds max {criteria['income_max']}")

    # Category check
    if criteria.get("categories"):
        if user.get("category") and user["category"].lower() in [c.lower() for c in criteria["categories"]]:
            matched.append("category")
        elif user.get("category"):
            failed.append(f"category {user['category']} not eligible")

    # Gender check
    if criteria.get("gender"):
        if user.get("gender") and user["gender"].lower() in [g.lower() for g in criteria["gender"]]:
            matched.append("gender")
        elif user.get("gender"):
            failed.append(f"gender {user['gender']} not eligible")

    # Occupation check
    if criteria.get("occupation"):
        occupations = [o.lower() for o in criteria["occupation"]]
        if "any" in occupations:
            matched.append("occupation")
        elif user.get("occupation") and user["occupation"].lower() in occupations:
            matched.append("occupation")
        elif user.get("occupation"):
            failed.append(f"occupation {user['occupation']} not eligible")

    # Land check
    if criteria.get("land_max_acres") and user.get("land_acres"):
        if float(user["land_acres"]) <= criteria["land_max_acres"]:
            matched.append("land_size")
        else:
            failed.append(f"land {user['land_acres']} acres exceeds max")

    # Udyam check
    if criteria.get("udyam_required"):
        if user.get("udyam_number"):
            matched.append("udyam_registered")
        else:
            failed.append("udyam registration required")

    eligible = len(failed) == 0
    match_score = len(matched) / max(len(matched) + len(failed), 1)

    return {
        "eligible": eligible,
        "match_score": round(match_score, 2),
        "matched_criteria": matched,
        "failed_criteria": failed,
        "scheme_code": scheme_code,
        "scheme_name": scheme.get("name_en", ""),
        "benefit_type": scheme.get("benefit_type", ""),
        "subsidy_percentage": float(scheme["subsidy_percentage"]) if scheme.get("subsidy_percentage") else None,
        "max_subsidy_amount": float(scheme["max_subsidy_amount"]) if scheme.get("max_subsidy_amount") else None,
    }


async def get_document_checklist(db: PostgresClient, scheme_code: str) -> list[str]:
    """Get list of documents required for a scheme."""
    scheme = await db.fetch_one(
        "SELECT documents_required FROM schemes WHERE scheme_code = $1", scheme_code)
    if not scheme:
        return []
    docs = scheme["documents_required"]
    if isinstance(docs, str):
        return json.loads(docs)
    return docs or []


async def get_eligible_schemes_for_user(db: PostgresClient, chroma: ChromaClient,
                                         user_id: str, sector: str | None = None) -> list[dict]:
    """Get all eligible schemes for a user, sorted by match score."""
    # Get all active schemes
    if sector:
        schemes = await db.fetch_all(
            "SELECT scheme_code FROM schemes WHERE is_active = true AND sector = $1", sector)
    else:
        schemes = await db.fetch_all(
            "SELECT scheme_code FROM schemes WHERE is_active = true")

    results = []
    for scheme in schemes:
        eligibility = await check_eligibility(db, user_id, scheme["scheme_code"])
        if eligibility["eligible"]:
            results.append(eligibility)

    # Sort by match score descending
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results
