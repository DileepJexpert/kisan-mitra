# KisanMitra — Local Laptop Setup Guide (Testing & Debugging)

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| **Docker Desktop** | 4.x+ | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| **Java 21** | JDK 21 | `brew install openjdk@21` / `sdkman install java 21-tem` |
| **Python 3.11+** | 3.11+ | `brew install python@3.11` / python.org |
| **Maven 3.9+** | 3.9+ | `brew install maven` / comes with IntelliJ |
| **Git** | any | already installed |

---

## Step 1: Clone & Configure

```bash
git clone https://github.com/DileepJexpert/kisan-mitra.git
cd kisan-mitra
git checkout claude/kisanmitra-ai-platform-tdd-IFs8s

# Create .env from example
cp .env.example .env
```

Edit `.env` — only these 3 are **required** for basic testing:
```
DB_PASSWORD=password
JWT_SECRET=my-super-secret-key-for-dev-must-be-at-least-256-bits-long-enough
GEMINI_API_KEY=AIzaSy...   # free from https://aistudio.google.com/apikey
```

Optional (for full features):
```
CLAUDE_API_KEY=sk-ant-...  # for legal notices, DPR quality text
BHASHINI_API_KEY=...       # for Hindi TTS (free from bhashini.gov.in)
```

---

## Step 2: Start Infrastructure (Docker)

```bash
cd infra
docker compose up -d postgres redis chromadb
```

Wait ~10 seconds, verify:
```bash
docker compose ps                        # all should be "running (healthy)"
docker compose logs postgres | tail -5   # should say "ready to accept connections"
```

> **Note:** Skip Ollama for now if you don't have GPU — Gemini will be the fallback LLM.

---

## Step 3: Seed Database

```bash
cd ..   # back to project root

# Install Python dependencies (use a venv)
cd services/ai-service
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Go back to root and seed
cd ../..
python scripts/seed_all_data.py
```

This creates tables, loads 34 schemes, generates 365 days of mock mandi prices, and indexes into ChromaDB.

---

## Step 4: Run AI Service (Python)

```bash
cd services/ai-service
source venv/bin/activate

# Set env vars for local dev
export DB_URL=postgresql://admin:password@localhost:5432/kisanmitra
export REDIS_HOST=localhost
export CHROMA_HOST=http://localhost:8000
export GEMINI_API_KEY=AIzaSy...    # your key
export LOG_LEVEL=DEBUG

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Test it:
```bash
# Health check
curl http://localhost:8001/health

# Chat test
curl -X POST http://localhost:8001/ai/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user-001","message":"namaste","language":"hi"}'

# Mandi price
curl "http://localhost:8001/ai/v1/mandi/price?commodity=Tomato&market=Kanpur"

# Scheme search
curl -X POST http://localhost:8001/ai/v1/schemes/search \
  -H "Content-Type: application/json" \
  -d '{"query":"dairy farming subsidy"}'
```

---

## Step 5: Run Gateway (Java) — Optional for API testing

Open a **new terminal**:
```bash
cd services/gateway

# Set env vars
export DB_URL=jdbc:postgresql://localhost:5432/kisanmitra
export DB_USERNAME=admin
export DB_PASSWORD=password
export REDIS_HOST=localhost
export AI_SERVICE_URL=http://localhost:8001
export JWT_SECRET=my-super-secret-key-for-dev-must-be-at-least-256-bits-long-enough

# Build and run
mvn spring-boot:run
```

Test gateway:
```bash
# Send OTP
curl -X POST http://localhost:8080/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210"}'

# Test chat (bypasses WhatsApp)
curl -X POST http://localhost:8080/api/v1/test/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"mujhe loan chahiye dairy ke liye"}'
```

---

## Step 6: Interactive Demo (Easiest Way to Test)

```bash
# From project root, with AI service running
python scripts/demo_conversation.py --url http://localhost:8001
```

Type messages in Hindi/English or pick numbered scenarios:
1. **Scheme Discovery** — "main aam ka achaar banata hoon, koi scheme hai?"
2. **Mandi Price** — "tamatar ka rate kya hai kanpur mein?"
3. **Loan Query** — "dairy farm ke liye loan chahiye, 10 gaay"
4. **Dispute Filing** — "buyer ne 3.5 lakh nahi diye, 2 mahine ho gaye"
5. **DPR Generation** — "dairy farm ka DPR banao 10 cow ka"

---

## Debugging Tips

### Check Logs

```bash
# AI Service — running with --reload shows errors live in terminal

# Docker service logs
docker compose -f infra/docker-compose.yml logs -f postgres
docker compose -f infra/docker-compose.yml logs -f chromadb
docker compose -f infra/docker-compose.yml logs -f redis
```

### Database Inspection

```bash
# Connect to postgres
docker exec -it kisanmitra-postgres psql -U admin -d kisanmitra

