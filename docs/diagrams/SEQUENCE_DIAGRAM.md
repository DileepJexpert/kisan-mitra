# KisanMitra — Sequence Diagrams

Temporal interactions between components for the most important scenarios. All diagrams use Mermaid and render directly on GitHub.

---

## 1. WhatsApp Text Query — Full Path

Scenario: Farmer sends *"dairy ke liye koi scheme hai?"* via WhatsApp.

```mermaid
sequenceDiagram
    autonumber
    actor F as Farmer
    participant G as Gupshup
    participant N as Nginx
    participant GW as Gateway (Java)
    participant AI as AI Service (FastAPI)
    participant SV as Supervisor
    participant RD as Redis
    participant SA as Scheme Agent
    participant CH as ChromaDB
    participant LLM as LLM Router
    participant PG as Postgres

    F->>G: Send text message
    G->>N: POST /webhook/whatsapp (HMAC signed)
    N->>GW: forward (rate limit check)
    GW->>GW: Verify signature
    GW->>PG: Insert inbound_message
    GW->>AI: POST /ai/v1/agent/chat<br/>{user_id, message, language}
    AI->>SV: process_message()
    SV->>RD: GET conv:{user_id}
    RD-->>SV: last 10 turns
    SV->>LLM: classify intent
    LLM-->>SV: intent=scheme_discovery
    SV->>SA: invoke(state)
    SA->>CH: vector_search(query, k=5, collection=schemes)
    CH-->>SA: top-5 schemes w/ scores
    SA->>PG: fetch user profile (land, income, sector)
    PG-->>SA: profile
    SA->>SA: eligibility_tool(profile, schemes)
    SA->>LLM: summarize in Hindi
    LLM-->>SA: reply_text
    SA-->>SV: {reply_text, agent=scheme}
    SV->>RD: RPUSH conv:{user_id} user+assistant turns
    SV->>RD: LTRIM -20 -1 / EXPIRE 86400
    SV-->>AI: response
    AI-->>GW: 200 {reply_text}
    GW->>GW: NotificationService.send()
    GW->>G: POST https://api.gupshup.io/wa/api/v1/msg
    G->>F: Deliver WhatsApp reply
    GW->>PG: Insert outbound_message
```

---

## 2. Voice Message — STT → Agent → TTS

Scenario: Farmer sends a 12-second Hindi voice note asking for tomato price.

```mermaid
sequenceDiagram
    autonumber
    actor F as Farmer
    participant G as Gupshup
    participant GW as Gateway
    participant AI as AI Service
    participant STT as STT Router
    participant W as Whisper
    participant SV as Supervisor
    participant MA as Mandi Agent
    participant PG as Postgres
    participant TTS as TTS Router
    participant B as Bhashini

    F->>G: Send voice note (OGG Opus)
    G->>GW: Webhook with media_url
    GW->>G: GET media_url (download ogg bytes)
    G-->>GW: audio bytes
    GW->>AI: POST /ai/v1/agent/chat<br/>{audio_base64, language=hi}
    AI->>SV: process_message(audio_base64)
    SV->>STT: transcribe(audio, "hi")
    STT->>STT: ffmpeg ogg→wav 16kHz mono
    STT->>W: load model (cached)
    STT->>W: transcribe(wav, language=hi)
    W-->>STT: "tamatar ka bhav kanpur mein"
    STT-->>SV: {text, language, duration}
    SV->>SV: classify intent = mandi
    SV->>MA: invoke(state)
    MA->>PG: SELECT price WHERE commodity='Tomato' AND market='Kanpur'
    PG-->>MA: latest row + 7-day avg
    MA->>MA: price_prediction_tool(history)
    MA-->>SV: reply_text (Hindi)
    SV->>TTS: speak(reply_text, "hi", voice=female)
    TTS->>B: POST /services/inference (TTS)
    B-->>TTS: wav bytes
    TTS-->>SV: audio bytes
    SV-->>AI: {reply_text, reply_audio_base64}
    AI-->>GW: 200
    GW->>G: Send audio message
    G->>F: Farmer hears reply
```

---

## 3. Authentication — Phone OTP Login

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant GW as Gateway
    participant RD as Redis
    participant M as MSG91
    participant PG as Postgres

    U->>GW: POST /api/v1/auth/send-otp {phone}
    GW->>GW: Generate 6-digit OTP
    GW->>RD: SET otp:{phone} {otp} EX 300
    GW->>M: POST sendOtp
    M-->>U: SMS with OTP
    GW-->>U: 200 {message: "OTP sent"}

    U->>GW: POST /api/v1/auth/verify-otp {phone, otp}
    GW->>RD: GET otp:{phone}
    RD-->>GW: stored otp
    GW->>GW: constant-time compare
    alt OTP matches
        GW->>PG: SELECT user WHERE phone=?
        alt existing
            PG-->>GW: user row
        else new
            GW->>PG: INSERT user
            PG-->>GW: new user
        end
        GW->>GW: issue JWT (15m) + refresh (7d)
        GW->>RD: SET refresh:{user_id} {token} EX 604800
        GW-->>U: 200 {access_token, refresh_token, user}
    else mismatch
        GW-->>U: 401 Invalid OTP
    end
