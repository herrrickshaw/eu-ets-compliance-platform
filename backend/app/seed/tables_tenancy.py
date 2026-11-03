"""Seed tables: tenancy (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .. import models

# ---------------- Tenants, users, organizations ----------------
# One Tenant (== one logged-in customer account) per Organization for this
# demo; a Tenant could in principle own several Organizations.
org_specs = {
    "steelco": dict(name="Nordic Steelworks AB", org_type=models.OrgType.ETS_OPERATOR, country="SE"),
    "cementco": dict(name="Danube Cement GmbH", org_type=models.OrgType.ETS_OPERATOR, country="AT"),
    "powerco": dict(name="Rhine Power Generation SE", org_type=models.OrgType.ETS_OPERATOR, country="DE"),
    "shipco": dict(name="Hanseatic Container Lines", org_type=models.OrgType.SHIPPING_COMPANY, country="DE"),
    "tankerco": dict(name="Aegean Tanker Group", org_type=models.OrgType.SHIPPING_COMPANY, country="GR"),
    "importer1": dict(name="Iberia Metals Import SL", org_type=models.OrgType.CBAM_DECLARANT, country="ES", lei_or_eori="ES1234567890"),
    "importer2": dict(name="Baltic Fertilizer Traders", org_type=models.OrgType.CBAM_DECLARANT, country="LT", lei_or_eori="LT9876543210"),
    "devco": dict(name="EquatorForest Carbon Ltd", org_type=models.OrgType.CREDIT_DEVELOPER, country="BR"),
    "devco2": dict(name="Sahel Cookstoves Initiative", org_type=models.OrgType.CREDIT_DEVELOPER, country="KE"),
    "trader1": dict(name="Meridian Carbon Trading LLP", org_type=models.OrgType.TRADER, country="GB"),
    "trader2": dict(name="Nordpool Emissions Desk", org_type=models.OrgType.TRADER, country="NO"),
    "verifier1": dict(name="TransEuro Verification Bureau", org_type=models.OrgType.VERIFIER, country="NL"),
    "verifier2": dict(name="Atlantic Classification & Assurance", org_type=models.OrgType.VERIFIER, country="FR"),
}
