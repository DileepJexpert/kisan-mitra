# KisanMitra — System Architecture Diagram

High-level view of the 5-layer architecture, showing how services, data stores, and external integrations fit together.

## Layered Architecture

```mermaid
graph TB
    subgraph "External Actors"
        Farmer[Farmer / MSME<br/>WhatsApp User]
        Admin[Admin / Operator]
    end

    subgraph "Layer 1 — Edge / Channel"
        Gupshup[Gupshup WhatsApp<br/>Business API]
        Nginx[Nginx Reverse Proxy<br/>SSL / Rate Limiting]
    end

    subgraph "Layer 2 — Platform Services (Java)"
        Gateway[Spring Boot Gateway :8080]
        Auth[Auth Service<br/>JWT + OTP]
        Webhook[Webhook Controller<br/>Gupshup Inbound]
        Scheduler[Schedulers<br/>Price Alerts / Reminders]
        NotifSvc[Notification Service<br/>WhatsApp Outbound]
    end

    subgraph "Layer 3 — AI Services (Python FastAPI :8001)"
        ChatRouter[Chat Router]
        MandiRouter[Mandi Router]
        SchemesRouter[Schemes Router]
        LoansRouter[Loans Router]
        DisputesRouter[Disputes Router]
        DPRRouter[DPR Router]
        STTRouter[STT Router]
        TTSRouter[TTS Router]
        OCRRouter[OCR Router]
    end

    subgraph "Layer 4 — Agent Framework (LangGraph)"
        Supervisor[Supervisor Agent<br/>Intent Routing]
        SchemeAgent[Scheme Agent]
        MandiAgent[Mandi Agent]
        LoanAgent[Loan Agent]
        DisputeAgent[Dispute Agent]
        DPRAgent[DPR Agent]
        GeneralAgent[General Agent]
    end

    subgraph "Layer 5 — Tools & Models"
        LLMRouter[LLM Provider Router<br/>Ollama → Gemini → Claude]
        Tools[Domain Tools<br/>Eligibility / EMI / Interest /<br/>Price Prediction]
        Whisper[Whisper STT]
        Bhashini[Bhashini TTS]
        Paddle[PaddleOCR]
    end

    subgraph "Data Layer"
        Postgres[(PostgreSQL 16<br/>users, schemes,<br/>mandi_prices, disputes)]
        Redis[(Redis 7<br/>conversation memory<br/>rate limit, cache)]
        Chroma[(ChromaDB<br/>schemes + loan_rules<br/>vector index)]
    end

    subgraph "Scrapers"
        Scraper[Python Scraper<br/>data.gov.in / Agmarknet]
    end

    subgraph "Observability"
        Prometheus[Prometheus]
        Grafana[Grafana]
    end

    Farmer -- WhatsApp --> Gupshup
    Gupshup -- Webhook --> Nginx
    Admin -- HTTPS --> Nginx
    Nginx --> Gateway

    Gateway --> Auth
    Gateway --> Webhook
    Gateway --> NotifSvc
    Webhook --> ChatRouter
    Scheduler --> NotifSvc
    NotifSvc -- REST --> Gupshup

    Gateway --> Postgres
    Gateway --> Redis

    ChatRouter --> Supervisor
    MandiRouter --> MandiAgent
    SchemesRouter --> SchemeAgent
    LoansRouter --> LoanAgent
    DisputesRouter --> DisputeAgent
    DPRRouter --> DPRAgent

    Supervisor --> SchemeAgent
    Supervisor --> MandiAgent
    Supervisor --> LoanAgent
    Supervisor --> DisputeAgent
    Supervisor --> DPRAgent
    Supervisor --> GeneralAgent

    SchemeAgent --> LLMRouter
    MandiAgent --> LLMRouter
    LoanAgent --> LLMRouter
    DisputeAgent --> LLMRouter
    DPRAgent --> LLMRouter
    GeneralAgent --> LLMRouter

    SchemeAgent --> Tools
    LoanAgent --> Tools
    DisputeAgent --> Tools
    MandiAgent --> Tools

    STTRouter --> Whisper
    TTSRouter --> Bhashini
    OCRRouter --> Paddle

    SchemeAgent --> Chroma
    LoanAgent --> Chroma
    MandiAgent --> Postgres
    DisputeAgent --> Postgres

    Supervisor --> Redis
    ChatRouter --> Redis

    Scraper --> Postgres
    Scraper --> Chroma

    Gateway --> Prometheus
    ChatRouter --> Prometheus
    Prometheus --> Grafana
```

## Component Responsibilities

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| Edge | Nginx | SSL termination, rate limiting, blocks `/ai/` and `/metrics` externally |
| Edge | Gupshup | WhatsApp Business API transport |
| Platform | Spring Boot Gateway | Auth, webhook intake, outbound notifications, scheduled jobs |
| AI Routers | FastAPI | HTTP surface for each product (chat, mandi, schemes, loans, disputes, DPR, STT, TTS, OCR) |
| Agents | LangGraph | Supervisor routes intent to domain sub-agents |
| Tools | Python libs | EMI calc, MSMED interest, Prophet price prediction, eligibility checks |
| Models | Multi-provider | LLM fallback chain, Whisper STT, Bhashini TTS, PaddleOCR |
| Data | Postgres / Redis / Chroma | Transactional, cache / memory, vector search |
| Ops | Prometheus + Grafana | Metrics, dashboards, alerting |

## LLM Fallback Chain

```mermaid
flowchart LR
    Req[Agent LLM Request] --> Ollama{Ollama<br/>local?}
    Ollama -- ok --> Done[Return response]
    Ollama -- fail/timeout --> Gemini{Gemini Flash}
    Gemini -- ok --> Done
    Gemini -- fail --> Claude{Claude Sonnet}
    Claude -- ok --> Done
    Claude -- fail --> Err[LLMError → graceful fallback]
```

## Deployment Topology (Production)

```mermaid
graph LR
    subgraph "Internet"
        U[User]
    end
    subgraph "VPS / Cloud VM"
        direction TB
        NG[nginx :443]
        GW[gateway :8080]
        AI[ai-service :8001]
        PG[(postgres)]
        RD[(redis)]
        CH[(chromadb)]
        OL[ollama]
        PR[prometheus]
        GR[grafana]
    end
    U --> NG
    NG --> GW
    GW --> AI
    GW --> PG
    GW --> RD
    AI --> PG
    AI --> RD
    AI --> CH
    AI --> OL
    GW --> PR
    AI --> PR
    PR --> GR
```
