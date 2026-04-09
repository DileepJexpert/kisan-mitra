# KisanMitra — Data Flow Diagrams

End-to-end flows for the main use cases. Each diagram traces a request from the farmer's phone to the reply.

---

## 1. Inbound WhatsApp Text Message (High-Level)

```mermaid
flowchart TD
    A[Farmer types message<br/>on WhatsApp] --> B[Gupshup Business API]
    B -- POST webhook --> C[Nginx :443]
    C --> D[Gateway<br/>WebhookController]
    D --> E{Signature<br/>valid?}
    E -- no --> X[401 Unauthorized]
    E -- yes --> F[Persist inbound_message]
    F --> G[AIClient.chat POST /ai/v1/agent/chat]
    G --> H[AI Service<br/>ChatRouter]
    H --> I[Supervisor.process_message]
    I --> J[Load conversation history<br/>from Redis]
    J --> K{Intent<br/>classifier}
    K -- scheme --> L1[Scheme Agent]
    K -- mandi --> L2[Mandi Agent]
    K -- loan --> L3[Loan Agent]
    K -- dispute --> L4[Dispute Agent]
    K -- dpr --> L5[DPR Agent]
    K -- smalltalk --> L6[General Agent]
    L1 --> M[Tool calls<br/>+ LLM]
    L2 --> M
    L3 --> M
    L4 --> M
    L5 --> M
    L6 --> M
    M --> N[Save turn to Redis<br/>ltrim 20, ttl 24h]
    N --> O[Response JSON<br/>reply_text + audio]
    O --> P[Gateway NotificationService]
    P -- send --> Q[Gupshup]
    Q --> R[Farmer receives reply]
```

---

## 2. Voice Message Flow (WhatsApp Audio → Transcribe → Reply)

```mermaid
flowchart LR
    A[Farmer sends<br/>voice note OGG] --> B[Gupshup]
    B -- media_url --> C[Gateway]
    C -- download ogg --> D[AIClient]
    D -- audio_base64 --> E[ChatRouter]
    E --> F[Supervisor]
    F --> G[STT Router]
    G --> H{ffmpeg<br/>ogg→wav}
    H --> I[Whisper<br/>hi-IN transcribe]
    I -- text --> F
    F --> J[Agent processing]
    J --> K[Reply text]
    K --> L[TTS Router<br/>Bhashini hi-IN]
    L -- wav --> M[Base64 audio]
    M --> C
    C -- send audio --> B
    B --> N[Farmer hears reply]
```

---

## 3. Scheme Discovery (RAG Flow)

```mermaid
flowchart TD
    Q[User: mujhe dairy ke liye<br/>koi scheme hai?] --> S[Supervisor]
    S --> SA[Scheme Agent]
    SA --> E1[Extract entities:<br/>sector=dairy, user=farmer]
    E1 --> V[ChromaDB<br/>vector similarity search<br/>collection=schemes]
    V --> TOP[Top-5 candidate schemes]
    TOP --> EL[Eligibility Tool<br/>matches user profile]
    EL --> F[Filtered list]
    F --> LLM[LLM Router<br/>Ollama / Gemini / Claude]
    LLM --> HN[Hindi summary<br/>with subsidy %, deadline,<br/>apply link]
    HN --> R[Reply JSON]
    R --> U[User]
```

---

## 4. Mandi Price Query

```mermaid
flowchart LR
    U[tamatar ka rate<br/>kanpur mein?] --> S[Supervisor]
    S --> MA[Mandi Agent]
    MA --> PE[Parse: commodity=Tomato<br/>market=Kanpur]
    PE --> DB[(Postgres<br/>mandi_prices)]
    DB --> LP[Latest + 7-day avg]
    LP --> PP[Prophet predictor<br/>next-7-day forecast]
    PP --> FMT[Format Hindi reply:<br/>aaj ka bhav, trend,<br/>sell/hold advice]
    FMT --> U2[User]
```

---

## 5. Loan Eligibility + EMI

