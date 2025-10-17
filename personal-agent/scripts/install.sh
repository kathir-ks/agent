#!/bin/bash
# Installation script for Personal Agent

set -e

echo "=== Personal Agent Installation ==="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Check if Python >= 3.10
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Error: Python 3.10 or higher is required"
    exit 1
fi

# Create virtual environment (optional but recommended)
read -p "Create a virtual environment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup .env file
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: You need to add your GEMINI_API_KEY to the .env file"
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Would you like to open .env for editing now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo ""
    echo ".env file already exists"
fi

# Create data directory
mkdir -p data

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Make sure your GEMINI_API_KEY is set in .env"
echo "2. Run one of the following:"
echo "   - Terminal CLI:  python -m src.terminal.cli"
echo "   - Web UI:        python -m src.web.app"
echo "   - Daemon:        python -m src.daemon.service"
echo ""
echo "Or use the quick start script: ./scripts/run.sh"
