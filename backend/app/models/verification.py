"""Module 5: Verification."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base
from .base import _now, db_enum


# --------------------------------------------------------------------------
# Module 5: Verification — cross-cutting stage/verify/commit workflow
# --------------------------------------------------------------------------
class VerificationSubjectType(str, enum.Enum):
    EMISSION_REPORT = "emission_report"
    CBAM_DECLARATION = "cbam_declaration"
    CREDIT_UNIT_BATCH = "credit_unit_batch"
    INSTALLATION_COMPLIANCE = "installation_compliance"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    VERIFIED = "verified"
    NON_CONFORMANCE = "non_conformance"


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_type: Mapped[VerificationSubjectType] = mapped_column(db_enum(VerificationSubjectType), nullable=False)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False)
    verifier_org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    status: Mapped[VerificationStatus] = mapped_column(db_enum(VerificationStatus), default=VerificationStatus.PENDING)
    findings: Mapped[str] = mapped_column(String, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
