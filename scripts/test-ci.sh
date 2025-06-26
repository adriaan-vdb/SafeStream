#!/bin/bash
# SafeStream CI Test Script
# Purpose: Test the same steps that GitHub Actions CI will run
# Usage: Run from SafeStream project root

set -e

echo "🧪 Testing SafeStream CI workflow locally..."

# Check Python version
echo "📋 Python version:"
python3 --version

# Install dependencies
echo "📦 Installing dependencies..."
python3 -m pip install --upgrade pip
pip3 install -e ".[dev]"

# Lint with ruff
echo "🔍 Running ruff linting..."
ruff check .

# Check formatting with black
echo "🎨 Checking code formatting with black..."
black --check .

# Run tests
echo "🧪 Running tests..."
pytest -q

echo "✅ All CI checks passed locally!"
echo "🚀 Ready for GitHub Actions deployment" 