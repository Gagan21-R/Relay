"""Evaluation metrics (synthetic data; real-world validation pending). Results come from `python -m eval.run_eval`."""
import json
import subprocess
import sys
import threading
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
RESULTS = Path(__file__).resolve().parents[2] / "eval" / "results.json"
_running = threading.Event()


@router.get("")
def metrics():
    if not RESULTS.exists():
        return {"available": False, "running": _running.is_set(), "disclaimer": "Evaluated on synthetic data; real-world validation pending."}
    return {"available": True, "running": _running.is_set(), **json.loads(RESULTS.read_text(encoding="utf-8"))}


@router.post("/run")
def run():
    """Re-run the evaluation in a separate process (its own throwaway database)."""
    if _running.is_set():
        return {"started": False, "running": True}

    def job():
        _running.set()
        try:
            subprocess.run([sys.executable, "-m", "eval.run_eval"], cwd=RESULTS.parents[1], capture_output=True, timeout=900)
        finally:
            _running.clear()
    threading.Thread(target=job, daemon=True).start()
    return {"started": True, "running": True}
