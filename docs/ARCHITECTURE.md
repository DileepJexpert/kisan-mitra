# KisanMitra AI Platform — Architecture

## 5-Layer Architecture

```
┌─────────────────────────────────────────────────┐
│  Layer 5: Product Logic (KisanMitra)            │
│  WhatsApp Bot · Agent Orchestration             │
├─────────────────────────────────────────────────┤
│  Layer 4: Agent Framework (LangGraph)           │
│  Supervisor · Scheme · Mandi · Loan · DPR       │
├─────────────────────────────────────────────────┤
│  Layer 3: AI Services                           │
│  LLM Router · STT · TTS · OCR · Price Predict  │
├─────────────────────────────────────────────────┤
│  Layer 2: Platform Services                     │
│  Auth/JWT · User Mgmt · Notifications · Billing │
├─────────────────────────────────────────────────┤
│  Layer 1: Foundation Infrastructure             │
│  PostgreSQL · Redis · ChromaDB · Ollama · Docker│
└─────────────────────────────────────────────────┘
```

## Data Flow: WhatsApp Message → Response

```
User (WhatsApp)
  │
  ▼
Gupshup Webhook → Nginx → Spring Boot Gateway
  │                           │
  │  1. Parse webhook         │
  │  2. Find/create user      │
  │  3. Create conversation   │
  │                           ▼
  │                  AI Service (FastAPI)
  │                     │
  │  4. STT (if audio)  │
  │  5. Load profile     │
  │  6. Load history     │
  │                      ▼
  │              Supervisor Agent
  │                 │
  │  7. Classify intent (keyword → LLM fallback)
  │                 │
  │      ┌──────────┼──────────┐
  │      ▼          ▼          ▼
  │   Scheme    Mandi      Loan/DPR
  │   Agent     Agent      Agent
  │      │          │          │
  │  8. Tools    Tools     Tools
  │  (ChromaDB)  (DB+ML)  (JSON rules)
  │      │          │          │
  │      └──────────┼──────────┘
  │                 ▼
  │  9. Format response (Hindi/English)
  │  10. Save context to Redis
  │  11. TTS (optional)
  │                 │
  │                 ▼
  │         ChatResponse
  │              │
  ▼              ▼
Gateway sends reply via Gupshup API
  │
  ▼
User sees reply on WhatsApp
```

## LLM Provider Fallback Chain

```
Ollama (self-hosted, free)
  │ fails?
  ▼
Gemini Flash (cheap API, ~$0.001/query)
  │ fails?
  ▼
Claude Sonnet (quality, ~$0.01/query)
```

- **Cheap tasks** (classification, price queries): Ollama → Gemini
- **Quality tasks** (legal notices, DPR narratives): Claude Sonnet

## Database Schema (Key Tables)

| Table | Purpose |
|-------|---------|
| users | User profiles (phone, location, category, occupation) |
| schemes | 50+ government schemes with eligibility JSONB |
| mandi_prices | Historical commodity prices (10 commodities × 15 markets) |
| disputes | MSME payment disputes under MSMED Act |
| conversations | Chat sessions with agent tracking |
| messages | Individual messages with tools/model used |
| price_alerts | User price alert subscriptions |
| project_reports | Generated DPRs with financial data |

## Technology Stack

| Component | Technology |
|-----------|-----------|
| API Gateway | Java 21 / Spring Boot 3.2.5 |
| AI Service | Python 3.11 / FastAPI |
| Agent Framework | LangGraph |
| LLM Providers | Ollama / Gemini Flash / Claude Sonnet |
| Vector DB | ChromaDB |
| Primary DB | PostgreSQL 16 |
| Cache/Sessions | Redis 7 |
| STT | OpenAI Whisper |
| TTS | Bhashini (Gov India) |
| OCR | PaddleOCR |
| Price Prediction | Facebook Prophet |
| WhatsApp | Gupshup Business API |
| Containerization | Docker Compose |
| Monitoring | Prometheus + Grafana |
