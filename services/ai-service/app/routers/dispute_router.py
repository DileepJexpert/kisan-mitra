import base64
from datetime import date

from fastapi import APIRouter

from app.schemas import DisputeAnalyzeRequest, DisputeAnalyzeResponse
from app.db.postgres_client import PostgresClient
from app.tools.dispute_tools import (
    calculate_msmed_interest,
    create_dispute_record,
    extract_invoice_data,
    generate_legal_notice,
)

router = APIRouter()


@router.post("/dispute/analyze", response_model=DisputeAnalyzeResponse)
async def analyze_dispute(request: DisputeAnalyzeRequest):
    """Analyze an invoice/dispute and calculate interest owed."""
    invoice_data = request.invoice_data or {}

    # OCR extract if image provided
    if request.invoice_image_base64:
        image_bytes = base64.b64decode(request.invoice_image_base64)
        invoice_data = await extract_invoice_data(image_bytes)

    # Calculate interest
    interest = {}
    if invoice_data.get("total_amount") and invoice_data.get("due_date"):
        from app.agents.dispute_agent import _parse_date
        due = _parse_date(invoice_data["due_date"])
        interest = calculate_msmed_interest(float(invoice_data["total_amount"]), due)

    return DisputeAnalyzeResponse(
        invoice_data=invoice_data,
        interest_calculation=interest,
    )


@router.post("/dispute/generate-notice")
async def generate_notice(request: DisputeAnalyzeRequest):
    """Generate a legal notice draft for a dispute."""
    db = PostgresClient()
    invoice_data = request.invoice_data or {}

    # Calculate interest first
    interest = {}
    if invoice_data.get("total_amount") and invoice_data.get("due_date"):
        from app.agents.dispute_agent import _parse_date
        due = _parse_date(invoice_data["due_date"])
        interest = calculate_msmed_interest(float(invoice_data["total_amount"]), due)

    dispute_data = {**invoice_data, **interest}
    notice = await generate_legal_notice(dispute_data)

    # Save dispute record
    record = await create_dispute_record(db, request.user_id, {
        **invoice_data,
        "days_overdue": interest.get("days_overdue"),
        "interest_amount": interest.get("interest_amount"),
        "total_claim": interest.get("total_claim"),
    })

    return {
        "legal_notice": notice,
        "interest_calculation": interest,
        "dispute_record": record,
    }