```mermaid
flowchart TD
    U[5 lakh dairy loan<br/>chahiye] --> S[Supervisor]
    S --> LA[Loan Agent]
    LA --> C[ChromaDB<br/>loan_rules]
    C --> R[Matching products<br/>NABARD / KCC / PMFME]
    R --> ET[Eligibility tool<br/>land, income, cibil]
    ET --> EMI[EMI tool<br/>P*R*(1+R)^N / ((1+R)^N-1)]
    EMI --> L[LLM formats<br/>comparison table]
    L --> U2[Reply with<br/>best 2-3 options]
```

---

## 6. Dispute Filing (MSMED Act Section 15/16)

```mermaid
flowchart TD
    U[buyer ne 3.5 lakh<br/>nahi diye, 2 mahine] --> S[Supervisor]
    S --> DA[Dispute Agent]
    DA --> P[Parse amount, days,<br/>buyer info]
    P --> INT[Interest Tool<br/>3x RBI rate, monthly<br/>compound]
    INT --> CALC[Principal + interest =<br/>total claim]
    CALC --> TMP[Legal notice template<br/>Section 15/16 MSMED]
    TMP --> LLM[Claude Sonnet<br/>draft Hindi/English notice]
    LLM --> PDF[fpdf2 PDF<br/>generation]
    PDF --> DB[(Postgres<br/>disputes table)]
    DB --> R[Reply with PDF link<br/>+ next steps]
    R --> U2[User]
```

---

## 7. DPR Generation (Detailed Project Report)

```mermaid
flowchart TD
    U[dairy farm ka DPR<br/>banao 10 cow ka] --> S[Supervisor]
    S --> DPR[DPR Agent]
    DPR --> T[Template loader<br/>data/templates/dairy]
    T --> Q{Missing<br/>fields?}
    Q -- yes --> ASK[Ask follow-up<br/>store context in Redis]
    ASK --> U2[User replies]
    U2 --> DPR
    Q -- no --> CALC[Financial calcs:<br/>capex, opex, IRR, NPV]
    CALC --> LLM[Claude Sonnet<br/>narrative sections]
    LLM --> PDF[fpdf2 multi-page PDF]
    PDF --> UP[Upload to /tmp<br/>return signed URL]
    UP --> U3[User receives PDF]
```

---

## 8. LLM Provider Fallback

```mermaid
flowchart LR
    A[Agent prompt] --> B{Ollama<br/>reachable?}
    B -- yes --> B1[llama3:8b]
    B1 -- ok --> Z[Response]
    B1 -- error/timeout --> C
    B -- no --> C{Gemini<br/>API key set?}
    C -- yes --> C1[gemini-1.5-flash]
    C1 -- ok --> Z
    C1 -- quota/error --> D
    C -- no --> D{Claude<br/>API key set?}
    D -- yes --> D1[claude-sonnet-4-6]
    D1 -- ok --> Z
    D1 -- error --> E[LLMError]
    D -- no --> E
    E --> F[Graceful fallback:<br/>cached answer OR<br/>I'm having trouble,<br/>please try again]
```

---

## 9. Data Ingestion (Background)

```mermaid
flowchart LR
    subgraph "Daily Cron"
        CR[cron 6am IST]
    end
    CR --> SC[Scraper]
    SC --> AG[data.gov.in /<br/>Agmarknet API]
    AG --> PG[(postgres<br/>mandi_prices)]
    SC2[Scheme loader] --> JSON[central_schemes.json]
    JSON --> PG
    JSON --> EMB[sentence-transformer<br/>embeddings]
    EMB --> CH[(ChromaDB<br/>schemes collection)]
    LR[loan_rules.json] --> EMB2[embeddings]
    EMB2 --> CH
```

---

## Key Latency Budgets

| Step | Target p95 |
|------|-----------|
| Nginx → Gateway | < 20 ms |
| Gateway → AI Service | < 50 ms |
| Redis memory read | < 10 ms |
| ChromaDB vector search | < 150 ms |
| Postgres query | < 50 ms |
| LLM (Ollama local) | < 2 s |
| LLM (Gemini Flash) | < 1.5 s |
| Whisper STT (15 s audio) | < 3 s |
| Bhashini TTS | < 1 s |
| **End-to-end text reply** | **< 3 s** |
| **End-to-end voice reply** | **< 6 s** |
