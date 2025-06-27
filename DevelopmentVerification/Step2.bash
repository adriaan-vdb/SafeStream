#!/bin/bash
# SafeStream — Step 2 Verification Script
# Purpose: Run key tests to confirm Docker setup, app health, and dev tooling are functional.
# Usage: Run this from the SafeStream project root: ./DevelopmentVerification/Step2.bash

### Before running the script:

# Activate your virtual environment if not already active
# python3.12 -m venv .venv
# source .venv/bin/activate

# Install all required dependencies
# pip install -e ".[dev]"

# To run entire script:
# chmod +x DevelopmentVerification/Step2.bash
# ./DevelopmentVerification/Step2.bash

set -e  # Exit immediately if a command fails

################################################################################
# 0. PREPARATION
################################################################################

# [Optional] Activate your virtual environment if not already active
# source .venv/bin/activate

# Ensure all Python dependencies are installed, including dev tools like pre-commit
# This assumes you've added httpx, pre-commit, ruff, black, pytest to [project.optional-dependencies].dev
# Run this once before executing the script:
# pip install -e ".[dev]"

################################################################################
# 1. PRE-COMMIT HOOKS
################################################################################

echo "▶ Running pre-commit checks..."

# Installs the .git/hooks/* scripts for the current repo
pre-commit install

# Runs all configured hooks (e.g., black, ruff) across the entire repo
# This step will also auto-fix code if needed
pre-commit run --all-files

################################################################################
# 2. LOCAL DOCKER BUILD + RUN TEST
################################################################################

echo "▶ Testing local Docker build and run..."

# Define variables for Docker operations
DOCKER_IMAGE=safestream
DOCKER_CONTAINER=safestream-test

# Build the Docker image
docker build -t $DOCKER_IMAGE .

# Stop and remove any existing test container (ignore errors if none exist)
docker rm -f $DOCKER_CONTAINER 2>/dev/null || true

# Start the container and expose port 8000
docker run -d -p 8000:8000 --name $DOCKER_CONTAINER $DOCKER_IMAGE

# Wait for the app to start
sleep 5

# Verify that the root endpoint returns a 200 with expected JSON
curl -f http://localhost:8000/ | grep '"status":"ok"'

# Verify that the /healthz endpoint returns expected health check status
curl -f http://localhost:8000/healthz | grep '"status":"healthy"'

# Clean up the test container
docker stop $DOCKER_CONTAINER && docker rm $DOCKER_CONTAINER

################################################################################
# 3. DOCKER COMPOSE TEST
################################################################################

echo "▶ Testing docker-compose with the 'api' service..."

# Build and start services defined in docker-compose.yml
docker compose up --build -d

# Wait for services to be healthy
sleep 5

# Confirm service is available via root and health endpoints
curl -f http://localhost:8000/ | grep '"status":"ok"'
curl -f http://localhost:8000/healthz | grep '"status":"healthy"'

# Shut everything down after testing
docker compose down

################################################################################
# 4. SUCCESS CONFIRMATION
################################################################################

echo "✅ Step 2 verification complete: All checks passed."
