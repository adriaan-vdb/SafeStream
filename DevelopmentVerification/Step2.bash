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
# 


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

# Start the container and expose port 8001
docker run -d -p 8001:8000 --name $DOCKER_CONTAINER $DOCKER_IMAGE

# Wait for the app to start (increase wait time and add retry logic)
echo "Waiting for container to start..."
for i in {1..30}; do
    if curl -s http://localhost:8001/ >/dev/null 2>&1; then
        echo "Container is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Container failed to start within 30 seconds"
        docker logs $DOCKER_CONTAINER
        docker stop $DOCKER_CONTAINER && docker rm $DOCKER_CONTAINER
        exit 1
    fi
    sleep 1
done

# Verify that the root endpoint returns a 200 with expected JSON
echo "Testing root endpoint..."
if curl -f http://localhost:8001/ | grep -q '"status":"ok"'; then
    echo "✅ Root endpoint test passed"
else
    echo "❌ Root endpoint test failed"
    docker logs $DOCKER_CONTAINER
    docker stop $DOCKER_CONTAINER && docker rm $DOCKER_CONTAINER
    exit 1
fi

# Verify that the /healthz endpoint returns expected health check status
echo "Testing health endpoint..."
if curl -f http://localhost:8001/healthz | grep -q '"status":"healthy"'; then
    echo "✅ Health endpoint test passed"
else
    echo "❌ Health endpoint test failed"
    docker logs $DOCKER_CONTAINER
    docker stop $DOCKER_CONTAINER && docker rm $DOCKER_CONTAINER
    exit 1
fi

# Clean up the test container
echo "Cleaning up test container..."
docker stop $DOCKER_CONTAINER && docker rm $DOCKER_CONTAINER

################################################################################
# 3. DOCKER COMPOSE TEST
################################################################################

echo "▶ Testing docker-compose with the 'api' service..."

# Build and start services defined in docker-compose.yml
docker compose up --build -d

# Wait for services to be healthy
echo "Waiting for docker-compose services to start..."
for i in {1..30}; do
    if curl -s http://localhost:8002/ >/dev/null 2>&1; then
        echo "Docker-compose services are ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Docker-compose services failed to start within 30 seconds"
        docker compose logs
        docker compose down
        exit 1
    fi
    sleep 1
done

# Confirm service is available via root and health endpoints
echo "Testing docker-compose root endpoint..."
if curl -f http://localhost:8002/ | grep -q '"status":"ok"'; then
    echo "✅ Docker-compose root endpoint test passed"
else
    echo "❌ Docker-compose root endpoint test failed"
    docker compose logs
    docker compose down
    exit 1
fi

echo "Testing docker-compose health endpoint..."
if curl -f http://localhost:8002/healthz | grep -q '"status":"healthy"'; then
    echo "✅ Docker-compose health endpoint test passed"
else
    echo "❌ Docker-compose health endpoint test failed"
    docker compose logs
docker compose down
    exit 1
fi

################################################################################
# 4. SUCCESS CONFIRMATION
################################################################################

echo "✅ Step 2 verification complete: All checks passed."
