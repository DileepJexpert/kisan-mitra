# KisanMitra AI Agent Platform

An AI-powered WhatsApp agent platform designed for Indian farmers. KisanMitra delivers real-time agricultural advisory, government scheme information, mandi prices, and weather alerts in local languages through conversational AI on WhatsApp.

## Architecture

```
                          KisanMitra AI Platform
  ============================================================

  +----------+     +------------------+     +------------------+
  |          |     |                  |     |                  |
  |  Farmer  +---->+    WhatsApp      +---->+   Spring Boot    |
  | (Mobile) |     |   (Gupshup)     |     |    Gateway       |
  |          |<----+                  |<----+   (Java 21)      |
  +----------+     +------------------+     +--------+---------+
                                                     |
                                                     v
                                            +--------+---------+
                                            |                  |
                                            |  FastAPI AI Svc  |
                                            |  (Python 3.11)   |
                                            |                  |
                                            +--------+---------+
                                                     |
                          +-------------+------------+------------+
                          |             |            |            |
                          v             v            v            v
                   +------+---+  +------+---+  +----+-----+  +--+-------+
                   | LangGraph|  |  Ollama  |  | ChromaDB |  | Scraper  |
                   |  Agents  |  | (Qwen3)  |  |  (RAG)   |  | Service  |
                   +----------+  +----------+  +----------+  +----------+
                     - Mandi                     Crop KB       Mandi prices
                     - Weather                   Schemes       Govt schemes
                     - Schemes                   Alerts        Weather data
                     - Advisory
```

## Tech Stack

| Layer          | Technology                                      |
|----------------|--------------------------------------------------|
| Gateway API    | Java 21, Spring Boot 3.x, Spring WebFlux         |
| AI Service     | Python 3.11+, FastAPI, LangGraph, LangChain      |
| LLM            | Ollama (Qwen3 7B), Claude API, Gemini API        |
| Vector Store   | ChromaDB                                         |
| Database       | PostgreSQL 16                                    |
| Cache          | Redis 7                                          |
| Translation    | Bhashini API, Sarvam AI                          |
| Messaging      | Gupshup (WhatsApp), MSG91 (SMS)                  |
| Payments       | Razorpay                                         |
| Scraping       | Python (BeautifulSoup, Scrapy)                   |
| Infrastructure | Docker, Docker Compose                           |

## Quick Start

### Prerequisites

- Java 21+
- Python 3.11+
- Docker and Docker Compose
- Maven 3.9+

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/kisan-mitra.git
cd kisan-mitra

# Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Edit .env with your actual credentials
nano .env

# Start infrastructure (PostgreSQL, Redis, ChromaDB, Ollama)
docker-compose up -d

# Start the Gateway (in a separate terminal)
cd services/gateway && mvn spring-boot:run

# Start the AI Service (in a separate terminal)
cd services/ai-service && uvicorn app.main:app --reload --port 8001
```

## Project Structure

```
kisan-mitra/
├── services/
│   ├── gateway/          # Spring Boot API gateway (Java 21)
│   ├── ai-service/       # FastAPI + LangGraph AI service (Python)
│   └── scraper/          # Data scraping service (Python)
├── infra/                # Docker Compose, Dockerfiles, Nginx config
├── data/                 # Seed data, SQL migrations, sample datasets
├── docs/                 # Architecture docs, API specs, runbooks
├── scripts/              # Setup, deployment, and utility scripts
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
├── LICENSE               # Apache 2.0
└── README.md             # This file
```

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

Copyright 2026 KisanMitra AI Platform.
