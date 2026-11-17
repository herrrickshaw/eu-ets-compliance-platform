from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    """TestClient over a freshly seeded temporary SQLite DB (no network, no credentials)."""
    os.environ["CARBON_DB_PATH"] = str(tmp_path_factory.mktemp("db") / "test.db")
    os.environ.setdefault("JWT_SECRET", "test-only-secret")
    from app.main import app
    from app.seed import seed_data
    from fastapi.testclient import TestClient

    seed_data.run()
    with TestClient(app) as c:
        yield c
