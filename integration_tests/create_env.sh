#!/bin/bash

# Quick setup script - creates .env file with your credentials

cat > integration_test/.env << 'EOF'
# Aluvia SDK Integration Tests - Environment Variables
ALUVIA_API_KEY=YOUR_API_KEY
ALUVIA_CONNECTION_ID=YOUR_CONNECTION_ID
EOF

echo "✅ Created integration_test/.env with your credentials"
echo ""
echo "Now you can run tests:"
echo "  source integration_test/.env"
echo "  ./integration_test/run_integration_tests.sh"
