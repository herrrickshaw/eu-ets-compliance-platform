"""Shared model helpers: enum column factory and UTC clock."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Enum,
)


def db_enum(enum_cls):
    """SQLAlchemy's Enum() stores the member .name by default; force .value
    (our lowercase strings) so API filters/schemas comparing against .value work."""
    return Enum(enum_cls, values_callable=lambda x: [e.value for e in x])


def _now() -> datetime:
    return datetime.utcnow()
