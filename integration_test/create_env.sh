#!/bin/bash

# Quick setup script - creates .env file with your credentials

cat > integration_test/.env << 'EOF'
# Aluvia SDK Integration Tests - Environment Variables
ALUVIA_API_KEY=97d13ab4022a0f9751dea41efeb81c1f22c41c8091f24ebab0de6b8f0b46c1b4
ALUVIA_CONNECTION_ID=1850
EOF

echo "✅ Created integration_test/.env with your credentials"
echo ""
echo "Now you can run tests:"
echo "  source integration_test/.env"
echo "  ./integration_test/run_integration_tests.sh"
