"""Characterisation: the seeded database dump and the OpenAPI schema must not change under refactors.

Digests were captured from the code before the seed/models split (password hashes and
wall-clock timestamps are normalised because they are random per run).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

SEED_DUMP_SHA256 = "595bccb3cbf498a56b3a1f7b392c12b8cae1bec0f635d630522d12411a0d7559"
OPENAPI_SHA256 = "251270c8cf8cc0c0c29cf8f5f30ec22d22e5f9e1cb1d6b55e634e06cfb441d84"


def _normalised_dump(path: str) -> str:
    con = sqlite3.connect(path)
    try:
        out = []
        for line in con.iterdump():
            line = re.sub(r"'\$2[abxy]\$[^']*'", "'<HASH>'", line)
            line = re.sub(r"'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.(?!000000')\d{6}'", "'<TS>'", line)
            # SQLite renders REALs with a version-dependent number of digits (3.54 prints shortest-repr, 3.46 prints
            # 20 digits in exponent form), so keep 12 significant digits to make the digest platform-independent.
            line = re.sub(r"(?<![\w.'])-?\d+\.\d{12,}(?:e[+-]\d+)?(?![\w'])", lambda m: format(float(m.group()), ".12g"), line)
            out.append(line)
        return "\n".join(out)
    finally:
        con.close()


def test_seeded_database_dump_is_unchanged(tmp_path):
    """Seed a throwaway DB in a subprocess (other tests mutate the shared one) and hash its dump."""
    db_path = tmp_path / "seed.db"
    backend = Path(__file__).resolve().parents[1] / "backend"
    env = {**os.environ, "CARBON_DB_PATH": str(db_path), "JWT_SECRET": "test-only-secret"}
    subprocess.run(
        [sys.executable, "-c", "from app.seed import seed_data; seed_data.run()"],
        cwd=backend, env=env, check=True, capture_output=True,
    )
    dump = _normalised_dump(str(db_path))
    assert hashlib.sha256(dump.encode()).hexdigest() == SEED_DUMP_SHA256


def test_openapi_schema_is_unchanged(client):
    text = json.dumps(client.get("/openapi.json").json(), indent=1)
    assert hashlib.sha256(text.encode()).hexdigest() == OPENAPI_SHA256
