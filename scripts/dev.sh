#!/bin/bash
# Development environment setup script
#
# Description:
#   One-time setup script that creates virtual environment, installs dependencies
#   (Python + Node.js), sets up Playwright browsers, and configures pre-commit hooks.
#
# Usage:
#   ./scripts/dev.sh
#
# Requirements:
#   - Python 3.10+ installed
#   - Node.js 18+ installed
#   - Poetry installed (curl -sSL https://install.python-poetry.org | python3 -)
#
# What It Does:
#   1. Creates virtual environment (venv/)
#   2. Upgrades pip
#   3. Installs Python dependencies via Poetry
#   4. Installs Node.js dependencies
#   5. Installs Playwright browsers (if not already installed)
#   6. Creates .env from .env.example (if missing)
#   7. Sets up pre-commit hooks
#
# Output:
#   - Virtual environment: venv/
#   - .env file created (if missing)
#   - All dependencies installed
#
# Examples:
#   ./scripts/dev.sh    # First-time setup

set -e

echo "🚀 Starting Deep Agent AGI development environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing Python dependencies..."
poetry install

# Install Node.js dependencies
echo "📥 Installing Node.js dependencies..."
npm install

# Install Playwright browsers if needed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "🎭 Installing Playwright browsers..."
    npx playwright install
    npx playwright install-deps
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API keys before running the app."
    exit 1
fi

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

echo "✅ Development environment ready!"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your API keys"
echo "  2. Run 'poetry run uvicorn backend.deep_agent.main:app --reload' to start backend"
echo "  3. Run 'npm run dev' from frontend/ to start frontend"
echo ""
