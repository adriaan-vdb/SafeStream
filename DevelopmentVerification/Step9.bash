#!/bin/bash

set -e

# Lint
ruff check .
black --check .

# Unit tests
pytest

# Run dashboard in headless mode for 5s
if [ "$SKIP_DASHBOARD" = "1" ]; then
  echo "Skipping dashboard launch in CI."
  exit 0
fi

streamlit run dashboard/app.py --server.headless true &
DASH_PID=$!
sleep 5
kill $DASH_PID 