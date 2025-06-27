# SafeStream — How to Run and Use Everything

## 1. Backend API (FastAPI + WebSocket)
**Start the backend server:**
```bash
lsof -i :8000
kill -9 34693
cd /Users/adriaanvanderberg/Documents/Interests/Software/TikTok/SafeStream
source .venv312/bin/activate  # Activate your virtual environment
pip install -e ".[dev,ml]"
uvicorn app.main:app --reload

-> Make sure Docker is running
./DevelopmentVerification/all_verifications.sh
./DevelopmentVerification/Step10.bash
python -m pytest -v
```
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/healthz
- **Chat UI:** http://localhost:8000/chat
- **WebSocket:** ws://localhost:8000/ws/{username}

## 2. Moderator Dashboard (Streamlit)
**Start the dashboard:**
```bash
streamlit run dashboard/app.py
```
- **Dashboard UI:** http://localhost:8501

## 3. Sending Gifts (API)
**Manual gift trigger:**
```bash
curl -X POST http://localhost:8000/api/gift -H "Content-Type: application/json" \
  -d '{"from":"admin","gift_id":999,"amount":1}'
```

## 4. Resetting Metrics and Logs
- **Reset metrics:**  
  ```bash
  curl -X POST http://localhost:8000/api/admin/reset_metrics
  ```
- **Reset logs:**  
  ```bash
  rm logs/*.jsonl
  ```

## 5. Running Tests and Verification
**Run all verification scripts:**
```bash
./DevelopmentVerification/all_verifications.sh
```
**Run tests manually:**
```bash
pytest
```

## 6. Docker (Optional)
**Build and run with Docker Compose:**
```bash
docker compose up --build
```
- This will start both the API and dashboard in containers.

## 7. Development Tips
- **Install dependencies:**  
  ```bash
  pip install -e ".[dev]"
  ```
- **Format code:**  
  ```bash
  black .
  ```
- **Lint code:**  
  ```bash
  ruff check .
  ```

---

You should access:
Main Chat Interface: http://localhost:8000/chat
API Documentation: http://localhost:8000/docs
Health Check: http://localhost:8000/healthz
Moderator Dashboard: http://localhost:8501 (if running Streamlit)

Enter a username in the modal to join the chat.
Chat and see real-time messages, gifts, and reactions

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