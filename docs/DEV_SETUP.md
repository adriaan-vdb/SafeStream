# SafeStream Development Setup Guide

This guide provides detailed instructions for setting up the SafeStream development environment using either local virtual environments or Docker.

## Prerequisites

- Python 3.12 or higher
- Git
- Docker and Docker Compose (for containerized development)

## Option 1: Local Development with Virtual Environment

### 1. Clone and Setup

```bash
git clone <repository-url>
cd SafeStream 
```

### 2. Create Virtual Environment 

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install project in editable mode with development dependencies
pip install -e ".[dev]"
```

### 4. Setup Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files (optional)
pre-commit run --all-files
```

### 5. Verify Installation

```bash
# Run tests
pytest -q

# Check code quality
ruff check .
black --check .

# Start development server
uvicorn app.main:app --reload
```

### 6. Test Endpoints

In another terminal:
```bash
curl http://localhost:8000/          # Should return {"status":"ok"}
curl http://localhost:8000/healthz   # Should return {"status":"healthy"}
```

### 7. Test WebSocket Chat

Connect to the WebSocket chat:
```bash
# Using websocat (install: brew install websocat)
websocat ws://localhost:8000/ws/yourname

# Or using wscat (install: npm install -g wscat)
wscat -c ws://localhost:8000/ws/yourname
```

Send a chat message:
```json
{"type":"chat","message":"Hello, everyone!"}
```

### 8. Test Gift API

Send a gift via HTTP API:
```bash
curl -X POST http://localhost:8000/api/gift \
  -d '{"from":"admin","gift_id":1,"amount":5}' \
  -H "Content-Type: application/json"
```

Expected response:
```json
{"status":"queued"}
```

## Option 2: Docker Development

### 1. Build and Start Services

```bash
# Build and start the API service
docker compose up --build

# Or run in detached mode
docker compose up --build -d
```

### 2. Verify Container is Running

```bash
# Check service status
docker compose ps

# Check logs
docker compose logs api

# Test endpoints
curl http://localhost:8000/          # Should return {"status":"ok"}
curl http://localhost:8000/healthz   # Should return {"status":"healthy"}
```

### 3. Test WebSocket and Gift API in Docker

```bash
# Connect to WebSocket
websocat ws://localhost:8000/ws/yourname

# Send gift
curl -X POST http://localhost:8000/api/gift \
  -d '{"from":"admin","gift_id":1,"amount":5}' \
  -H "Content-Type: application/json"
```

### 4. Development Workflow

```bash
# Stop services
docker compose down

# Rebuild after code changes
docker compose up --build

# View logs in real-time
docker compose logs -f api
```

## Development Tools

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

- **Black**: Automatic code formatting (the only formatter)
- **Ruff**: Linting and import sorting (no formatting)

Hooks run automatically on `git commit`. To run manually:
```bash
pre-commit run --all-files
```

### Code Quality Tools

```bash
# Format code (Black is the only formatter)
black .

# Lint code
ruff check .

# Fix linting issues
ruff check . --fix

# Run tests
pytest -q

# Run tests with coverage (when implemented)
pytest --cov=app tests/
```

## API Examples

### WebSocket Chat Protocol

Connect to chat:
```bash
websocat ws://localhost:8000/ws/yourname
```

Send message:
```json
{"type":"chat","message":"Hello, world!"}
```

Receive message:
```json
{
  "type":"chat",
  "user":"yourname",
  "message":"Hello, world!",
  "toxic":false,
  "score":0.0,
  "ts":"2025-06-26T12:34:56Z"
}
```

### Gift API Protocol

Send gift:
```bash
curl -X POST http://localhost:8000/api/gift \
  -d '{"from":"admin","gift_id":999,"amount":1}' \
  -H "Content-Type: application/json"
```

Response:
```json
{"status":"queued"}
```

WebSocket clients receive:
```json
{
  "type":"gift",
  "from":"admin",
  "gift_id":999,
  "amount":1
}
```

## Project Structure Reference

See the main [README.md](../README.md) for:
- [Feature Summary](../README.md#1-feature-summary)
- [Architecture Overview](../README.md#3-architecture)
- [API Documentation](../README.md#6-api--protocol)
- [Configuration Options](../README.md#5-configuration)

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **Docker Build Fails**
   ```bash
   # Clean Docker cache
   docker system prune -a
   # Rebuild
   docker compose up --build
   ```

3. **Pre-commit Hooks Fail**
   ```bash
   # Update pre-commit hooks
   pre-commit autoupdate
   # Run manually
   pre-commit run --all-files
   ```

4. **WebSocket Connection Issues**
   ```bash
   # Check if server is running
   curl http://localhost:8000/healthz
   
   # Check WebSocket endpoint
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
     http://localhost:8000/ws/test
   ```

### Environment Variables

Key environment variables (see [Configuration](../README.md#5-configuration)):
- `APP_PORT`: FastAPI server port (default: 8000)
- `TOXIC_THRESHOLD`: Moderation threshold (default: 0.6)
- `GIFT_RATE_SEC`: Gift simulation rate (default: 15)

### ML Moderation Setup (Stage 7+)

SafeStream uses Detoxify for toxicity detection. Setup options:

#### Option A: Full ML Moderation (Recommended for Production)
```bash
# Install with ML dependencies
pip install -e ".[dev,ml]"

# Run with real toxicity detection
uvicorn app.main:app --reload
```

#### Option B: Stub Mode (Recommended for Development/CI)
```bash
# Install without ML dependencies
pip install -e ".[dev]"

# Disable Detoxify (uses stub that always returns non-toxic)
export DISABLE_DETOXIFY=1
uvicorn app.main:app --reload
```

#### Environment Variables for ML Moderation
- `DISABLE_DETOXIFY`: Set to "1" to use stub mode (default: "0")
- `TOXIC_THRESHOLD`: Threshold for toxic classification (default: 0.6)

#### ML Moderation Performance
- **First run**: Downloads ~60MB model, slow inference
- **Subsequent runs**: ~10ms inference on CPU, ~200MB RAM usage
- **Model**: Detoxify "original-small" (HuggingFace)

#### Testing ML Moderation
```bash
# Test with real model
pytest tests/test_moderation.py

# Test with stub mode
DISABLE_DETOXIFY=1 pytest tests/test_moderation.py
```

## Next Steps

After setup, continue with:
1. [Stage 2: WebSocket Implementation](../README.md#13-high-level-build-guide)
2. [Stage 3: Moderation Pipeline](../README.md#13-high-level-build-guide)
3. [Stage 4: Gift Simulation](../README.md#13-high-level-build-guide)

## Contributing

1. Create a feature branch
2. Make changes with pre-commit hooks enabled
3. Run tests: `pytest -q`
4. Submit pull request

For more details, see the main [README.md](../README.md). 