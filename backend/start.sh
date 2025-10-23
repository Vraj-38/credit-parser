#!/bin/bash
set -e

# Activate venv if present (optional)
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Start FastAPI app with uvicorn
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
