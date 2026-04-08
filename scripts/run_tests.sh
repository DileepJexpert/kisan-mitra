#!/bin/bash
# Run all tests for KisanMitra platform
# Usage: ./scripts/run_tests.sh [python|java|all]

set -e

TARGET="${1:-all}"
EXIT_CODE=0

echo "============================================"
echo "KisanMitra — Test Runner"
echo "============================================"

run_python_tests() {
    echo ""
    echo "[Python] Running AI service tests..."
    cd services/ai-service
    if [ -f "requirements.txt" ]; then
        python -m pytest tests/ -v --tb=short 2>&1 || EXIT_CODE=1
    else
        echo "  No requirements.txt found. Skipping."
    fi
    cd ../..
}

run_java_tests() {
    echo ""
    echo "[Java] Running Gateway tests..."
    cd services/gateway
    if [ -f "pom.xml" ]; then
        mvn test -q 2>&1 || EXIT_CODE=1
    else
        echo "  No pom.xml found. Skipping."
    fi
    cd ../..
}

case $TARGET in
    python)
        run_python_tests
        ;;
    java)
        run_java_tests
        ;;
    all)
        run_python_tests
        run_java_tests
        ;;
    *)
        echo "Usage: $0 [python|java|all]"
        exit 1
        ;;
esac

echo ""
echo "============================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed. Check output above."
fi
echo "============================================"

exit $EXIT_CODE
