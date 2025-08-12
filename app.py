from fastapi import FastAPI
from pydantic import BaseModel
import os
import numpy as np
import uvicorn
from typing import Dict, Any

app = FastAPI(title="FastAPI App", version="1.0.0")

@app.get("/env")
def home() -> Dict[str, str]:
    app_name = os.getenv("APP_NAME", "FastAPIApp")
    return {"message": f"Welcome to {app_name}!"}

@app.get("/random")
def random_stats() -> Dict[str, float]:
    data = np.random.randn(100)
    return {
        "mean": float(np.mean(data)),
        "std_dev": float(np.std(data))
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
