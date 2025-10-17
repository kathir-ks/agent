#!/bin/bash
# Quick start script for Personal Agent

set -e

echo "=== Personal Agent Setup & Run ==="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your GEMINI_API_KEY"
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter after you've added your API key to .env..."
fi

# Create data directory
mkdir -p data

# Install dependencies if needed
if ! python -c "import google.generativeai" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Ask what to run
echo ""
echo "What would you like to run?"
echo "1. Terminal CLI (Interactive)"
echo "2. Web UI"
echo "3. Background Daemon"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "Starting Terminal CLI..."
        python -m src.terminal.cli
        ;;
    2)
        echo "Starting Web UI..."
        echo "Access the web interface at: http://localhost:8000"
        python -m src.web.app
        ;;
    3)
        echo "Starting Background Daemon..."
        python -m src.daemon.service
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
