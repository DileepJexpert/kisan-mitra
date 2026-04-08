#!/bin/bash
# =============================================================================
# KisanMitra AI Platform - Development Environment Setup
# =============================================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "============================================="
echo " KisanMitra AI Platform - Setup"
echo "============================================="
echo ""

# -------------------------------------------------------
# 1. Check prerequisites
# -------------------------------------------------------
echo "Checking prerequisites..."
MISSING=0

# Java 21
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n1 | sed 's/.*"\([0-9]*\).*/\1/')
    if [ "$JAVA_VERSION" -ge 21 ] 2>/dev/null; then
        echo -e "  ${GREEN}[OK]${NC} Java $JAVA_VERSION"
    else
        echo -e "  ${RED}[MISSING]${NC} Java 21+ required (found Java $JAVA_VERSION)"
        MISSING=1
    fi
else
    echo -e "  ${RED}[MISSING]${NC} Java 21+ is not installed"
    MISSING=1
fi

# Python 3.11+
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | sed 's/Python //')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ] 2>/dev/null; then
        echo -e "  ${GREEN}[OK]${NC} Python $PY_VERSION"
    else
        echo -e "  ${RED}[MISSING]${NC} Python 3.11+ required (found Python $PY_VERSION)"
        MISSING=1
    fi
else
    echo -e "  ${RED}[MISSING]${NC} Python 3.11+ is not installed"
    MISSING=1
fi

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version 2>&1 | sed 's/Docker version \([^,]*\).*/\1/')
    echo -e "  ${GREEN}[OK]${NC} Docker $DOCKER_VERSION"
else
    echo -e "  ${RED}[MISSING]${NC} Docker is not installed"
    MISSING=1
fi

# Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo -e "  ${GREEN}[OK]${NC} Docker Compose"
else
    echo -e "  ${RED}[MISSING]${NC} Docker Compose is not installed"
    MISSING=1
fi

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}WARNING: Some prerequisites are missing. The setup may not complete successfully.${NC}"
    echo "Please install the missing tools and re-run this script."
    echo ""
    read -p "Continue anyway? (y/N): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "Setup aborted."
        exit 1
    fi
fi

echo ""

# -------------------------------------------------------
# 2. Copy .env.example to .env if .env doesn't exist
# -------------------------------------------------------
echo "Configuring environment..."
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    echo -e "  ${GREEN}[OK]${NC} Created .env from .env.example"
    echo -e "  ${YELLOW}[NOTE]${NC} Edit .env with your actual credentials before running services"
else
    echo -e "  ${GREEN}[OK]${NC} .env already exists, skipping"
fi

echo ""

# -------------------------------------------------------
# 3. Build Java Gateway Service
# -------------------------------------------------------
echo "Building Java Gateway Service..."
if [ -f "$PROJECT_ROOT/services/gateway/pom.xml" ]; then
    cd "$PROJECT_ROOT/services/gateway" && mvn clean install -DskipTests
    echo -e "  ${GREEN}[OK]${NC} Gateway service built successfully"
else
    echo -e "  ${YELLOW}[SKIP]${NC} services/gateway/pom.xml not found"
fi

echo ""

# -------------------------------------------------------
# 4. Install Python dependencies for AI Service
# -------------------------------------------------------
echo "Installing Python dependencies for AI Service..."
if [ -f "$PROJECT_ROOT/services/ai-service/requirements.txt" ]; then
    cd "$PROJECT_ROOT/services/ai-service" && pip install -r requirements.txt
    echo -e "  ${GREEN}[OK]${NC} AI Service dependencies installed"
else
    echo -e "  ${YELLOW}[SKIP]${NC} services/ai-service/requirements.txt not found"
fi

echo ""

# -------------------------------------------------------
# 5. Install Python dependencies for Scraper Service
# -------------------------------------------------------
echo "Installing Python dependencies for Scraper Service..."
if [ -f "$PROJECT_ROOT/services/scraper/requirements.txt" ]; then
    cd "$PROJECT_ROOT/services/scraper" && pip install -r requirements.txt
    echo -e "  ${GREEN}[OK]${NC} Scraper Service dependencies installed"
else
    echo -e "  ${YELLOW}[SKIP]${NC} services/scraper/requirements.txt not found"
fi

echo ""

# -------------------------------------------------------
# Done
# -------------------------------------------------------
echo "============================================="
echo -e " ${GREEN}Setup Complete!${NC}"
echo "============================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your actual credentials"
echo "  2. Start infrastructure services:"
echo "       docker-compose up -d"
echo "  3. Start the Gateway:"
echo "       cd services/gateway && mvn spring-boot:run"
echo "  4. Start the AI Service:"
echo "       cd services/ai-service && uvicorn app.main:app --reload --port 8001"
echo ""
echo "Documentation: see README.md"
echo ""
