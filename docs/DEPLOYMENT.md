# KisanMitra — Deployment Guide

## Minimum Server Requirements
- **CPU**: 2 vCPU (4 recommended with Ollama)
- **RAM**: 4 GB minimum (8 GB recommended)
- **Disk**: 50 GB SSD
- **OS**: Ubuntu 22.04 LTS

## Quick Start (Local Development)

```bash
# 1. Clone
git clone https://github.com/DileepJexpert/kisan-mitra.git
cd kisan-mitra

# 2. Configure
cp .env.example .env
# Edit .env — set DB_PASSWORD, JWT_SECRET, API keys

# 3. Start infrastructure
cd infra && docker compose up -d postgres redis chromadb ollama

# 4. Wait for postgres, then seed data
cd .. && python scripts/seed_all_data.py

# 5. Start services (dev mode)
cd infra && docker compose up -d gateway ai-service scraper

# 6. Test
curl http://localhost:8080/api/v1/test/chat \
  -X POST -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"namaste"}'
```

## Production Deployment

### 1. Server Setup
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Clone project
git clone https://github.com/DileepJexpert/kisan-mitra.git
cd kisan-mitra
```

### 2. Configure Environment
```bash
cp .env.example .env
nano .env
```

Required variables:
```
DB_PASSWORD=<strong_password>
JWT_SECRET=<256_bit_random_string>
CLAUDE_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
GUPSHUP_API_KEY=<from_gupshup>
GUPSHUP_APP_NAME=KisanMitraBot
```

### 3. SSL Certificates (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy to nginx ssl dir
mkdir -p infra/nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem infra/nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem infra/nginx/ssl/

# Use prod nginx config
cp infra/nginx/nginx.prod.conf infra/nginx/nginx.conf
```

### 4. Deploy
```bash
./scripts/deploy.sh --build --seed
```

### 5. Download AI Models
```bash
# Ollama models (run once)
docker exec kisanmitra-ollama ollama pull qwen3:7b

# Whisper + PaddleOCR download on first use (automatic)
```

## Gupshup WhatsApp Setup

1. Create account at [gupshup.io](https://www.gupshup.io)
2. Create a WhatsApp Business App
3. Set webhook URL: `https://yourdomain.com/api/v1/webhook/whatsapp`
4. Copy API key and app name to `.env`
5. Set webhook verification token in Gupshup dashboard

## Monitoring

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Health**: http://localhost/health

## Backup

```bash
# Manual backup
./scripts/backup.sh

# Schedule daily backup (add to crontab)
0 2 * * * /path/to/kisan-mitra/scripts/backup.sh

# Restore from backup
./scripts/backup.sh --restore backups/kisanmitra_20260408.sql.gz
```

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Gateway won't start | Check DB_PASSWORD in .env matches postgres |
| AI service unhealthy | Check `docker logs kisanmitra-ai-service` |
| Ollama OOM | Reduce model size or increase RAM |
| Whisper slow | Use "medium" model instead of "large-v3" |
| ChromaDB errors | Check volume permissions: `docker volume inspect` |
