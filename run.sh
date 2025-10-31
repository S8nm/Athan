#!/bin/bash
# One-command setup and run script for Athan bot (Linux/Mac)

echo "🕌 Athan Bot - Startup Script"
echo "================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ Python found: $PYTHON_VERSION"

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! pip list 2>&1 | grep -q "discord.py"; then
    echo "📥 Installing dependencies..."
    pip install -e .
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies already installed"
fi

# Check for Discord token
echo ""
echo "🔑 Checking for Discord token..."

TOKEN_FOUND=false

if [ -f "DISCORD_TOKEN.txt" ]; then
    if [ -s "DISCORD_TOKEN.txt" ]; then
        echo "✓ Token found in: DISCORD_TOKEN.txt"
        TOKEN_FOUND=true
    fi
elif [ -f ".env" ]; then
    if grep -q "DISCORD_TOKEN" .env; then
        echo "✓ Token found in: .env"
        TOKEN_FOUND=true
    fi
elif [ -n "$DISCORD_TOKEN" ]; then
    echo "✓ Token found in environment variable"
    TOKEN_FOUND=true
fi

if [ "$TOKEN_FOUND" = false ]; then
    echo "✗ Discord token not found!"
    echo ""
    echo "Please create one of these files:"
    echo "  1. DISCORD_TOKEN.txt (just paste your token)"
    echo "  2. .env (add line: DISCORD_TOKEN=your_token)"
    echo ""
    echo "Get your bot token from: https://discord.com/developers/applications"
    exit 1
fi

# Check for adhan audio file
if [ ! -f "assets/adhan.mp3" ]; then
    echo "⚠ Warning: assets/adhan.mp3 not found"
    echo "  Voice Adhan will not work until you add the audio file"
    echo "  See assets/README.md for details"
else
    echo "✓ Adhan audio file found"
fi

# Create data directory if missing
if [ ! -d "data" ]; then
    mkdir -p data
    echo "✓ Data directory created"
else
    echo "✓ Data directory exists"
fi

echo ""
echo "🚀 Starting Athan Bot..."
echo "================================"
echo ""
echo "Press Ctrl+C to stop the bot"
echo ""

# Run the bot
python3 -m athan.bot

