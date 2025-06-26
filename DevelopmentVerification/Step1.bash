#!/bin/bash
# SafeStream — Step 1 Manual Verification Script
# Purpose: Ensure the project skeleton is functional, testable, and style/lint compliant.
# Run this from the root of the SafeStream repository.

### To run the script:
# chmod +x DevelopmentVerification/Step1.bash
# ./DevelopmentVerification/Step1.bash

set -e  # Exit on first error

################################################################################
# 1. NAVIGATE TO PROJECT ROOT
################################################################################

# 1. Ensure you are at project root (where pyproject.toml lives)
# cd /path/to/safestream  # ⬅️ Replace with actual path or use `pwd` to check
# Or navigate to the SafeStream directory containing pyproject.toml

################################################################################
# 2. CREATE AND ACTIVATE A VIRTUAL ENVIRONMENT
################################################################################

# Create a new virtual environment (skip if one already exists)
python3 -m venv .venv

# Activate it:
# On macOS/Linux:
source .venv/bin/activate

# On Windows PowerShell:
# .venv\Scripts\Activate.ps1

################################################################################
# 3. INSTALL STAGE-1 DEPENDENCIES
################################################################################

# Upgrade pip to avoid any outdated resolver issues
python -m pip install --upgrade pip

# Install only the Stage 1 core dependencies (editable mode)
# If httpx, black, ruff, and pytest are under `[project.optional-dependencies].dev`,
# use the dev extras instead:
pip install -e ".[dev]"

################################################################################
# 4. RUN THE FASTAPI APP (DEVELOPMENT SERVER)
################################################################################

# Launch the FastAPI server in the background with live-reload enabled
uvicorn app.main:app --reload &
APP_PID=$!

# Wait a moment for the server to start
sleep 2

################################################################################
# 5. SANITY CHECK THE CORE ENDPOINTS
################################################################################

# Check the root endpoint returns the correct status JSON
curl -s http://127.0.0.1:8000/ | grep '"status":"ok"'

# If something went wrong, check the processes running:
# lsof -i :8000
# kill -9 <PID>

# Check the /healthz endpoint returns HTTP 200
curl -s -o /dev/null -w "%{http_code}\\n" http://127.0.0.1:8000/healthz  # Expected output: 200

################################################################################
# 6. STOP THE DEVELOPMENT SERVER
################################################################################

# Kill the Uvicorn background process
kill $APP_PID

# On Windows: just use Ctrl+C if running in foreground, or find the PID with `Get-Process` and stop manually

################################################################################
# 7
