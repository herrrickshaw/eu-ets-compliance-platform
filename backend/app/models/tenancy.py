"""Auth, multi-tenancy and shared organizations."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import _now, db_enum


# --------------------------------------------------------------------------
# Auth & multi-tenancy: every Organization belongs to exactly one Tenant
# (the billing/login boundary — a customer's account on the platform). A
# Tenant can in principle own several Organizations (a group with
# subsidiaries); the demo seeds one Tenant per Organization.
# --------------------------------------------------------------------------
class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(db_enum(UserRole), default=UserRole.MEMBER)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    tenant: Mapped[Tenant] = relationship()


# --------------------------------------------------------------------------
# Shared: organizations — every actor in the system is one of these
# --------------------------------------------------------------------------
class OrgType(str, enum.Enum):
    ETS_OPERATOR = "ets_operator"
    SHIPPING_COMPANY = "shipping_company"
    CBAM_DECLARANT = "cbam_declarant"
    CREDIT_DEVELOPER = "credit_developer"
    TRADER = "trader"
    VERIFIER = "verifier"
    REGULATOR = "regulator"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    org_type: Mapped[OrgType] = mapped_column(db_enum(OrgType), nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=True)
    lei_or_eori: Mapped[str] = mapped_column(String, nullable=True)

    tenant: Mapped[Tenant] = relationship()
