"""
RailBlock AI Backend Entrypoint.

Allows running uvicorn directly from the backend directory:
    uvicorn main:app --host 0.0.0.0 --port 8000
Or from the project root:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Re-export app instance
from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
