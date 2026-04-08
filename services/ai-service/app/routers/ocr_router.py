"""
OCR Router
Extracts text from images using PaddleOCR (Hindi + English).
Supports structured parsing for invoices, PAN, Aadhaar references.
"""

import base64

from fastapi import APIRouter, HTTPException
import structlog

from app.schemas import OCRRequest, OCRResponse
from app.models.ocr_provider import get_ocr_provider
from app.models.llm_provider import get_llm_router

logger = structlog.get_logger(__name__)

router = APIRouter()

# Document type → LLM parsing prompts
DOCUMENT_PARSERS = {
    "invoice": """Extract the following fields from this invoice/bill text. Return valid JSON only.
{
  "invoice_number": "",
  "invoice_date": "",
  "buyer_name": "",
  "buyer_gstin": "",
  "buyer_address": "",
  "seller_name": "",
  "seller_gstin": "",
  "items": [{"description": "", "quantity": 0, "rate": 0, "amount": 0}],
  "subtotal": 0,
  "gst_amount": 0,
  "total_amount": 0,
  "payment_terms": "",
  "due_date": ""
}
If a field is not found, use null. Amounts should be numbers without currency symbols.""",

    "pan_card": """Extract the following fields from this PAN card text. Return valid JSON only.
{
  "pan_number": "",
  "name": "",
  "father_name": "",
  "date_of_birth": ""
}
Only return the data, no explanations.""",

    "aadhaar": """Extract only the NAME and LAST 4 DIGITS of Aadhaar number from this text.
Do NOT extract the full Aadhaar number for privacy.
Return valid JSON only:
{
  "name": "",
  "aadhaar_last4": "",
  "address": "",
  "date_of_birth": ""
}""",

    "bank_statement": """Extract the following from this bank statement text. Return valid JSON only.
{
  "account_holder": "",
  "account_number_last4": "",
  "bank_name": "",
  "branch": "",
  "statement_period": "",
  "opening_balance": 0,
  "closing_balance": 0,
  "total_credits": 0,
  "total_debits": 0
}
Only return last 4 digits of account number for privacy.""",

    "land_record": """Extract the following from this land record/khasra text. Return valid JSON only.
{
  "owner_name": "",
  "khasra_number": "",
  "village": "",
  "tehsil": "",
  "district": "",
  "area_acres": 0,
  "land_type": "",
  "crop_season": ""
}""",
}


@router.post("/ocr/extract", response_model=OCRResponse)
async def extract_text(request: OCRRequest):
    """Extract text from an image using PaddleOCR with optional structured parsing."""
    try:
        image_bytes = base64.b64decode(request.image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    if len(image_bytes) < 100:
        raise HTTPException(status_code=400, detail="Image data too small")

    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    # Run OCR
    ocr = get_ocr_provider()
    try:
        ocr_result = await ocr.extract(image_bytes)
    except Exception as e:
        logger.error("ocr.extract_failed", error=str(e))
        raise HTTPException(status_code=503, detail="OCR service unavailable")

    raw_text = ocr_result.get("raw_text", "")
    confidence = ocr_result.get("confidence", 0.0)

    if not raw_text:
        return OCRResponse(
            raw_text="",
            structured_data=None,
            confidence=0.0,
        )

    # Structured parsing if document type specified
    structured_data = None
    if request.document_type != "general" and request.document_type in DOCUMENT_PARSERS:
        structured_data = await _parse_document(raw_text, request.document_type)

    return OCRResponse(
        raw_text=raw_text,
        structured_data=structured_data,
        confidence=confidence,
    )


async def _parse_document(raw_text: str, doc_type: str) -> dict | None:
    """Use LLM to parse OCR text into structured fields."""
    parse_prompt = DOCUMENT_PARSERS.get(doc_type)
    if not parse_prompt:
        return None

    llm = get_llm_router()
    try:
        response = await llm.chat_cheap([
            {"role": "system", "content": "You are a document parser. Extract structured data from OCR text. Return ONLY valid JSON, no markdown, no explanation."},
            {"role": "user", "content": f"{parse_prompt}\n\nOCR Text:\n{raw_text}"},
        ], temperature=0.1, max_tokens=1024)

        # Parse JSON from response
        import json
        # Strip markdown code blocks if present
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()

        return json.loads(text)
    except Exception as e:
        logger.warning("ocr.parse_failed", doc_type=doc_type, error=str(e))
        return None
