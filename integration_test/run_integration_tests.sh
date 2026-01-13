#!/bin/bash

# Run all integration tests for Aluvia SDK

echo "=========================================="
echo "  Aluvia SDK Integration Tests"
echo "=========================================="
echo ""

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   python3 -m venv .venv"
    echo "   .venv/bin/pip install -e ."
    exit 1
fi

PYTHON=".venv/bin/python"

# Run API integration tests
echo "🧪 Running API Integration Tests..."
echo ""
$PYTHON integration_test/integration_api_test.py
API_RESULT=$?
echo ""

# Run SDK integration tests
echo "🧪 Running SDK Integration Tests..."
echo ""
$PYTHON integration_test/integration_sdk_test.py
SDK_RESULT=$?
echo ""

# Run complete workflow test
echo "🧪 Running Complete Workflow Test..."
echo ""
$PYTHON integration_test/integration_full_workflow.py
WORKFLOW_RESULT=$?
echo ""

# Summary
echo "=========================================="
echo "  Test Results Summary"
echo "=========================================="
echo ""

if [ $API_RESULT -eq 0 ]; then
    echo "✅ API Integration Tests: PASSED"
else
    echo "❌ API Integration Tests: FAILED (exit code: $API_RESULT)"
fi

if [ $SDK_RESULT -eq 0 ]; then
    echo "✅ SDK Integration Tests: PASSED"
else
    echo "❌ SDK Integration Tests: FAILED (exit code: $SDK_RESULT)"
fi

if [ $WORKFLOW_RESULT -eq 0 ]; then
    echo "✅ Complete Workflow Test: PASSED"
else
    echo "❌ Complete Workflow Test: FAILED (exit code: $WORKFLOW_RESULT)"
fi

echo ""

# Exit with non-zero if any test failed
if [ $API_RESULT -ne 0 ] || [ $SDK_RESULT -ne 0 ] || [ $WORKFLOW_RESULT -ne 0 ]; then
    echo "❌ Some tests failed"
    exit 1
else
    echo "✅ All integration tests passed!"
    exit 0
fi
