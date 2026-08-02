"""Run Smart Discovery Assistant API server."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import uvicorn

from config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )
