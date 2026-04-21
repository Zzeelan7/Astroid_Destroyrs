#!/bin/bash
# run-tests.sh - Run all unit tests

echo "🧪 Running GridCharge Test Suite..."
echo "===================================="

cd backend

# Run pytest with coverage
pytest tests/ -v --cov=app --cov-report=html

echo ""
echo "✅ Tests complete! Coverage report: htmlcov/index.html"
