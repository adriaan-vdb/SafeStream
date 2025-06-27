# Quick Start Guide

cd /Users/adriaanvanderberg/Documents/Interests/Software/TikTok/SafeStream
source .venv312/bin/activate
./DevelopmentVerification/all_verifications.sh

## Environment Setup

### Python 3.12.3 (Required for ML dependencies)

```bash
# Install Python 3.12.3
pyenv install 3.12.3
cd SafeStream
pyenv local 3.12.3

# Create virtual environment
pyenv exec python3 -m venv .venv312
source .venv312/bin/activate

# Install dependencies
pip install -e ".[dev,ml]"
```

### Verify Setup

```bash
python3 --version  # Should show Python 3.12.3
python3 -c "import detoxify; print('✓ ML ready')"
```

## Development Commands

### Run Tests

# ./DevelopmentVerification/all_verifications.sh

```bash
# All tests
pytest -q

# Specific test file
pytest tests/test_moderation.py -q

# With coverage
pytest --cov=app tests/
```

### Start Development Server

```bash
# Basic server
uvicorn app.main:app --reload

# With custom port
uvicorn app.main:app --reload --port 8001

# Production mode (no reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Fix linting issues
ruff check . --fix
```

## Environment Variables

```bash
# ML Moderation
export DISABLE_DETOXIFY=0    # Enable real ML (default)
export DISABLE_DETOXIFY=1    # Use stub mode
export TOXIC_THRESHOLD=0.6   # Toxicity threshold

# Gift Simulation
export GIFT_INTERVAL_SECS=15 # Gift generation interval
```

## Access Points

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/healthz
- **WebSocket**: ws://localhost:8000/ws/{username}

## Troubleshooting

### Common Issues

1. **Python version**: Must use Python 3.12.3 for ML dependencies
2. **Virtual environment**: Always activate `.venv312` before working
3. **Port conflicts**: Use `--port 8001` if 8000 is busy
4. **ML not working**: Check `DISABLE_DETOXIFY` environment variable

### Reset Environment

```bash
# If dependencies get corrupted
rm -rf .venv312
pyenv exec python3 -m venv .venv312
source .venv312/bin/activate
pip install -e ".[dev,ml]"
``` 