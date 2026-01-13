#!/bin/bash
# Quick install script for Aluvia Python SDK

echo "🚀 Installing Aluvia Python SDK..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "✓ Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "✓ Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "✓ Installing dependencies..."
pip install -e . > /dev/null 2>&1

# Install dev dependencies (optional)
if [ "$1" = "dev" ]; then
    echo "✓ Installing dev dependencies..."
    pip install -e ".[dev]" > /dev/null 2>&1
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To verify installation:"
echo "  python verify_install.py"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
echo "To view examples:"
echo "  ls examples/"
echo ""
