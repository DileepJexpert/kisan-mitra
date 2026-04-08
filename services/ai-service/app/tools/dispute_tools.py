"""
Dispute Agent Tools
- extract_invoice_data: OCR + LLM parsing
- calculate_msmed_interest: compound interest per MSMED Act
- generate_legal_notice: Claude Sonnet quality
- create_dispute_record, update_dispute_status
"""

import json
from datetime import date, datetime
from math import pow

import structlog

from app.db.postgres_client import PostgresClient
from app.models.llm_provider import get_llm_router
from app.models.ocr_provider import get_ocr_provider

logger = structlog.get_logger(__name__)

# RBI Bank Rate as of 2026 (approximate)
RBI_BANK_RATE = 6.5
MSMED_INTEREST_RATE = RBI_BANK_RATE * 3  # 19.5% per annum


async def extract_invoice_data(image_bytes: bytes) -> dict:
    """OCR extract + LLM parse invoice data."""
    ocr = get_ocr_provider()
    ocr_result = await ocr.extract(image_bytes)
    raw_text = ocr_result.get("raw_text", "")

    if not raw_text.strip():
        return {"error": "Could not extract text from image", "raw_text": ""}

    # Use LLM to parse structured data from OCR text
    router = get_llm_router()
    prompt = f"""Extract the following fields from this invoice text and return as JSON:
- invoice_number
- invoice_date (DD/MM/YYYY)
- buyer_name
- buyer_gstin
- buyer_address
- total_amount (number only)
- payment_terms (if mentioned)

Invoice text:
{raw_text}

Return ONLY valid JSON, no markdown."""

    try:
        response = await router.chat_cheap([{"role": "user", "content": prompt}])
        # Try to parse JSON from response
        json_str = response.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("```")[1].strip()
            if json_str.startswith("json"):
                json_str = json_str[4:].strip()
        parsed = json.loads(json_str)
        parsed["raw_text"] = raw_text
        parsed["confidence"] = ocr_result.get("confidence", 0)
        return parsed
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("invoice.parse_failed", error=str(e))
        return {"raw_text": raw_text, "confidence": ocr_result.get("confidence", 0),
                "error": "Could not parse structured data"}


def calculate_msmed_interest(principal: float, due_date: date,
                              calculation_date: date | None = None) -> dict:
    """
    Calculate compound interest under MSMED Act Section 16.
    Rate: 3x RBI bank rate, compounded monthly.
    """
    if calculation_date is None:
        calculation_date = date.today()

    days_overdue = (calculation_date - due_date).days
    if days_overdue <= 0:
        return {"principal": principal, "days_overdue": 0, "interest_amount": 0,
                "total_claim": principal, "interest_rate_annual": MSMED_INTEREST_RATE}

    months_overdue = days_overdue / 30.0
    monthly_rate = MSMED_INTEREST_RATE / 100 / 12

    # Compound interest: A = P(1 + r)^n
    amount = principal * pow(1 + monthly_rate, months_overdue)
    interest = amount - principal

    return {
        "principal": round(principal, 2),
        "due_date": str(due_date),
        "calculation_date": str(calculation_date),
        "days_overdue": days_overdue,
        "months_overdue": round(months_overdue, 1),
        "interest_rate_annual": MSMED_INTEREST_RATE,
        "interest_amount": round(interest, 2),
        "total_claim": round(amount, 2),
        "legal_basis": "Section 15 & 16 of MSMED Act, 2006",
    }


async def generate_legal_notice(dispute_data: dict) -> str:
    """Generate professional legal notice using Claude Sonnet."""
    router = get_llm_router()

    prompt = f"""Generate a formal legal notice under Section 15 of the MSMED Act, 2006 for delayed payment.

Details:
- Sender: {dispute_data.get('sender_name', 'MSME Owner')}
- Sender Udyam: {dispute_data.get('udyam_number', 'UDYAM-XX-00-0000000')}
- Buyer: {dispute_data.get('buyer_name', '')}
- Buyer GSTIN: {dispute_data.get('buyer_gstin', '')}
- Invoice Number: {dispute_data.get('invoice_number', '')}
- Invoice Date: {dispute_data.get('invoice_date', '')}
- Invoice Amount: Rs.{dispute_data.get('invoice_amount', 0)}
- Due Date: {dispute_data.get('due_date', '')}
- Days Overdue: {dispute_data.get('days_overdue', 0)}
- Interest Rate: {MSMED_INTEREST_RATE}% p.a. (3x RBI Bank Rate)
- Interest Amount: Rs.{dispute_data.get('interest_amount', 0)}
- Total Claim: Rs.{dispute_data.get('total_claim', 0)}

Generate a professional legal notice in English. Include:
1. Reference to MSMED Act Section 15 (payment obligation) and Section 16 (interest)
2. Clear demand for payment within 15 days
3. Warning of MSEFC proceedings if not paid
4. Proper legal notice format with date and reference number"""

    notice = await router.chat_quality([
        {"role": "system", "content": "You are a legal document generator specializing in MSME payment recovery under Indian law."},
        {"role": "user", "content": prompt},
    ], max_tokens=2000)

    return notice


async def create_dispute_record(db: PostgresClient, user_id: str, dispute_data: dict) -> dict:
    """Create a new dispute record in the database."""
    row = await db.fetch_one(
        """INSERT INTO disputes (user_id, buyer_name, buyer_gstin, invoice_number,
                  invoice_date, invoice_amount, due_date, days_overdue,
                  interest_amount, total_claim, status)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'new')
           RETURNING id, status""",
        user_id, dispute_data.get("buyer_name"), dispute_data.get("buyer_gstin"),
        dispute_data.get("invoice_number"), dispute_data.get("invoice_date"),
        dispute_data.get("invoice_amount"), dispute_data.get("due_date"),
        dispute_data.get("days_overdue"), dispute_data.get("interest_amount"),
        dispute_data.get("total_claim"))
    return dict(row) if row else {"error": "Failed to create dispute"}
