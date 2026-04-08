import os
import json

from fastapi import APIRouter

from app.schemas import DPRGenerateRequest, DPRGenerateResponse
from app.db.postgres_client import PostgresClient
from app.tools.dpr_tools import (
    calculate_financials,
    generate_dpr_narrative,
    get_dpr_template,
    save_dpr_record,
)

router = APIRouter()


@router.post("/dpr/generate", response_model=DPRGenerateResponse)
async def generate_dpr(request: DPRGenerateRequest):
    """Generate a Detailed Project Report (DPR) for a business plan."""
    db = PostgresClient()

    # Load template
    template = get_dpr_template(request.business_type, request.scale)
    if not template:
        return DPRGenerateResponse(
            dpr_data={"error": f"No template for {request.business_type}"},
        )

    # Load user profile for category-based subsidy
    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", request.user_id)
    profile = dict(user) if user else {}
    category = profile.get("category", "general")

    # Find best subsidy
    applicable = template.get("applicable_schemes", [])
    best_subsidy = 0
    for scheme in applicable:
        if category in ("sc", "st"):
            sub = scheme.get("subsidy_sc_st", scheme.get("subsidy_general", 0))
        else:
            sub = scheme.get("subsidy_general", 0)
        best_subsidy = max(best_subsidy, sub)

    # Calculate financials
    financials = calculate_financials(template, subsidy_percent=best_subsidy)

    # Generate narrative
    narrative = await generate_dpr_narrative(template, financials, profile)

    # Save to DB
    dpr_data = {**financials, "narrative": narrative}
    record = await save_dpr_record(db, request.user_id, request.business_type, dpr_data)

    return DPRGenerateResponse(
        dpr_data={**dpr_data, "record": record},
    )


@router.get("/dpr/templates")
async def list_dpr_templates():
    """List available DPR templates by business type."""
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "templates")
    if not os.path.exists(templates_dir):
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "templates")

    templates = []
    if os.path.exists(templates_dir):
        for f in os.listdir(templates_dir):
            if f.startswith("dpr_") and f.endswith(".json"):
                with open(os.path.join(templates_dir, f), "r") as fh:
                    data = json.load(fh)
                templates.append({
                    "business_type": data.get("business_type", ""),
                    "name_en": data.get("business_name_en", ""),
                    "name_hi": data.get("business_name_hi", ""),
                    "variants": list(data.get("variants", {}).keys()),
                })
    return {"templates": templates}
