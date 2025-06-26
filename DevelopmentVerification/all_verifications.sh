#!/bin/bash
# Run all SafeStream DevelopmentVerification test scripts in order
#
# PREREQUISITES - Run these commands BEFORE executing this script:
#
# 1. Navigate to the SafeStream project root (where pyproject.toml is located):
#    cd /path/to/SafeStream
#
# 2. Create and activate a virtual environment:
#    python3 -m venv .venv
#    source .venv/bin/activate
#
# 3. Install all development dependencies:
#    pip install -e ".[dev]"
#
# 4. Make all verification scripts executable:
#    chmod +x DevelopmentVerification/*.bash
#
# 5. Run this script from the SafeStream project root:
#    ./DevelopmentVerification/all_verifications.sh

set -e

# Ensure we're in the SafeStream project root (where pyproject.toml is located)
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the SafeStream project root."
    echo "   Current directory: $(pwd)"
    echo "   Expected: Directory containing pyproject.toml"
    exit 1
fi

echo "▶ Running all SafeStream verification scripts..."

for script in DevelopmentVerification/Step*.bash; do
    if [[ -x "$script" ]]; then
        echo ""
        echo "============================================================"
        echo "▶ Running $script"
        echo "============================================================"
        ./"$script"
    else
        echo ""
        echo "⚠️  $script is not executable, skipping. (Run: chmod +x $script)"
    fi
done

echo ""
echo "✅ All DevelopmentVerification scripts completed."