#!/bin/bash
# Run all SafeStream DevelopmentVerification test scripts in order
#
# PREREQUISITES - Run these commands BEFORE executing this script:
#
# 1. Navigate to the SafeStream project root (where pyproject.toml is located):
#    cd /path/to/SafeStream
#
# 2. Create and activate a virtual environment:
#    python3.12 -m venv .venv
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

# Remove 'set -e' to allow all scripts to run
# set -e

FAILED_SCRIPTS=()

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
        ./$script
        STATUS=$?
        if [ $STATUS -ne 0 ]; then
            echo "❌ $script FAILED (exit code $STATUS)"
            FAILED_SCRIPTS+=("$script")
        fi
    else
        echo ""
        echo "⚠️  $script is not executable, skipping. (Run: chmod +x $script)"
    fi

done

echo ""
if [ ${#FAILED_SCRIPTS[@]} -eq 0 ]; then
    echo "✅ All DevelopmentVerification scripts completed successfully."
    exit 0
else
    echo "❌ The following scripts failed:"
    for failed in "${FAILED_SCRIPTS[@]}"; do
        echo "   - $failed"
    done
    exit 1
fi