"""Capture tests/golden/api_baseline.json from a checkout: `python capture_golden.py <repo_root> <out.json>`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repo / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app  # noqa: E402
from app.seed import seed_data  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from scenario import run_scenario  # noqa: E402

if __name__ == "__main__":
    seed_data.run()
    with TestClient(app) as client:
        result = run_scenario(client)
    Path(sys.argv[2]).write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + "\n")
    print(len(result), "responses captured")
