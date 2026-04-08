#!/bin/bash
# KisanMitra Production Deployment Script
# Usage: ./scripts/deploy.sh [--build] [--seed]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker-compose.prod.yml"
ENV_FILE="$PROJECT_ROOT/.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[DEPLOY]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Parse args
BUILD=false
SEED=false
for arg in "$@"; do
    case $arg in
        --build) BUILD=true ;;
        --seed) SEED=true ;;
        --help) echo "Usage: $0 [--build] [--seed]"; exit 0 ;;
    esac
done

# Check prerequisites
log "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || error "Docker not installed"
command -v docker compose >/dev/null 2>&1 || error "Docker Compose not installed"

if [ ! -f "$ENV_FILE" ]; then
    error ".env file not found. Copy .env.example and fill in values:\n  cp .env.example .env"
fi

# Verify critical env vars
source "$ENV_FILE"
[ -z "${DB_PASSWORD:-}" ] && error "DB_PASSWORD not set in .env"
[ -z "${JWT_SECRET:-}" ] && error "JWT_SECRET not set in .env"

log "Environment validated."

# Pull latest code
log "Pulling latest code..."
cd "$PROJECT_ROOT"
git pull origin "$(git branch --show-current)" || warn "Git pull failed — continuing with local code"

# Build if requested
if [ "$BUILD" = true ]; then
    log "Building Docker images..."
    docker compose -f "$COMPOSE_FILE" build --parallel
fi

# Start infrastructure services first
log "Starting infrastructure (postgres, redis, chromadb, ollama)..."
docker compose -f "$COMPOSE_FILE" up -d postgres redis chromadb ollama

# Wait for postgres
log "Waiting for PostgreSQL to be healthy..."
for i in $(seq 1 30); do
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U admin -d kisanmitra >/dev/null 2>&1; then
        log "PostgreSQL is ready."
        break
    fi
    [ "$i" -eq 30 ] && error "PostgreSQL failed to start in 30 seconds"
    sleep 1
done

# Run seed data if requested
if [ "$SEED" = true ]; then
    log "Running data seeding..."
    docker compose -f "$COMPOSE_FILE" run --rm ai-service python -m scripts.seed_all_data || warn "Seeding had errors (may be OK if data exists)"
fi

# Start application services
log "Starting application services..."
docker compose -f "$COMPOSE_FILE" up -d gateway ai-service scraper

# Start monitoring
log "Starting monitoring services..."
docker compose -f "$COMPOSE_FILE" up -d prometheus grafana nginx

# Wait and health check
log "Waiting for services to start..."
sleep 10

log "Running health checks..."
HEALTH_OK=true

# Gateway health
if curl -sf http://localhost:8080/actuator/health >/dev/null 2>&1; then
    log "  Gateway: HEALTHY"
else
    warn "  Gateway: NOT READY (may still be starting)"
    HEALTH_OK=false
fi

# AI Service health
if curl -sf http://localhost:8001/health >/dev/null 2>&1; then
    log "  AI Service: HEALTHY"
else
    warn "  AI Service: NOT READY (may still be starting)"
    HEALTH_OK=false
fi

# Nginx
if curl -sf http://localhost/ >/dev/null 2>&1; then
    log "  Nginx: HEALTHY"
else
    warn "  Nginx: NOT READY"
    HEALTH_OK=false
fi

echo ""
if [ "$HEALTH_OK" = true ]; then
    log "Deployment successful!"
else
    warn "Some services are still starting. Check: docker compose -f $COMPOSE_FILE ps"
fi

echo ""
log "Service URLs:"
log "  API Gateway:  http://localhost:8080"
log "  AI Service:   http://localhost:8001"
log "  Nginx (prod): http://localhost"
log "  Grafana:      http://localhost:3000"
log ""
log "Test: curl http://localhost:8080/api/v1/test/chat -X POST -H 'Content-Type: application/json' -d '{\"user_id\":\"test\",\"message\":\"namaste\"}'"
