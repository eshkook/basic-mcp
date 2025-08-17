#!/bin/sh
set -e

if [ "$DEBUG" = "true" ]; then
    echo "🛠️  Running in DEBUG mode (FastAPI + debugpy)..."
    exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app:app --host=0.0.0.0 --port=5000 --reload
else
    echo "🚀 Running in normal mode (FastAPI)..."
    exec python -m uvicorn app:app --host=0.0.0.0 --port=5000
fi



