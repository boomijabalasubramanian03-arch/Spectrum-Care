#!/usr/bin/env bash
# Chroma Context - one-command start (macOS / Linux).
# First run needs internet once (installs packages); afterwards fully offline.
set -e
cd "$(dirname "$0")"

command -v python3 >/dev/null || { echo "Python 3.10+ required"; exit 1; }

if [ ! -d backend/venv ]; then
  echo "[1/3] Creating Python environment..."
  python3 -m venv backend/venv
fi
if [ ! -f backend/venv/.deps_installed ]; then
  echo "[2/3] Installing Python packages (first run only)..."
  backend/venv/bin/pip install --upgrade pip
  backend/venv/bin/pip install -r backend/requirements.txt
  touch backend/venv/.deps_installed
fi
if [ ! -f frontend/dist/index.html ]; then
  command -v npm >/dev/null || { echo "Node.js 18+ needed once to build the web app"; exit 1; }
  echo "[3/3] Building the web app (first run only)..."
  (cd frontend && npm install && npm run build)
fi

echo "Starting Chroma Context on http://localhost:8000  (Ctrl+C to stop)"
cd backend
exec venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
