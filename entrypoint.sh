#!/bin/bash
set -e

if [ "$MODE" = "script" ]; then
    if [ "$DEBUG" = "true" ]; then
        echo "🛠️  Running script in DEBUG mode..."
        exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m script
    else
        echo "🛠️  Running script in normal mode..."
        exec python -m script
    fi

elif [ "$MODE" = "api" ]; then
    if [ "$DEBUG" = "true" ]; then
        echo "🛠️  Running fastapi in DEBUG mode..."
        exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app:app --host=0.0.0.0 --port=5000 --reload
    else
        echo "🚀 Running fastapi in normal mode..."
        exec python -m uvicorn app:app --host=0.0.0.0 --port=5000
    fi

else
    echo "❌ Unknown MODE: $MODE"
    exit 1
fi



