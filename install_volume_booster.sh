#!/bin/bash

# Volume Booster Trading Mode - Installation Script
# This script sets up the Python environment and installs required packages

set -e

echo "🚀 Setting up Volume Booster Trading Mode for OctoBot..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install core OctoBot packages
echo "📥 Installing OctoBot core packages..."
pip install octobot octobot-commons octobot-trading --no-deps

# Install additional packages for development and analysis
echo "📊 Installing development and analysis packages..."
pip install numpy pandas matplotlib plotly ta pytest pytest-asyncio asyncio-mqtt

# Install packages from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    echo "📋 Installing packages from requirements.txt..."
    pip install -r requirements.txt --no-deps
fi

echo "✅ Installation completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Test the Volume Booster: python -c 'from Trading.Mode.volume_booster_trading_mode.volume_booster_trading import VolumeBoosterTradingMode; print(\"✅ Volume Booster ready!\")'"
echo "3. Start OctoBot and look for 'VolumeBoosterTradingMode' in the trading modes"
echo ""
echo "📚 Documentation:"
echo "- Setup Guide: Trading/Mode/volume_booster_trading_mode/SETUP.md"
echo "- Configuration: profiles/volume_booster/README.md"
echo "- Summary: VOLUME_BOOSTER_SUMMARY.md"
