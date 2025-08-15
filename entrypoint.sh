#!/bin/sh

if [ "$DEBUG" = "true" ]; then
    echo "🛠️  Running in DEBUG mode (FastAPI + debugpy)..."
    exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app:app --host=0.0.0.0 --port=5000 --reload
else
    echo "🚀 Running in normal mode (FastAPI)..."
    exec uvicorn app:app --host=0.0.0.0 --port=5000
fi


# to just run a script:

# if [ "$DEBUG" = "true" ]; then
#     echo "🛠️  Running in DEBUG mode..."
#     exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client script.py
# else
#     echo "🚀 Running in normal mode..."
#     exec python script.py
# fi