```

---

## 4. Dispute Filing with MSMED Interest

```mermaid
sequenceDiagram
    autonumber
    actor U as MSME Owner
    participant GW as Gateway
    participant AI as AI Service
    participant SV as Supervisor
    participant DA as Dispute Agent
    participant IT as Interest Tool
    participant LLM as Claude Sonnet
    participant FPDF as fpdf2
    participant PG as Postgres

    U->>GW: "buyer ne 3.5 lakh nahi diye, 60 din ho gaye"
    GW->>AI: /ai/v1/agent/chat
    AI->>SV: process_message
    SV->>DA: invoke(state, intent=dispute)
    DA->>DA: parse {amount=350000, days=60, buyer=?}
    DA->>U: ask "buyer ka naam aur address?"
    U-->>DA: provides details
    DA->>IT: calc_msmed_interest(350000, 60 days, rbi_rate=6.5%)
    Note over IT: Rate = 3 × RBI = 19.5% p.a.<br/>Monthly compound
    IT-->>DA: {interest: 11543, total: 361543}
    DA->>LLM: draft legal notice (Section 15/16 MSMED Act)
    LLM-->>DA: Hindi + English text
    DA->>FPDF: render notice PDF
    FPDF-->>DA: pdf bytes
    DA->>PG: INSERT dispute row (status=draft)
    PG-->>DA: dispute_id
    DA-->>SV: {reply, pdf_url, dispute_id}
    SV-->>AI: response
    AI-->>GW: 200
    GW->>U: WhatsApp message with PDF attachment
```

---

## 5. Scheduled Price Alert Job

```mermaid
sequenceDiagram
    autonumber
    participant CR as Cron (Scheduler)
    participant GW as Gateway
    participant PG as Postgres
    participant AI as AI Service
    participant PRED as Prophet Predictor
    participant G as Gupshup
    actor U as Farmer

    CR->>GW: PriceAlertScheduler.run() @ 7am IST
    GW->>PG: SELECT users WHERE alerts_enabled=true
    PG-->>GW: list of users with subscribed commodities
    loop for each user-commodity pair
        GW->>AI: GET /ai/v1/mandi/price?commodity=X&market=Y
        AI->>PG: latest + history
        PG-->>AI: rows
        AI->>PRED: predict next 3 days
        PRED-->>AI: forecast
        AI-->>GW: {today, change_pct, trend, advice}
        alt abs(change_pct) > 5%
            GW->>G: Send alert "Tomato +8% in Kanpur, sell now"
            G->>U: Push notification
        end
    end
    GW->>PG: Log alert_sent entries
```

---

## 6. LLM Fallback on Provider Failure

```mermaid
sequenceDiagram
    autonumber
    participant AG as Scheme Agent
    participant RT as LLM Router
    participant OL as Ollama
    participant GM as Gemini Flash
    participant CL as Claude Sonnet

    AG->>RT: generate(prompt, temperature=0.3)
    RT->>OL: POST /api/generate
    OL-->>RT: ConnectionError
    Note right of RT: primary failed
    RT->>GM: generate_content
    GM-->>RT: 429 quota exceeded
    Note right of RT: secondary failed
    RT->>CL: messages.create
    CL-->>RT: 200 {content}
    RT-->>AG: response
    Note over RT: Emit metric<br/>llm_fallback_used{tier=claude}
```

---

## 7. Conversation Memory (Follow-up Context)

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant SV as Supervisor
    participant RD as Redis
    participant LA as Loan Agent
    participant LLM as LLM Router

    U->>SV: "5 lakh ka dairy loan chahiye"
    SV->>RD: GET conv:{user_id}
    RD-->>SV: [] (empty)
    SV->>LA: invoke
    LA-->>SV: "NABARD @ 10%, EMI 10,624..."
    SV->>RD: RPUSH user+assistant turn
    SV-->>U: reply

    U->>SV: "aur kitna time lagta hai?"
    SV->>RD: GET conv:{user_id}
    RD-->>SV: [prev loan turn]
    SV->>LLM: classify with history
    LLM-->>SV: intent=loan (follow-up), topic=processing_time
    SV->>LA: invoke(state + history)
    LA-->>SV: "NABARD dairy loan 15-30 din mein..."
    SV->>RD: RPUSH again, LTRIM -20 -1
    SV-->>U: contextual reply
```

---

## 8. Health Check Sequence

```mermaid
sequenceDiagram
    participant M as Monitor / curl
    participant AI as AI Service
    participant PG as Postgres
    participant RD as Redis
    participant CH as ChromaDB

    M->>AI: GET /health
    par parallel probes
        AI->>PG: SELECT 1
        PG-->>AI: ok
    and
        AI->>RD: PING
        RD-->>AI: PONG
    and
        AI->>CH: GET /api/v1/heartbeat
        CH-->>AI: ok
    end
    AI-->>M: 200 {status: healthy, deps: {...}}
```

---

## Notes

- All sequences assume the Gateway has already authenticated the request (JWT or HMAC webhook signature).
- Timeouts: AI Service HTTP timeout = 30s, LLM per-provider timeout = 15s, STT = 20s, TTS = 10s.
- Every agent turn emits structured logs with `trace_id` for correlation across services.
- Prometheus metrics: `agent_latency_seconds{agent=...}`, `llm_provider_requests_total{provider=...,status=...}`, `webhook_inbound_total`.
