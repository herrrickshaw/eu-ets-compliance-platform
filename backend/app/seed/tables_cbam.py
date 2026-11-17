"""Seed tables: cbam (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

default_values = [
    # cn_code, good_name, country, direct, indirect, markup_pct(2026), valid_from
    ("7208", "Hot-rolled steel", "default", 2.10, 0.35, 10.0, date(2026, 1, 1)),
    ("7208", "Hot-rolled steel", "CN", 2.60, 0.55, 10.0, date(2026, 1, 1)),
    ("7208", "Hot-rolled steel", "IN", 2.45, 0.48, 10.0, date(2026, 1, 1)),
    ("2523", "Portland cement", "default", 0.85, 0.10, 10.0, date(2026, 1, 1)),
    ("7601", "Unwrought aluminium", "default", 1.55, 8.60, 10.0, date(2026, 1, 1)),
    ("3102", "Nitrogen fertilizers", "default", 3.90, 0.20, 1.0, date(2026, 1, 1)),
    ("2804", "Hydrogen", "default", 9.00, 2.10, 10.0, date(2026, 1, 1)),
]

# CBAM phase-in schedule — Reg. (EU) 2023/956 Art. 31(a), as amended by the Omnibus
# Regulation (EU) 2025/2083 (17 Oct 2025, which also deferred CBAM certificate SALES
# from Jan 2026 to Feb 2027 and cut the quarterly certificate-holding buffer from 80%
# to 50% of estimated embedded emissions — buffer/timing details not modeled here,
# only the annual cbam_factor_pct that determines the surrender obligation itself).
# Cross-checked across multiple corroborating secondary sources (ICAP, cbamguide.com,
# OPIS); the primary Official Journal text was not read directly this session.
cbam_phase_in = [
    (2026, 97.5, 2.5, "First compliance year; certificate purchase itself deferred to Feb 2027 by the Omnibus amendment."),
    (2027, 95.0, 5.0, None),
    (2028, 90.0, 10.0, None),
    (2029, 77.5, 22.5, None),
    (2030, 51.5, 48.5, "Largest single-year jump in the schedule: +26 points from 2029."),
    (2031, 39.0, 61.0, None),
    (2032, 26.5, 73.5, None),
    (2033, 14.0, 86.0, None),
    (2034, 0.0, 100.0, "Free allocation to the equivalent EU ETS sector reaches zero — full embedded-emissions liability."),
]
