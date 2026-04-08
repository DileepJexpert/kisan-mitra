from pydantic import BaseModel


# ── Agent ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id: str
    message: str
    language: str = "hi"
    channel: str = "whatsapp"
    audio_base64: str | None = None


class ChatResponse(BaseModel):
    reply_text: str
    reply_audio_base64: str | None = None
    agents_used: list[str] = []
    actions_taken: list[str] = []
    follow_up_actions: list[dict] = []


# ── Schemes ──────────────────────────────────────────────────────────────────

class SchemeSearchRequest(BaseModel):
    query: str
    user_id: str | None = None
    sector: str | None = None
    state: str | None = None


class SchemeSearchResponse(BaseModel):
    schemes: list[dict]


# ── Mandi Prices ─────────────────────────────────────────────────────────────

class MandiPriceResponse(BaseModel):
    commodity: str
    market: str
    current_price: dict | None = None
    history: list[dict] = []
    prediction: list[dict] | None = None
    recommendation: str | None = None


# ── Loans ────────────────────────────────────────────────────────────────────

class LoanCheckRequest(BaseModel):
    user_id: str
    loan_type: str | None = None
    amount_needed: float | None = None


class LoanCheckResponse(BaseModel):
    eligible_loans: list[dict]
    recommended_combination: dict | None = None


# ── Disputes ─────────────────────────────────────────────────────────────────

class DisputeAnalyzeRequest(BaseModel):
    user_id: str
    invoice_image_base64: str | None = None
    invoice_data: dict | None = None


class DisputeAnalyzeResponse(BaseModel):
    invoice_data: dict
    interest_calculation: dict
    legal_notice_draft: str | None = None


# ── DPR ──────────────────────────────────────────────────────────────────────

class DPRGenerateRequest(BaseModel):
    user_id: str
    business_type: str
    scale: str | None = None
    location: str | None = None


class DPRGenerateResponse(BaseModel):
    dpr_data: dict
    pdf_url: str | None = None


# ── Speech-to-Text ───────────────────────────────────────────────────────────

class STTRequest(BaseModel):
    audio_base64: str
    language: str = "hi"


class STTResponse(BaseModel):
    text: str
    language_detected: str | None = None
    confidence: float | None = None


# ── Text-to-Speech ───────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    language: str = "hi"
    voice: str = "female_hindi_1"


class TTSResponse(BaseModel):
    audio_base64: str
    duration_seconds: float | None = None


# ── OCR ──────────────────────────────────────────────────────────────────────

class OCRRequest(BaseModel):
    image_base64: str
    document_type: str = "general"


class OCRResponse(BaseModel):
    raw_text: str
    structured_data: dict | None = None
    confidence: float | None = None


# ── Predictions ──────────────────────────────────────────────────────────────

# (Uses MandiPriceResponse for output)


# ── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    checks: dict
