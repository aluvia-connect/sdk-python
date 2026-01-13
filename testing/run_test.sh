#!/bin/bash
# Quick test runner for sdk.py

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run from sdk-python root: python3 -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi

# Activate virtual environment and run test
source ../venv/bin/activate
python sdk.py
