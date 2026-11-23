"""Replays tests/scenario.py against a seeded DB and compares with the pre-refactor golden file."""
from __future__ import annotations

import json
from pathlib import Path

from scenario import run_scenario

GOLDEN = Path(__file__).parent / "golden" / "api_baseline.json"


def test_api_matches_pre_refactor_baseline(client):
    result = json.loads(json.dumps(run_scenario(client), default=str))
    golden = json.loads(GOLDEN.read_text())
    assert result.keys() == golden.keys()
    for label in golden:
        assert result[label] == golden[label], label
