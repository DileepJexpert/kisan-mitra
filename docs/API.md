# KisanMitra AI Platform — API Reference

## Base URLs
- **Gateway**: `http://localhost:8080/api/v1`
- **AI Service**: `http://localhost:8001/ai/v1`

## Authentication

### Send OTP
```
POST /api/v1/auth/send-otp
Body: { "phone": "9876543210" }
Response: { "message": "OTP sent", "expires_in": 300 }
```

### Verify OTP
```
POST /api/v1/auth/verify-otp
Body: { "phone": "9876543210", "otp": "123456" }
Response: {
  "token": "eyJ...",
  "refreshToken": "eyJ...",
  "user": { "id": "uuid", "phone": "9876543210", "name": null }
}
```

### Refresh Token
```
POST /api/v1/auth/refresh
Body: { "refreshToken": "eyJ..." }
Response: { "token": "new_jwt", "refreshToken": "new_refresh" }
```

## Chat (Main Agent Endpoint)

### Agent Chat
```
POST /ai/v1/agent/chat
Body: {
  "user_id": "uuid",
  "message": "tamatar ka bhav batao",
  "language": "hi",
  "channel": "whatsapp",
  "audio_base64": null
}
Response: {
  "reply_text": "📊 Tomato — Kanpur\nआज का भाव: Rs.2500/क्विंटल...",
  "reply_audio_base64": null,
  "agents_used": ["mandi"],
  "actions_taken": ["get_current_price"],
  "follow_up_actions": []
}
```

## Schemes

### Search Schemes
```
POST /ai/v1/schemes/search
Body: { "query": "dairy farming subsidy", "sector": "dairy" }
Response: { "schemes": [{ "scheme_code": "NABARD_DEDS", ... }] }
```

### Eligible Schemes for User
```
GET /ai/v1/schemes/eligible/{user_id}?sector=agriculture
Response: { "schemes": [{ "scheme_code": "PM_KISAN", "eligible": true, ... }] }
```

### Scheme Details
```
GET /ai/v1/schemes/details/PMFME
Response: { "scheme_code": "PMFME", "name_en": "...", "documents_required": [...] }
```

## Mandi Prices

### Current Price
```
GET /ai/v1/mandi/price?commodity=Tomato&market=Kanpur
Response: { "commodity": "Tomato", "market": "Kanpur", "modal_price": 2500, ... }
```

### Price History
```
GET /ai/v1/mandi/history?commodity=Tomato&market=Kanpur&days=30
Response: { "commodity": "Tomato", "history": [{ "price_date": "2026-04-01", ... }] }
```

### Market Comparison
```
GET /ai/v1/mandi/compare?commodity=Tomato&state=Uttar Pradesh
Response: { "markets": [{ "market": "Kanpur", "modal_price": 2500 }, ...] }
```

### Price Prediction
```
GET /ai/v1/predict/price?commodity=Tomato&market=Kanpur&days=7
Response: {
  "forecast": [{ "date": "2026-04-09", "predicted_price": 2600, ... }],
  "recommendation": "HOLD",
  "reason": "Prices expected to rise by 5.2%..."
}
```

## Loans

### Check Eligibility
```
POST /ai/v1/loan/check
Body: { "user_id": "uuid", "amount_needed": 500000 }
Response: {
  "eligible_loans": [{ "loan_code": "KCC", "eligible": true, ... }],
  "recommended_combination": { ... }
}
```

### Calculate EMI
```
POST /ai/v1/loan/emi?principal=500000&annual_rate=10&tenure_years=5
Response: { "emi_monthly": 10624.25, "total_interest": 137455, "total_payment": 637455 }
```

## Disputes

### Analyze Invoice
```
POST /ai/v1/dispute/analyze
Body: { "user_id": "uuid", "invoice_image_base64": "base64...", "invoice_data": null }
Response: { "invoice_data": { ... }, "interest_calculation": { "days_overdue": 45, ... } }
```

### Generate Legal Notice
```
POST /ai/v1/dispute/generate-notice
Body: { "user_id": "uuid", "invoice_data": { "total_amount": 350000, "due_date": "2026-01-01" } }
Response: { "legal_notice": "...", "dispute_record": { "id": "uuid" } }
```

## DPR (Project Reports)

### Generate DPR
```
POST /ai/v1/dpr/generate
Body: { "user_id": "uuid", "business_type": "dairy_farm", "scale": "10_cow" }
Response: { "dpr_data": { "project_cost": { ... }, "financial_ratios": { ... } } }
```

### List Templates
```
GET /ai/v1/dpr/templates
Response: { "templates": [{ "business_type": "dairy_farm", "variants": ["10_cow", "20_cow"] }] }
```

## Speech/Vision Services

### Speech-to-Text
```
POST /ai/v1/stt/transcribe
Body: { "audio_base64": "base64...", "language": "hi" }
Response: { "text": "tamatar ka bhav batao", "confidence": 0.92 }
```

### Text-to-Speech
```
POST /ai/v1/tts/speak
Body: { "text": "आज टमाटर का भाव 2500 रुपये प्रति क्विंटल है", "language": "hi" }
Response: { "audio_base64": "base64...", "duration_seconds": 3.5 }
```

### OCR
```
POST /ai/v1/ocr/extract
Body: { "image_base64": "base64...", "document_type": "invoice" }
Response: { "raw_text": "...", "structured_data": { "invoice_number": "INV-001", ... } }
```

## Health Check
```
GET /health
Response: { "status": "healthy", "checks": { "postgres": "healthy", "redis": "healthy", "chroma": "healthy" } }
```

## Error Responses
All errors return:
```json
{ "error": "error_type", "message": "Human-readable message", "timestamp": 1712345678 }
```

| Code | Meaning |
|------|---------|
| 400 | Bad request (validation error) |
| 401 | Unauthorized (invalid/expired JWT) |
| 403 | Forbidden |
| 404 | Not found |
| 422 | Unprocessable (e.g., OCR failed) |
| 429 | Rate limited |
| 500 | Internal server error |
| 503 | Service unavailable (LLM/STT/TTS down) |
