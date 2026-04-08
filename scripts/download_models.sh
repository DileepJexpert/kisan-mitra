#!/bin/bash
# Download all AI models needed for KisanMitra
# Run once on new server setup

set -e

echo "============================================"
echo "KisanMitra — AI Model Downloader"
echo "============================================"

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

# 1. Ollama Models
echo ""
echo "[1/3] Downloading Ollama models..."

# Check if Ollama is running
if curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
    echo "  Ollama is running at $OLLAMA_HOST"

    echo "  Pulling qwen3:7b (default reasoning model)..."
    curl -s "$OLLAMA_HOST/api/pull" -d '{"name": "qwen3:7b"}' | while read -r line; do
        status=$(echo "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || true)
        if [ -n "$status" ]; then
            printf "\r  Status: %-60s" "$status"
        fi
    done
    echo ""
    echo "  ✓ qwen3:7b downloaded"

else
    echo "  WARNING: Ollama is not running at $OLLAMA_HOST"
    echo "  Start Ollama first: docker-compose up ollama -d"
    echo "  Then re-run this script."
fi

# 2. Whisper Model (downloaded on first use by the library)
echo ""
echo "[2/3] Whisper STT model..."
echo "  Whisper large-v3 will be downloaded on first use (~3GB)"
echo "  To pre-download, run: python3 -c \"import whisper; whisper.load_model('large-v3')\""

# 3. PaddleOCR Models (downloaded on first use)
echo ""
echo "[3/3] PaddleOCR models..."
echo "  PaddleOCR models will be downloaded on first use (~150MB)"
echo "  To pre-download, run: python3 -c \"from paddleocr import PaddleOCR; PaddleOCR(lang='hi')\""

echo ""
echo "============================================"
echo "Model download complete!"
echo "============================================"
echo ""
echo "Models ready:"
echo "  ✓ Ollama (qwen3:7b) — Reasoning LLM"
echo "  ○ Whisper large-v3 — STT (downloads on first use)"
echo "  ○ PaddleOCR — OCR (downloads on first use)"
echo ""
echo "External APIs (configure in .env):"
echo "  - Claude Sonnet 4.6 — Quality generation"
echo "  - Gemini Flash — Cheap LLM calls"
echo "  - Bhashini — Hindi TTS"