# Useful queries
SELECT count(*) FROM mandi_prices;       -- should be ~46,000
SELECT count(*) FROM schemes;             -- should be 34
SELECT * FROM users LIMIT 5;
\dt                                       -- list all tables
\q                                        -- quit
```

### Redis Inspection

```bash
docker exec -it kisanmitra-redis redis-cli
KEYS *                    # list all keys
GET conv:test-user-001    # check conversation memory
TTL conv:test-user-001    # check TTL remaining
QUIT
```

### ChromaDB Check

```bash
curl http://localhost:8000/api/v1/collections
# Should show "schemes" and "loan_rules" collections
```

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `asyncpg.CannotConnectNow` | PostgreSQL not ready — wait 10s or `docker compose restart postgres` |
| `chromadb.errors.NotFoundError` | Run `python scripts/seed_all_data.py` to populate ChromaDB |
| `All LLM providers failed` | Set `GEMINI_API_KEY` in your env / terminal |
| `ModuleNotFoundError` | Activate venv: `source venv/bin/activate` |
| Maven build fails | Ensure Java 21: `java -version` |
| Port 5432 already in use | Stop local PostgreSQL: `brew services stop postgresql` or `sudo systemctl stop postgresql` |
| Port 8000 already in use | Stop other service on 8000, or change ChromaDB port in docker-compose |
| `ConnectionRefusedError` on Redis | `docker compose up -d redis` — ensure Redis container is running |
| Docker out of memory | Increase Docker Desktop memory to 4GB+ in Settings → Resources |
| Whisper model download slow | First STT call downloads ~1.5GB model — be patient or skip (see below) |

---

## Skip Heavy Dependencies (Faster Startup)

If you don't need OCR/STT/prediction locally, comment these out in `services/ai-service/requirements.txt`:

```
# paddleocr>=2.7.0          # ~2GB download (OCR)
# paddlepaddle>=2.6.0       # ~500MB (OCR dependency)
# openai-whisper>=20231117   # ~1GB model (Speech-to-Text)
# prophet>=1.1.5             # heavy install (Price prediction)
```

The app will still work — those features will return errors when called but won't crash other agents.

Reinstall after commenting:
```bash
cd services/ai-service
pip install -r requirements.txt
```

---

## What to Test First (In Order)

| # | Test | What it validates |
|---|------|-------------------|
| 1 | `curl http://localhost:8001/health` | DB, Redis, ChromaDB connections |
| 2 | Chat: `"namaste"` | Supervisor + general agent (LLM call) |
| 3 | Chat: `"tamatar ka bhav batao"` | Mandi agent (DB query, no LLM needed) |
| 4 | Chat: `"dairy ke liye koi scheme hai?"` | Scheme agent (ChromaDB RAG + LLM) |
| 5 | Chat: `"5 lakh ka loan chahiye"` | Loan agent (JSON rules, EMI calc) |
| 6 | `python scripts/demo_conversation.py` | All agents interactively |
| 7 | `curl .../mandi/price?commodity=Tomato&market=Kanpur` | Direct REST API |
| 8 | `curl .../predict/price?commodity=Tomato&market=Kanpur&days=7` | Price prediction |

---

## Full Docker Setup (Alternative — No Java/Python Install Needed)

If you prefer running everything in Docker (no local Java/Python):

```bash
cd infra
docker compose up -d          # starts ALL 7 services
# Wait 30-60 seconds for everything to start

# Seed data
docker compose exec ai-service python -c "
import subprocess
subprocess.run(['python', '/app/scripts/seed_all_data.py'])
"

# Test
curl http://localhost:8080/api/v1/test/chat \
  -X POST -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"namaste"}'
```

> **Downside:** No `--reload`, so you need to rebuild on code changes:
> `docker compose up -d --build ai-service`

---

## Project Structure Quick Reference

```
kisan-mitra/
├── services/
│   ├── ai-service/          # Python FastAPI — AI agents, tools, ML
│   │   ├── app/
│   │   │   ├── agents/      # LangGraph agents (scheme, mandi, loan, dispute, dpr, supervisor)
│   │   │   ├── tools/       # Agent tools (eligibility, EMI, interest, price prediction)
│   │   │   ├── models/      # LLM/STT/TTS/OCR provider abstraction
│   │   │   ├── routers/     # FastAPI endpoints (10 routers)
│   │   │   ├── db/          # Postgres, Redis, ChromaDB async clients
│   │   │   ├── middleware/   # Error handling
│   │   │   ├── main.py      # FastAPI app entry point
│   │   │   └── config.py    # Settings from .env
│   │   └── tests/           # Test suite
│   ├── gateway/             # Java Spring Boot — Auth, WhatsApp, notifications
│   │   └── src/main/java/com/kisanmitra/gateway/
│   │       ├── config/      # Security, JWT, Redis, rate limiting
│   │       ├── controller/  # Auth, Webhook, Test, User, Notification
│   │       ├── service/     # Auth, WhatsApp, AI client, Notification
│   │       ├── model/       # JPA entities
│   │       ├── dto/         # Request/Response DTOs
│   │       └── scheduler/   # Price alerts, deadline reminders
│   └── scraper/             # Python — Mandi price scraper, scheme loader
├── infra/
│   ├── docker-compose.yml       # Development
│   ├── docker-compose.prod.yml  # Production
│   ├── sql/                     # Database migrations
│   ├── nginx/                   # Reverse proxy configs
│   └── prometheus/              # Monitoring config
├── data/
│   ├── schemes/             # central_schemes.json (34 schemes)
│   ├── loan_rules/          # all_loans.json (11 loan products)
│   └── templates/           # DPR templates, legal notice templates
├── scripts/
│   ├── seed_all_data.py     # Master data seeding
│   ├── demo_conversation.py # Interactive terminal demo
│   ├── load_test.py         # Concurrent load testing
│   ├── deploy.sh            # Production deployment
│   └── backup.sh            # Database backup/restore
├── docs/                    # API.md, ARCHITECTURE.md, DEPLOYMENT.md
├── .env.example             # Environment template
└── .github/workflows/ci.yml # CI/CD pipeline
```
