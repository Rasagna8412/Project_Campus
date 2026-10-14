"""Convenience script to start the Project Campus backend development server."""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} backend on http://{settings.HOST}:{settings.PORT}")
    print(f"API Documentation available at: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Health check endpoint: http://{settings.HOST}:{settings.PORT}/health")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
