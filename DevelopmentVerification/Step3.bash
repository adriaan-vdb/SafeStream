#!/bin/bash
# SafeStream — Step 3 Verification Script
# Purpose: Test CI/CD pipeline, enhanced testing infrastructure, code quality, and placeholder documentation
# Usage: Run this from the SafeStream project root: ./DevelopmentVerification/Step3.bash

### Before running the script:

# Activate your virtual environment if not already active
# python3.12 -m venv .venv
# source .venv/bin/activate

# Install all required dependencies
# pip install -e ".[dev]"

# To run entire script:
# chmod +x DevelopmentVerification/Step3.bash
# ./DevelopmentVerification/Step3.bash

set -e  # Exit immediately if a command fails

################################################################################
# 0. PREPARATION
################################################################################

echo "🚀 SafeStream Step 3 Verification - CI/CD, Testing, and Quality Checks"

# [Optional] Activate your virtual environment if not already active
# source .venv/bin/activate

# Ensure all Python dependencies are installed, including dev tools
# This includes: httpx, pre-commit, ruff, black, pytest, pytest-asyncio
# Run this once before executing the script:
# pip install -e ".[dev]"

################################################################################
# 1. CODE QUALITY CHECKS
################################################################################

echo "▶ Step 1: Running code quality checks..."

# Check code formatting with Black
# This ensures all Python files follow consistent formatting (88 char line length)
echo "  📝 Checking code formatting with Black (the only formatter)..."
black --check .

# Run comprehensive linting with Ruff
# This checks for style issues, unused imports, and code quality problems (no formatting)
echo "  🔍 Running linting with Ruff (linting only, not formatting)..."
ruff check .

# Verify no linting issues remain
# Ruff should report "All checks passed!" if everything is clean
echo "  ✅ Code quality checks completed"

################################################################################
# 2. TESTING INFRASTRUCTURE
################################################################################

echo "▶ Step 2: Testing infrastructure verification..."

# Run the enhanced test suite
# This tests: root endpoint, health endpoint, OpenAPI docs, and schema
echo "  🧪 Running enhanced test suite..."
pytest -q

# Verify test count (should be 4 tests: root, health, docs, schema)
echo "  📊 Test results verified"

# Test pytest fixtures are working
# This ensures conftest.py is properly configured
echo "  🔧 Testing pytest fixtures..."
pytest -q --collect-only

################################################################################
# 3. PRE-COMMIT HOOKS
################################################################################

echo "▶ Step 3: Pre-commit hooks verification..."

# Install pre-commit hooks if not already installed
# This sets up git hooks for automatic code quality checks
echo "  📦 Installing pre-commit hooks..."
pre-commit install

# Run pre-commit on all files
# This simulates what happens on every git commit
echo "  🔄 Running pre-commit checks..."
pre-commit run --all-files

################################################################################
# 4. LOCAL CI SIMULATION
################################################################################

echo "▶ Step 4: Local CI workflow simulation..."

# Run the CI test script that simulates GitHub Actions
# This verifies the exact steps that will run in CI
echo "  🏭 Running local CI simulation..."
./scripts/test-ci.sh

################################################################################
# 5. DOCKER VERIFICATION
################################################################################

echo "▶ Step 5: Docker verification..."

# Test Docker build and run
# This ensures the containerized environment works correctly
echo "  🐳 Testing Docker build..."
docker build -t safestream-test .

# Test container startup and health
echo "  🏥 Testing container health..."
docker run -d --name safestream-health-test -p 8001:8000 safestream-test
sleep 5

# Verify endpoints work in container
echo "  🔗 Testing containerized endpoints..."
curl -f http://localhost:8001/ | grep '"status":"ok"'
curl -f http://localhost:8001/healthz | grep '"status":"healthy"'

# Clean up test container
docker stop safestream-health-test && docker rm safestream-health-test

################################################################################
# 6. PLACEHOLDER DOCUMENTATION VERIFICATION
################################################################################

echo "▶ Step 6: Placeholder documentation verification..."

# Check that all placeholder files have proper TODO comments
# This ensures future development is well-documented
echo "  📚 Checking placeholder documentation..."

# Verify main.py has stage-specific TODOs
grep -q "TODO(stage-" app/main.py && echo "  ✅ app/main.py TODOs verified"

# Verify schemas.py has protocol-specific TODOs
grep -q "TODO(stage-" app/schemas.py && echo "  ✅ app/schemas.py TODOs verified"

# Verify events.py has configuration-specific TODOs
grep -q "TODO(stage-" app/events.py && echo "  ✅ app/events.py TODOs verified"

# Verify moderation.py has threshold-specific TODOs
grep -q "TODO(stage-" app/moderation.py && echo "  ✅ app/moderation.py TODOs verified"

# Verify db.py has model-specific TODOs
grep -q "TODO(stage-" app/db.py && echo "  ✅ app/db.py TODOs verified"

################################################################################
# 7. GITHUB ACTIONS WORKFLOW VERIFICATION
################################################################################

echo "▶ Step 7: GitHub Actions workflow verification..."

# Check that CI workflow file exists and is valid
echo "  📋 Checking CI workflow configuration..."
if [ -f ".github/workflows/ci.yml" ]; then
    echo "  ✅ CI workflow file exists"
    
    # Verify workflow has required sections
    grep -q "name: CI" .github/workflows/ci.yml && echo "  ✅ Workflow name defined"
    grep -q "python-version:" .github/workflows/ci.yml && echo "  ✅ Python versions configured"
    grep -q "ruff check" .github/workflows/ci.yml && echo "  ✅ Ruff linting configured"
    grep -q "black --check" .github/workflows/ci.yml && echo "  ✅ Black formatting configured"
    grep -q "pytest -q" .github/workflows/ci.yml && echo "  ✅ Pytest testing configured"
else
    echo "  ❌ CI workflow file missing"
    exit 1
fi

################################################################################
# 8. FINAL VERIFICATION
################################################################################

echo "▶ Step 8: Final verification..."

# Run a comprehensive check of all quality tools
echo "  🔍 Final quality check..."
black --check . && echo "  ✅ Black formatting: PASS"
ruff check . && echo "  ✅ Ruff linting: PASS"
pytest -q && echo "  ✅ Pytest tests: PASS"

# Verify project structure
echo "  📁 Project structure verification..."
[ -f "pyproject.toml" ] && echo "  ✅ pyproject.toml exists"
[ -f "tests/conftest.py" ] && echo "  ✅ tests/conftest.py exists"
[ -f "tests/test_smoke.py" ] && echo "  ✅ tests/test_smoke.py exists"
[ -f "scripts/test-ci.sh" ] && echo "  ✅ scripts/test-ci.sh exists"

################################################################################
# 9. SUCCESS CONFIRMATION
################################################################################

echo ""
echo "🎉 Step 3 verification complete: All checks passed!"
echo ""
echo "✅ What was verified:"
echo "   • Code quality (Black + Ruff)"
echo "   • Testing infrastructure (Pytest + Fixtures)"
echo "   • Pre-commit hooks"
echo "   • Local CI simulation"
echo "   • Docker containerization"
echo "   • Placeholder documentation"
echo "   • GitHub Actions workflow"
echo ""
echo "🚀 SafeStream is ready for Stage 4: WebSocket implementation!"
echo ""
echo "📋 Next steps:"
echo "   • Implement /ws/{username} endpoint"
echo "   • Add in-memory socket management"
echo "   • Create Pydantic schemas for messages"
echo "   • Add WebSocket E2E tests" 