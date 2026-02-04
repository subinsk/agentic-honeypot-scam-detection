"""
Run the Honey-Pot API. Use from project root with venv activated.

Development (auto-reload on code and .env changes):
  RELOAD=true python run.py
  or on Windows: set RELOAD=true && python run.py

Production (no reload):
  python run.py
  or: uvicorn src.main:app --host 0.0.0.0 --port 8000
"""
import os
import sys
from pathlib import Path

# Ensure project root is on path when run as script
_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root))

import uvicorn

_RELOAD = os.environ.get("RELOAD", "").strip().lower() in ("1", "true", "yes")
_HOST = os.environ.get("HOST", "0.0.0.0")
_PORT = int(os.environ.get("PORT", "8000"))

if __name__ == "__main__":
    kwargs = {"host": _HOST, "port": _PORT, "reload": _RELOAD}
    if _RELOAD:
        kwargs["reload_includes"] = [".env"]
    uvicorn.run("src.main:app", **kwargs)
