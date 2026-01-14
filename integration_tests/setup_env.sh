#!/bin/bash

# Helper script to set up environment variables for integration tests

echo "🔧 Aluvia SDK Integration Tests - Environment Setup"
echo ""

# Check if .env file exists
if [ -f "integration_test/.env" ]; then
    echo "✅ Found integration_test/.env file"
    echo "   Sourcing environment variables..."
    source integration_test/.env
else
    echo "⚠️  No .env file found at integration_test/.env"
    echo ""
    echo "Creating .env file from example..."
    cp integration_test/.env.example integration_test/.env
    echo "✅ Created integration_test/.env"
    echo ""
    echo "📝 Please edit integration_test/.env with your credentials:"
    echo "   - ALUVIA_API_KEY (required)"
    echo "   - ALUVIA_CONNECTION_ID (optional)"
    echo ""
    echo "Then run this script again or manually source it:"
    echo "   source integration_test/setup_env.sh"
    exit 0
fi

# Verify required variables are set
if [ -z "$ALUVIA_API_KEY" ]; then
    echo "❌ Error: ALUVIA_API_KEY is not set in .env file"
    exit 1
fi

echo "✅ Environment variables loaded:"
echo "   - ALUVIA_API_KEY: ${ALUVIA_API_KEY:0:20}..."

if [ -n "$ALUVIA_CONNECTION_ID" ]; then
    echo "   - ALUVIA_CONNECTION_ID: $ALUVIA_CONNECTION_ID"
else
    echo "   - ALUVIA_CONNECTION_ID: (not set - tests will create connections)"
fi

echo ""
echo "✅ Ready to run integration tests!"
echo ""
echo "Run tests with:"
echo "   ./integration_test/run_integration_tests.sh"
echo "   python integration_test/quick_test.py"
