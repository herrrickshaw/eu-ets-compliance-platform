"""Illustrative/sample seed data — NOT live regulatory or market data.

EUA prices, CBAM default values, and vessel/installation figures below are
representative of real published ranges (e.g. EUA ~EUR 60-90/t through 2025-26,
CBAM default-value mark-ups of 10/20/30% for 2026/27/28) but are hand-picked for
demo purposes, not pulled from a live feed or the EU's actual regulation text.
Run: python -m app.seed.seed_data
"""
from __future__ import annotations

import random
import re
from datetime import date, datetime, timedelta

from .. import models
from ..auth.security import hash_password
from ..db import Base, SessionLocal, engine

random.seed(42)

DEMO_PASSWORD = "demo1234"


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def run():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

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

    orgs = {}
    credentials = []
    for key, spec in org_specs.items():
        slug = _slugify(spec["name"])
        tenant = models.Tenant(name=spec["name"], slug=slug)
        db.add(tenant)
        db.flush()

        email = f"demo@{slug}.example"
        user = models.User(
            tenant_id=tenant.id, email=email, hashed_password=hash_password(DEMO_PASSWORD), role=models.UserRole.OWNER
        )
        db.add(user)

        org = models.Organization(tenant_id=tenant.id, **spec)
        db.add(org)
        db.flush()
        orgs[key] = org
        credentials.append((spec["name"], email, DEMO_PASSWORD))
    db.flush()

    # ---------------- Module 1: EU ETS core ----------------
    steel = models.Installation(org_id=orgs["steelco"].id, name="Nordic Steelworks — Lulea Plant", country="SE", sector="steel", ets_scheme="EU_ETS_1")
    cement = models.Installation(org_id=orgs["cementco"].id, name="Danube Cement — Linz Works", country="AT", sector="cement", ets_scheme="EU_ETS_1")
    power = models.Installation(org_id=orgs["powerco"].id, name="Rhine Power — Duisburg CCGT", country="DE", sector="power", ets_scheme="EU_ETS_1")
    for i in (steel, cement, power):
        db.add(i)
    db.flush()

    accounts = {}
    compliance_rows = []
    install_data = [
        (steel, orgs["steelco"], 2025, 480_000, 300_000, 250_000),
        (cement, orgs["cementco"], 2025, 210_000, 150_000, 210_000),
        (power, orgs["powerco"], 2025, 1_250_000, 50_000, 900_000),
    ]
    for installation, org, year, verified_emissions, free_alloc, held_eua in install_data:
        acct = models.AllowanceAccount(
            org_id=org.id,
            installation_id=installation.id,
            account_type=models.AccountType.OPERATOR_HOLDING,
            instrument="EUA",
            balance=held_eua + free_alloc,
        )
        db.add(acct)
        db.flush()
        accounts[installation.id] = acct
        db.add(
            models.AllowanceTransaction(
                account_id=acct.id,
                txn_type=models.AllowanceTxnType.FREE_ALLOCATION,
                amount=free_alloc,
                compliance_year=year,
            )
        )
        compliance_rows.append(
            models.ComplianceStatus(
                installation_id=installation.id,
                year=year,
                verified_emissions_t=verified_emissions,
                free_allocation_t=free_alloc,
                allowances_surrendered_t=0,
                surrender_deadline=date(year + 1, 9, 30),  # EU ETS surrender deadline, year N+1
                status="open",
            )
        )
    db.add_all(compliance_rows)
    db.flush()

    # ---------------- Module 2: Shipping MRV ----------------
    vessel1 = models.Vessel(org_id=orgs["shipco"].id, imo_number="9811000", name="MV Hanseatic Voyager", vessel_type="container", gross_tonnage=98_500)
    vessel2 = models.Vessel(org_id=orgs["tankerco"].id, imo_number="9744231", name="MT Aegean Horizon", vessel_type="tanker", gross_tonnage=61_200)
    db.add_all([vessel1, vessel2])
    db.flush()

    db.add_all(
        [
            models.MonitoringPlan(vessel_id=vessel1.id, version=2, status=models.MonitoringPlanStatus.APPROVED, submitted_at=datetime(2025, 1, 15)),
            models.MonitoringPlan(vessel_id=vessel2.id, version=1, status=models.MonitoringPlanStatus.APPROVED, submitted_at=datetime(2025, 2, 3)),
        ]
    )

    routes = [
        ("Rotterdam", "Hamburg", True, 280, 45),
        ("Hamburg", "Shanghai", False, 10_500, 1_850),
        ("Shanghai", "Rotterdam", False, 11_200, 1_920),
        ("Rotterdam", "Piraeus", True, 3_100, 520),
        ("Piraeus", "Istanbul", False, 380, 60),
    ]
    voyage_id_by_vessel = {vessel1.id: [], vessel2.id: []}
    for vid in (vessel1.id, vessel2.id):
        t = datetime(2025, 1, 5)
        for dep, arr, intra, dist, fuel in routes:
            voyage = models.Voyage(
                vessel_id=vid,
                departure_port=dep,
                arrival_port=arr,
                departure_time=t,
                arrival_time=t + timedelta(days=max(1, dist // 400)),
                distance_nm=dist,
                fuel_type="VLSFO",
                fuel_consumed_mt=fuel * random.uniform(0.9, 1.1),
                intra_eu=intra,
            )
            db.add(voyage)
            t += timedelta(days=max(1, dist // 400) + 3)
    db.flush()

    # ---------------- Module 3: CBAM ----------------
    declarant1 = models.CbamDeclarant(org_id=orgs["importer1"].id, eori_number="ES1234567890", auth_status=models.CbamAuthStatus.AUTHORISED)
    declarant2 = models.CbamDeclarant(org_id=orgs["importer2"].id, eori_number="LT9876543210", auth_status=models.CbamAuthStatus.AUTHORISED)
    db.add_all([declarant1, declarant2])
    db.flush()

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
    for cn, name, country, direct, indirect, markup, valid_from in default_values:
        db.add(
            models.CbamDefaultValue(
                cn_code=cn, good_name=name, country=country,
                direct_emissions_factor=direct, indirect_emissions_factor=indirect,
                markup_pct=markup, valid_from=valid_from,
            )
        )
    db.flush()

    imports = [
        (declarant1, "7208", "CN", 1_200, date(2026, 2, 10)),
        (declarant1, "7601", "default", 450, date(2026, 2, 20)),
        (declarant2, "3102", "default", 3_000, date(2026, 2, 5)),
        (declarant2, "2523", "default", 800, date(2026, 3, 1)),
    ]
    for decl, cn, country, qty, imp_date in imports:
        dv = next(d for d in default_values if d[0] == cn and (d[2] == country or d[2] == "default"))
        _, name, _, direct, indirect, markup, _ = dv
        db.add(
            models.CbamGoodsImport(
                declarant_id=decl.id, cn_code=cn, good_name=name, country_of_origin=country,
                quantity_t=qty, import_date=imp_date, emission_source=models.EmissionSource.DEFAULT_VALUE,
                direct_emissions_t=round(qty * direct * (1 + markup / 100), 2),
                indirect_emissions_t=round(qty * indirect * (1 + markup / 100), 2),
            )
        )

    db.add(
        models.CbamCertificate(
            declarant_id=declarant1.id, quantity_t_co2=2_500, price_eur_per_t=68.5,
            purchase_date=date(2026, 1, 20), status=models.CbamCertificateStatus.HELD,
        )
    )
    db.add(
        models.CbamCertificate(
            declarant_id=declarant2.id, quantity_t_co2=10_000, price_eur_per_t=67.0,
            purchase_date=date(2026, 1, 25), status=models.CbamCertificateStatus.HELD,
        )
    )
    db.flush()

    # ---------------- Module 4: Carbon credit sourcing ----------------
    verra = models.CreditProgram(name="Verra (VCS)")
    gold_standard = models.CreditProgram(name="Gold Standard")
    db.add_all([verra, gold_standard])
    db.flush()

    meth1 = models.CreditMethodology(program_id=verra.id, name="REDD+ Avoided Deforestation", sector="forestry")
    meth2 = models.CreditMethodology(program_id=gold_standard.id, name="Improved Cookstoves", sector="household devices")
    db.add_all([meth1, meth2])
    db.flush()

    project1 = models.CreditProject(
        program_id=verra.id, methodology_id=meth1.id, developer_org_id=orgs["devco"].id,
        name="Rio Negro Basin REDD+ Project", country="BR", status=models.CreditProjectStatus.ISSUING,
    )
    project2 = models.CreditProject(
        program_id=gold_standard.id, methodology_id=meth2.id, developer_org_id=orgs["devco2"].id,
        name="Sahel Efficient Cookstoves Programme", country="KE", status=models.CreditProjectStatus.ISSUING,
    )
    db.add_all([project1, project2])
    db.flush()

    issuance1 = models.CreditIssuance(project_id=project1.id, vintage_year=2025, quantity=50_000, issuance_date=date(2026, 1, 10))
    issuance2 = models.CreditIssuance(project_id=project2.id, vintage_year=2025, quantity=20_000, issuance_date=date(2026, 2, 1))
    db.add_all([issuance1, issuance2])
    db.flush()

    credit_units = []
    for i in range(6):
        credit_units.append(
            models.CreditUnit(issuance_id=issuance1.id, quantity=2_000, status=models.CreditUnitStatus.ISSUED, current_owner_org_id=orgs["devco"].id)
        )
    for i in range(4):
        credit_units.append(
            models.CreditUnit(issuance_id=issuance2.id, quantity=1_500, status=models.CreditUnitStatus.STAGED, current_owner_org_id=orgs["devco2"].id)
        )
    db.add_all(credit_units)
    db.flush()

    # ---------------- Module 5: Verification ----------------
    db.add(
        models.VerificationRecord(
            subject_type=models.VerificationSubjectType.CREDIT_UNIT_BATCH,
            subject_id=credit_units[-1].id,
            verifier_org_id=orgs["verifier1"].id,
            status=models.VerificationStatus.PENDING,
        )
    )
    db.add(
        models.VerificationRecord(
            subject_type=models.VerificationSubjectType.INSTALLATION_COMPLIANCE,
            subject_id=power.id,
            verifier_org_id=orgs["verifier2"].id,
            status=models.VerificationStatus.PENDING,
        )
    )
    db.flush()

    # ---------------- Module 6: Trading ----------------
    eua = models.Instrument(instrument_type=models.InstrumentType.EUA, symbol="EUA-DEC26")
    cbam_cert = models.Instrument(instrument_type=models.InstrumentType.CBAM_CERTIFICATE, symbol="CBAM-CERT")
    vcs_credit = models.Instrument(instrument_type=models.InstrumentType.VOLUNTARY_CREDIT, symbol="VCS-REDD-BR", reference_credit_project_id=project1.id)
    db.add_all([eua, cbam_cert, vcs_credit])
    db.flush()

    start_price = 68.0
    price = start_price
    d = date(2025, 9, 1)
    while d <= date(2026, 9, 1):
        price = max(45.0, price + random.uniform(-2.5, 2.5))
        db.add(models.PriceHistory(instrument_id=eua.id, price_date=d, price_eur=round(price, 2)))
        d += timedelta(days=7)

    cbam_price = 66.0
    d = date(2026, 1, 1)
    while d <= date(2026, 9, 1):
        cbam_price = max(40.0, cbam_price + random.uniform(-2.0, 2.0))
        db.add(models.PriceHistory(instrument_id=cbam_cert.id, price_date=d, price_eur=round(cbam_price, 2)))
        d += timedelta(days=7)

    vcs_price = 12.0
    d = date(2025, 9, 1)
    while d <= date(2026, 9, 1):
        vcs_price = max(4.0, vcs_price + random.uniform(-0.8, 0.8))
        db.add(models.PriceHistory(instrument_id=vcs_credit.id, price_date=d, price_eur=round(vcs_price, 2)))
        d += timedelta(days=7)

    db.flush()

    db.add(
        models.Order(org_id=orgs["trader2"].id, instrument_id=eua.id, side=models.OrderSide.SELL, quantity=5_000, limit_price_eur=69.5, status=models.OrderStatus.OPEN)
    )
    db.add(
        models.Order(org_id=orgs["powerco"].id, instrument_id=eua.id, side=models.OrderSide.SELL, quantity=2_000, limit_price_eur=70.0, status=models.OrderStatus.OPEN)
    )
    db.add(
        models.Order(org_id=orgs["trader1"].id, instrument_id=vcs_credit.id, side=models.OrderSide.SELL, quantity=1_500, limit_price_eur=11.0, status=models.OrderStatus.OPEN)
    )

    for org, instr, qty, cost in [
        (orgs["steelco"], eua, 250_000, 65.2),
        (orgs["cementco"], eua, 210_000, 64.8),
        (orgs["trader1"], vcs_credit, 3_000, 10.5),
    ]:
        db.add(models.Position(org_id=org.id, instrument_id=instr.id, quantity=qty, avg_cost_eur=cost))

    # ---------------- Module 7: India CCTS ----------------
    # Sourced from a Sept 2026 research pass (BEE/MoEFCC/ICAP/secondary reporting —
    # NOT a local repo, NOT a primary gazette text; see docs/INDIA_CCTS_SOURCES.md).
    # obligated_entities_est / target_reduction_pct_* / status / notification_ref are
    # sourced as noted per row. default_volume_mt / default_intensity_tco2_per_t are
    # illustrative editable assumptions (steel/aluminium/cement/fertilizer intensities
    # reused from this platform's own CBAM default-value table for consistency;
    # others are rough order-of-magnitude estimates) — NOT official BEE figures.
    india_sectors = [
        dict(
            key="aluminium", name="Aluminium", status=models.GeiStatus.FINAL,
            notification_ref="G.S.R. 739(E)", notification_date=date(2025, 10, 8),
            obligated_entities_est=None, target_reduction_pct_low=2.8, target_reduction_pct_high=7.06,
            target_reduction_pct_avg=4.9, default_volume_mt=4.1, default_intensity_tco2_per_t=10.15,
            source_confidence=models.SourceConfidence.SECONDARY,
            source_note="Part of a combined 282-entity announcement across 4 sectors (not broken out per "
            "sector in sources found). Intensity reused from this platform's CBAM aluminium default value.",
        ),
        dict(
            key="cement", name="Cement", status=models.GeiStatus.FINAL,
            notification_ref="G.S.R. 739(E)", notification_date=date(2025, 10, 8),
            obligated_entities_est=None, target_reduction_pct_low=4.7, target_reduction_pct_high=7.6,
            target_reduction_pct_avg=6.15, default_volume_mt=370, default_intensity_tco2_per_t=0.95,
            source_confidence=models.SourceConfidence.SECONDARY,
            source_note="Integrated plants ~2.7% / Grinding units ~6.6% per source; avg is the low-high "
            "midpoint. Part of the same combined 282-entity announcement. Intensity reused from this "
            "platform's CBAM cement default value.",
        ),
        dict(
            key="chlor_alkali", name="Chlor-Alkali", status=models.GeiStatus.FINAL,
            notification_ref="G.S.R. 739(E)", notification_date=date(2025, 10, 8),
            obligated_entities_est=None, target_reduction_pct_low=3.3, target_reduction_pct_high=11.0,
            target_reduction_pct_avg=6.5, default_volume_mt=4.5, default_intensity_tco2_per_t=1.8,
            source_confidence=models.SourceConfidence.SECONDARY,
            source_note="Part of the same combined 282-entity announcement. Volume/intensity are illustrative "
            "(no CBAM reference value available for this sector).",
        ),
        dict(
            key="pulp_paper", name="Pulp & Paper", status=models.GeiStatus.FINAL,
            notification_ref="G.S.R. 739(E)", notification_date=date(2025, 10, 8),
            obligated_entities_est=None, target_reduction_pct_low=None, target_reduction_pct_high=15.0,
            target_reduction_pct_avg=6.5, default_volume_mt=20, default_intensity_tco2_per_t=1.2,
            source_confidence=models.SourceConfidence.SECONDARY,
            source_note="Part of the same combined 282-entity announcement; low end of target range not "
            "found. Volume/intensity are illustrative.",
        ),
        dict(
            key="petroleum_refining", name="Petroleum Refining", status=models.GeiStatus.FINAL,
            notification_ref="MoEFCC notification", notification_date=date(2026, 1, 16),
            obligated_entities_est=None, target_reduction_pct_low=None, target_reduction_pct_high=None,
            target_reduction_pct_avg=3.1, default_volume_mt=254, default_intensity_tco2_per_t=0.3,
            source_confidence=models.SourceConfidence.SECONDARY,
            source_note="Part of a combined ~208-entity addition (petroleum refining + petrochemicals + "
            "textiles, not broken out individually) bringing the cumulative total to ~490 across 7 sectors. "
            "Volume/intensity are illustrative.",
        ),
        dict(
            key="petrochemicals", name="Petrochemicals", status=models.GeiStatus.FINAL,
            notification_ref="MoEFCC notification", notification_date=date(2026, 1, 16),
            obligated_entities_est=None, target_reduction_pct_low=None, target_reduction_pct_high=None,
            target_reduction_pct_avg=3.6, default_volume_mt=30, default_intensity_tco2_per_t=1.0,
            source_confidence=models.SourceConfidence.SECONDARY,
            source_note="Part of the same combined ~208-entity addition as petroleum refining/textiles. "
            "Volume/intensity are illustrative.",
        ),
        dict(
            key="textiles", name="Textiles", status=models.GeiStatus.FINAL,
            notification_ref="MoEFCC notification", notification_date=date(2026, 1, 16),
            obligated_entities_est=None, target_reduction_pct_low=None, target_reduction_pct_high=None,
            target_reduction_pct_avg=6.6, default_volume_mt=7, default_intensity_tco2_per_t=2.5,
            source_confidence=models.SourceConfidence.SECONDARY,
            source_note="Part of the same combined ~208-entity addition as petroleum refining/petrochemicals. "
            "Volume/intensity are illustrative.",
        ),
        dict(
            key="iron_steel", name="Iron & Steel", status=models.GeiStatus.DRAFT,
            notification_ref="Revised draft (not yet final)", notification_date=date(2026, 6, 26),
            obligated_entities_est=255, target_reduction_pct_low=2.0, target_reduction_pct_high=5.0,
            target_reduction_pct_avg=3.5, default_volume_mt=145, default_intensity_tco2_per_t=2.93,
            source_confidence=models.SourceConfidence.SECONDARY,
            source_note="255 units across 10 states; draft made public 2 Jul 2026 with a 60-day objection "
            "window (~through end-Aug 2026) — NOT yet legally binding as of this seed. Criticized by Climate "
            "Risk Horizons as too weak. Intensity reused from this platform's CBAM steel (India) default value.",
        ),
        dict(
            key="fertilizer", name="Fertilizer", status=models.GeiStatus.CONTESTED,
            notification_ref=None, notification_date=None,
            obligated_entities_est=20, target_reduction_pct_low=None, target_reduction_pct_high=None,
            target_reduction_pct_avg=None, default_volume_mt=30, default_intensity_tco2_per_t=4.1,
            source_confidence=models.SourceConfidence.MODELED,
            source_note="Status is genuinely contested across sources: one claims final gazette notification "
            "8 Oct 2025 alongside 4 other sectors, but ICAP's detailed CCTS page lists only 7 finalized "
            "sectors and does NOT include fertilizer. No confirmed target % found — do not treat as final. "
            "~20 plants anticipated (NFL, RCF, IFFCO, FACT, GSFC, KRIBHCO, Chambal). Intensity reused from "
            "this platform's CBAM fertilizer default value (reasonably close to one source's modeled "
            "2.2-3.1 tCO2e/t baseline estimate).",
        ),
    ]
    for spec in india_sectors:
        db.add(models.IndiaCctsSector(**spec))

    article6_activities = [
        ("re_storage", "Renewable energy with storage (stored component only)", models.Article6Category.MITIGATION, False),
        ("solar_thermal", "Solar thermal power", models.Article6Category.MITIGATION, False),
        ("offshore_wind", "Offshore wind", models.Article6Category.MITIGATION, False),
        ("green_hydrogen", "Green hydrogen", models.Article6Category.MITIGATION, False),
        ("cbg", "Compressed biogas", models.Article6Category.MITIGATION, False),
        ("mobility", "Emerging mobility / fuel cells", models.Article6Category.MITIGATION, False),
        ("energy_efficiency", "High-efficiency / high-end energy-efficiency technology", models.Article6Category.MITIGATION, True),
        ("saf", "Sustainable aviation fuel (SAF)", models.Article6Category.MITIGATION, False),
        ("bat_hard_to_abate", "Best Available Technologies (BAT) for hard-to-abate process improvement", models.Article6Category.MITIGATION, False),
        ("tidal", "Tidal / ocean thermal / salt-gradient / wave / current energy", models.Article6Category.MITIGATION, False),
        ("hvdc", "HVDC transmission paired with renewable energy projects", models.Article6Category.MITIGATION, False),
        ("green_ammonia", "Green ammonia", models.Article6Category.ALTERNATE_MATERIALS, False),
        ("ccus", "Carbon Capture, Utilization and Storage (CCUS)", models.Article6Category.REMOVAL, True),
    ]
    a6 = {}
    for key, name, category, also_offset in article6_activities:
        obj = models.Article6EligibleActivity(category=category, name=name, also_ccts_offset_eligible=also_offset)
        db.add(obj)
        db.flush()
        a6[key] = obj

    india_prices = [
        dict(
            market="Korea", instrument="KAU (K-ETS)", price_native=13750, currency="KRW",
            price_usd=9.53, price_eur=8.80, price_date=date(2026, 3, 1),
            trend_note="Up ~33% YTD 2026; 2025 secondary-market avg was KRW 9,393 (~$6.60). Recovering "
            "after years of oversupply; 2026-2030 phase cuts the cap ~12% (2.54 bn tCO2e).",
            source_confidence=models.SourceConfidence.SECONDARY,
        ),
        dict(
            market="China", instrument="CEA (national ETS)", price_native=83.86, currency="CNY",
            price_usd=11.0, price_eur=10.5, price_date=date(2026, 8, 31),
            trend_note="Jan-Aug 2026 average, peaking near CNY 100 late Aug; +14.4% YoY vs 2025 full-year "
            "avg of CNY 73.3/t. Rising as metals/cement sectors are folded into the national ETS.",
            source_confidence=models.SourceConfidence.SECONDARY,
        ),
        dict(
            market="Japan", instrument="J-Credit (energy efficiency)", price_native=4800, currency="JPY",
            price_usd=32.0, price_eur=30.0, price_date=date(2026, 4, 7),
            trend_note="Platts assessment. Voluntary scheme; usable for up to 10% of GX-ETS compliance.",
            source_confidence=models.SourceConfidence.SECONDARY,
        ),
        dict(
            market="Japan", instrument="J-Credit (forestry)", price_native=5300, currency="JPY",
            price_usd=35.0, price_eur=33.0, price_date=date(2026, 4, 7),
            trend_note="Platts assessment; one exchange listing showed forestry J-Credit at JPY 4,400 in "
            "Jul 2026 — prices vary meaningfully by listing venue.",
            source_confidence=models.SourceConfidence.SECONDARY,
        ),
        dict(
            market="Japan", instrument="GX-ETS allowance (mandatory, FY2026 corridor)", price_native=1700,
            price_native_high=4300, currency="JPY", price_usd=None, price_eur=None, price_date=date(2026, 4, 1),
            trend_note="NOT an observed trade price — a government-set floor/ceiling corridor; trading was "
            "described as absent a week into the mandatory phase. Policymakers reportedly considering a "
            "JPY 4,000-6,000/t band by 2027. J-Credit is the more usable real/observed Japan proxy for now.",
            source_confidence=models.SourceConfidence.SECONDARY,
        ),
        dict(
            market="EU", instrument="EUA (context)", price_native=83.80, currency="EUR",
            price_usd=None, price_eur=83.80, price_date=date(2026, 9, 7),
            trend_note="Range ~EUR 75.5-83.8/t through Sept 2026 (EUR 83.80 = highest since Jul 2026). Some "
            "2026 full-year forecasts cite ~EUR 104/t average — an unverified analyst forecast, not spot.",
            source_confidence=models.SourceConfidence.SECONDARY,
        ),
    ]
    for spec in india_prices:
        db.add(models.IndiaCarbonPriceComparison(**spec))

    # ---------------- India supply-capacity (Article 6.2 gap analysis) ----------------
    # Sourced from a Sept 2026 research pass reading primary PIB/MNRE/MoPNG/NITI Aayog/
    # steel.gov.in/BEE documents directly where noted; secondary trade-press cited only
    # where no primary figure could be located. A follow-up research pass reading the
    # actual CDM ACM0002 / Verra VMR0017 methodology text confirmed the correct baseline
    # factor for this kind of calculation is CEA's Combined Margin (CM) — not a simple
    # weighted average — so this uses CM = 0.736 tCO2/MWh (FY2024-25 vintage), from CEA
    # "CO2 Baseline Database for the Indian Power Sector v21.0", Nov 2025,
    # https://cea.nic.in/wp-content/uploads/baseline/2025/12/User_Guide_V_21.0.pdf
    # Capacity-factor assumptions below are a mix of: (a) real India national
    # fleet-average CUFs derived from MNRE's own capacity+generation statistics
    # (solar ~17.5-19%, wind ~20%; see docs/INDIA_CCTS_SOURCES.md and the
    # credit_benchmarks table for the full derivation), used where directly
    # applicable, and (b) illustrative assumptions for hybrid/enabling-infrastructure
    # rows (FDRE/RTC, the Ladakh corridor's solar+wind blend) where no direct
    # benchmark exists — each row's conversion_note says which.
    CEA_GRID_FACTOR = 0.736  # tCO2/MWh, Combined Margin, FY2024-25 vintage, CEA CO2 Baseline Database v21.0 (primary)

    AT = models.FigureType.ASPIRATIONAL_TARGET
    AO = models.FigureType.AWARDED_OPERATIONAL
    CA = models.FigureType.CURRENT_ACTUAL
    PRIMARY = models.SourceConfidence.PRIMARY
    SECONDARY = models.SourceConfidence.SECONDARY

    supply_rows = [
        # ---- Renewable energy with storage (FDRE) ----
        dict(
            activity_id=a6["re_storage"].id,
            metric_label="MNRE FDRE bidding trajectory (annual issuance target)",
            value=50, unit="GW/year (FY2023-24 to FY2027-28)", figure_type=AT,
            as_of_date=date(2026, 4, 2),
            source_name="PIB — Ministry of Power, Electricity Generation from Non-Conventional Sources",
            source_url="https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=2248342",
            source_confidence=PRIMARY,
            conversion_note="Annual issuance PACE, not a cumulative installed/awarded capacity figure — "
            "no aggregate GW-awarded total found on any primary source, so not converted to tCO2e.",
            potential_avoided_mt_co2e=None,
        ),
        dict(
            activity_id=a6["re_storage"].id,
            metric_label="SECI FDRE tenders awarded (illustrative sample, not exhaustive)",
            value=2.5, unit="GW (1.5 GW FDRE + 1 GW FDRE-RTC, 2026 tenders)", figure_type=AO,
            as_of_date=date(2026, 8, 7),
            source_name="pv-magazine India (secondary — SECI's own results page could not be reached)",
            source_url="https://www.pv-magazine-india.com/2026/08/07/secis-1-gw-fdre-rtc-power-tender-discovers-inr-5-25-kwh-tariff/",
            source_confidence=SECONDARY,
            conversion_note="2,500 MW x 35% capacity factor (illustrative — FDRE/RTC firm-power tenders "
            "typically run higher CF than plain solar, not India-specific-sourced) x 8,760 h x CEA "
            "Combined Margin 0.736 tCO2/MWh = 5.64 Mt CO2e/yr. This is only a sample of awarded tenders, "
            "not a complete national FDRE tally.",
            potential_avoided_mt_co2e=5.64,
        ),
        # ---- Solar thermal power ----
        dict(
            activity_id=a6["solar_thermal"].id,
            metric_label="Installed CSP (concentrated solar thermal) capacity",
            value=228.5, unit="MW (JNNSM Phase-I, 2014-15; effectively stalled since)", figure_type=CA,
            as_of_date=date(2015, 3, 31),
            source_name="MNRE Physical Achievements page (no current figure listed) / secondary reviews for the historical number",
            source_url="https://mnre.gov.in/en/physical-progress/",
            source_confidence=SECONDARY,
            conversion_note="MNRE's current CST page tracks only industrial-heat market potential (6.45 "
            "GWth), not power generation, and CSP is absent from MNRE's official installed-capacity table "
            "— confirming this is genuinely negligible today, not a data gap.",
            potential_avoided_mt_co2e=None,
        ),
        # ---- Offshore wind ----
        dict(
            activity_id=a6["offshore_wind"].id,
            metric_label="Cabinet-approved VGF offshore wind capacity",
            value=1000, unit="MW (500 MW Gujarat + 500 MW Tamil Nadu)", figure_type=AO,
            as_of_date=date(2024, 6, 19),
            source_name="PIB — Cabinet approves VGF scheme for Offshore Wind Energy Projects",
            source_url="https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2026700",
            source_confidence=PRIMARY,
            conversion_note="1,000 MW x 42% offshore capacity factor (real observed international offshore "
            "project range 42-46% — Norther Belgium 43.1%, Alpha Ventus Germany 42-42.7%, European fleet "
            "avg ~45.8%; India has no operational offshore wind to derive its own CF, so the international "
            "low end is used) x 8,760 h x CEA Combined Margin 0.736 tCO2/MWh = 2.71 Mt CO2e/yr. IMPORTANT: "
            "SECI's first 500 MW Gujarat tender (issued Sep 2024) drew ZERO bids by its extended Jul 2025 "
            "deadline — this capacity is funded/approved but nothing is under construction yet.",
            potential_avoided_mt_co2e=2.71,
        ),
        dict(
            activity_id=a6["offshore_wind"].id,
            metric_label="National offshore wind policy target",
            value=30, unit="GW by 2030", figure_type=AT,
            as_of_date=date(2018, 9, 1),
            source_name="MNRE offshore wind policy (widely reported; exact primary PIB URL not located)",
            source_url="https://mnre.gov.in/en/off-shore-wind/",
            source_confidence=SECONDARY,
            conversion_note="30,000 MW x 42% CF (same real international-project-derived assumption as "
            "above) x 8,760 h x CEA Combined Margin 0.736 tCO2/MWh = 81.2 Mt CO2e/yr IF fully built by "
            "2030. Given the first tender drew zero bids, treat this as a distant upper bound, not a "
            "plausible near-term figure.",
            potential_avoided_mt_co2e=81.2,
        ),
        # ---- Green hydrogen ----
        dict(
            activity_id=a6["green_hydrogen"].id,
            metric_label="Green hydrogen production capacity awarded (SIGHT scheme)",
            value=862000, unit="tonnes H2/year (19 companies, as of May 2025)", figure_type=AO,
            as_of_date=date(2025, 5, 1),
            source_name="PIB — Unlocking India's Green Hydrogen Production Potential",
            source_url="https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251112690301.pdf",
            source_confidence=PRIMARY,
            conversion_note="862,000 tH2/yr x 9.5 tCO2/tH2 grey-hydrogen (SMR) displacement factor "
            "(standard industry range 9-10 tCO2/tH2, midpoint used — not India-specific-sourced) = 8.19 "
            "Mt CO2e/yr. Most of this awarded capacity is still under construction, not yet producing.",
            potential_avoided_mt_co2e=8.19,
        ),
        dict(
            activity_id=a6["green_hydrogen"].id,
            metric_label="National Green Hydrogen Mission 2030 target",
            value=5_000_000, unit="tonnes H2/year by 2030", figure_type=AT,
            as_of_date=date(2025, 5, 1),
            source_name="PIB — Unlocking India's Green Hydrogen Production Potential",
            source_url="https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251112690301.pdf",
            source_confidence=PRIMARY,
            conversion_note="5 MMT/yr x 9.5 tCO2/tH2 = 47.5 Mt CO2e/yr IF fully built by 2030. Awarded "
            "capacity so far (862,000 t/yr, see above) is only ~17% of this target.",
            potential_avoided_mt_co2e=47.5,
        ),
        # ---- Compressed biogas ----
        dict(
            activity_id=a6["cbg"].id,
            metric_label="CBG plants commissioned (SATAT+MDA+BAM+DPI+CFA, cumulative)",
            value=200, unit="plants", figure_type=CA,
            as_of_date=date(2026, 8, 6),
            source_name="PIB — Cabinet approves GOBARdhan (National Unified Scheme for Compressed Biogas)",
            source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2295480",
            source_confidence=PRIMARY,
            conversion_note="Plant count only — no verified average per-plant output figure found to "
            "convert to tCO2e.",
            potential_avoided_mt_co2e=None,
        ),
        dict(
            activity_id=a6["cbg"].id,
            metric_label="Cumulative CBG output (secondary, unverified against a primary document)",
            value=920, unit="tonnes/day (~336,000 t/yr)", figure_type=CA,
            as_of_date=date(2026, 1, 1),
            source_name="Minister statement reported by Tribune/Energetica/Sunday Guardian",
            source_url=None,
            source_confidence=SECONDARY,
            conversion_note="920 t/day x 365 = 335,800 t/yr x 2.68 tCO2/t fossil-fuel-(CNG/diesel)-"
            "displacement factor (standard biomethane accounting convention, not India-specific-sourced) "
            "= 0.90 Mt CO2e/yr. Both the output figure and the conversion factor are unverified.",
            potential_avoided_mt_co2e=0.90,
        ),
        dict(
            activity_id=a6["cbg"].id,
            metric_label="GOBARdhan revised target",
            value=None, unit="~10x current production (no absolute baseline published)", figure_type=AT,
            as_of_date=date(2026, 8, 6),
            source_name="PIB — Cabinet approves GOBARdhan",
            source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2295480",
            source_confidence=PRIMARY,
            conversion_note="Cabinet states a 'nearly ten-fold' increase from current levels but does not "
            "restate an absolute MMT target (the old 15 MMT SATAT target appears superseded) — not "
            "quantifiable without an official baseline.",
            potential_avoided_mt_co2e=None,
        ),
        # ---- Emerging mobility / fuel cells ----
        dict(
            activity_id=a6["mobility"].id,
            metric_label="Sanctioned hydrogen mobility pilots",
            value=37, unit="vehicles (15 FCEV + 22 H2-ICE) + 9 refuelling stations", figure_type=AO,
            as_of_date=date(2025, 3, 3),
            source_name="PIB — MNRE hydrogen mobility pilot sanction",
            source_url="https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=2107795",
            source_confidence=PRIMARY,
            conversion_note="Pilot-scale (37 vehicles, ₹208 crore); not meaningfully quantifiable against "
            "sector-scale demand. Commissioning expected ~18-24 months from the Mar 2025 announcement.",
            potential_avoided_mt_co2e=None,
        ),
        # ---- High-efficiency / energy-efficiency technology (BEE PAT scheme) ----
        dict(
            activity_id=a6["energy_efficiency"].id,
            metric_label="PAT scheme cumulative energy savings",
            value=25.78, unit="Million toe cumulative (BEE dashboard, labeled 2025)", figure_type=CA,
            as_of_date=date(2025, 1, 1),
            source_name="BEE — Perform, Achieve and Trade (PAT) programme page",
            source_url="https://beeindia.gov.in/en/programmes/perform-achieve-and-trade-pat",
            source_confidence=PRIMARY,
            conversion_note="No matching current CO2-avoided figure is published alongside this "
            "energy-savings number; a toe-to-tCO2e conversion would require assuming a specific fuel mix "
            "and was not attempted to avoid fabricating false precision.",
            potential_avoided_mt_co2e=None,
        ),
        dict(
            activity_id=a6["energy_efficiency"].id,
            metric_label="PAT Cycle I+II CO2 avoided (dated, incomplete)",
            value=97.01, unit="Mt CO2 cumulative avoided, Cycles I-II only (2012-2019)", figure_type=CA,
            as_of_date=date(2022, 3, 29),
            source_name="PIB — Status of Implementation of NMEEE",
            source_url="https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1811051",
            source_confidence=PRIMARY,
            conversion_note="This is a CUMULATIVE figure since 2012 (a stock), not an annual rate — using "
            "it in an annual-basis gap analysis would misrepresent it. Cycles III-VII actuals (2019 "
            "onward) are missing from every source found. Excluded from the quantifiable total for this "
            "reason, not because the number itself is unsourced.",
            potential_avoided_mt_co2e=None,
        ),
        # ---- Sustainable Aviation Fuel ----
        dict(
            activity_id=a6["saf"].id,
            metric_label="SAF blending mandate volume (2028, 2% blend, international ops)",
            value=0.19, unit="MMT SAF/year (midpoint estimate)", figure_type=AT,
            as_of_date=date(2028, 1, 1),
            source_name="PIB (mandate) + PPAC Flash Report (ATF consumption baseline for conversion)",
            source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2163273",
            source_confidence=PRIMARY,
            conversion_note="0.19 MMT/yr x 3.16 tCO2/t (standard jet-fuel combustion factor) x 80% "
            "lifecycle-reduction assumption (typical ICAO/IATA SAF figure) = 0.48 Mt CO2e/yr. Both "
            "conversion factors are standard aviation-industry conventions, not verified in this "
            "India-specific research pass. Mandate applies to international operations only.",
            potential_avoided_mt_co2e=0.48,
        ),
        dict(
            activity_id=a6["saf"].id,
            metric_label="PIB's own stated SAF decarbonization potential",
            value=22.5, unit="Mt CO2/year (PIB's own claim, midpoint of 20-25)", figure_type=AT,
            as_of_date=date(2025, 9, 3),
            source_name="PIB — SAF a practical and immediate solution to decarbonize aviation",
            source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2163273",
            source_confidence=PRIMARY,
            conversion_note="A direct claim from the PIB release itself (not independently derived); "
            "adoption-rate/time-horizon assumptions behind the 20-25 Mt figure are unstated. Excluded "
            "from the quantifiable total to avoid double-counting with the mandate-derived row above — "
            "shown for context only.",
            potential_avoided_mt_co2e=None,
        ),
        # ---- BAT for hard-to-abate sectors ----
        dict(
            activity_id=a6["bat_hard_to_abate"].id,
            metric_label="Green Steel certified production (FY2025-26)",
            value=12.4, unit="MMT green steel (<2.2 tCO2e/tfs threshold), 90 units certified", figure_type=CA,
            as_of_date=date(2026, 3, 31),
            source_name="Ministry of Steel — Green Steel Initiative",
            source_url="https://steel.gov.in/green-steel-initiative",
            source_confidence=PRIMARY,
            conversion_note="A production-volume and intensity-THRESHOLD figure, not an avoided-emissions "
            "figure — converting it would require a counterfactual (non-green-steel) baseline intensity "
            "that isn't published. No aggregate national BAT-adoption abatement target exists for any "
            "hard-to-abate sector.",
            potential_avoided_mt_co2e=None,
        ),
        # ---- Tidal / ocean energy ----
        dict(
            activity_id=a6["tidal"].id,
            metric_label="Operational tidal/ocean energy capacity",
            value=0, unit="MW (both pilot attempts — 3.75 MW Sundarbans, 50 MW Gulf of Kutch — dropped)", figure_type=CA,
            as_of_date=date(2026, 1, 1),
            source_name="Secondary reporting (Down To Earth/Mongabay/Business Standard); no primary MNRE figure located",
            source_url=None,
            source_confidence=SECONDARY,
            conversion_note="Genuinely negligible — confirmed zero operational capacity, not a data gap. "
            "An MNRE Action Plan reportedly targets 100 MW demonstration by 2027 but could not be "
            "verified against a primary document this session.",
            potential_avoided_mt_co2e=0,
        ),
        # ---- HVDC transmission paired with renewables ----
        dict(
            activity_id=a6["hvdc"].id,
            metric_label="Ladakh Green Energy Corridor-II (RE capacity enabled)",
            value=13, unit="GW RE + 12 GWh BESS, 480 km HVDC line, targeted FY2029-30", figure_type=AO,
            as_of_date=date(2023, 10, 18),
            source_name="PIB — CCEA approves Green Energy Corridor Phase-II (Ladakh)",
            source_url="https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1968732",
            source_confidence=PRIMARY,
            conversion_note="13,000 MW x 19% blended solar+wind capacity factor (real India national "
            "fleet-average CUFs: solar ~17.5-19% MNRE-derived/regulatory benchmark, wind ~19.8-20% — "
            "averaged; Ladakh's own high-altitude solar resource could run higher but no site-specific "
            "figure was found) x 8,760 h x CEA Combined Margin 0.736 tCO2/MWh = 15.92 Mt CO2e/yr. "
            "Cabinet-approved and funded (₹20,773.70 crore, 40% CFA) — infrastructure under "
            "implementation, targeted completion FY2029-30, not yet operational.",
            potential_avoided_mt_co2e=15.92,
        ),
        # ---- Green ammonia ----
        dict(
            activity_id=a6["green_ammonia"].id,
            metric_label="SECI green ammonia procurement tendered (SIGHT Mode-2A)",
            value=724000, unit="tonnes/year (cumulative across 13 planned auctions)", figure_type=AO,
            as_of_date=date(2025, 8, 6),
            source_name="PIB — SECI conducts first-ever auction for Green Ammonia procurement",
            source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2153006",
            source_confidence=PRIMARY,
            conversion_note="724,000 t/yr x 2.0 tCO2/t grey-ammonia (SMR-based) displacement factor "
            "(typical range 1.8-2.4 tCO2/t, midpoint used — not India-specific-sourced) = 1.45 Mt CO2e/yr. "
            "Only the first 75,000 t/yr tranche (to Paradeep Phosphates, Aug 2025) has actually cleared; "
            "the remaining ~649,000 t/yr is still to be auctioned.",
            potential_avoided_mt_co2e=1.45,
        ),
        # ---- CCUS ----
        dict(
            activity_id=a6["ccus"].id,
            metric_label="NITI Aayog CCUS capture potential (2050)",
            value=750, unit="Mt CO2/year by 2050", figure_type=AT,
            as_of_date=date(2022, 11, 29),
            source_name="NITI Aayog — CCUS Policy Framework and Deployment Mechanism in India",
            source_url="https://www.niti.gov.in/sites/default/files/2022-11/CCUS-Report.pdf",
            source_confidence=PRIMARY,
            conversion_note="Already in the correct unit (Mt CO2/year captured) — no physical conversion "
            "needed. But this is a 2050-horizon target, 20+ years beyond the CCTS demand model's "
            "FY2025-27 window; including it in a near-term (or even a 2030-aspirational) gap analysis "
            "would be wildly misleading, so it is deliberately excluded from BOTH totals despite having a "
            "numeric value. No 2030-horizon CCUS figure exists from any source found.",
            potential_avoided_mt_co2e=None,
        ),
        dict(
            activity_id=a6["ccus"].id,
            metric_label="ONGC Gandhar CCS pilot (unverified against a primary MoPNG source)",
            value=100, unit="tonnes CO2/day captured (~36,500 t/yr)", figure_type=CA,
            as_of_date=date(2025, 6, 1),
            source_name="Trade press (Carbon Herald, iamrenew.com) citing ONGC statements",
            source_url=None,
            source_confidence=SECONDARY,
            conversion_note="100 t/day x 365 = 36,500 t/yr = 0.0365 Mt CO2e/yr. A single small pilot, not "
            "sector-scale — but the only near-term CCUS figure found anywhere, primary or secondary.",
            potential_avoided_mt_co2e=0.0365,
        ),
    ]
    for spec in supply_rows:
        db.add(models.IndiaSupplyCapacity(**spec))

    # ---------------- Credit benchmarks: capacity -> credits, per technology ----------------
    # Grounded in the REAL MRV formula (CDM ACM0002 / Verra VMR0017, adopted as-is by Gold
    # Standard): baseline emissions = actual metered generation (MWh) x grid emission factor
    # (tCO2/MWh). No registry publishes a default capacity factor — it's a project-specific
    # estimate, not a methodology parameter — so capacity_factor_pct below is the best
    # available REAL figure: either derived from MNRE's own official capacity+generation
    # statistics (Renewable Energy Statistics 2024-25), an official MNRE/CERC regulatory
    # tariff-setting benchmark, or a real operating project's observed output. Sourced from
    # a Sept 2026 research pass; see docs/INDIA_CCTS_SOURCES.md for full derivation and caveats.
    ACM0002_VMR0017 = "CDM ACM0002 / Verra VMR0017 (adopted as-is by Gold Standard): metered generation x grid emission factor"

    credit_benchmarks = [
        dict(
            technology="Solar PV", region="India (national fleet average, FY2024-25)",
            capacity_factor_pct=17.5, mwh_per_mw_per_year=1530,
            grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1126,
            methodology=ACM0002_VMR0017,
            source_name="MNRE Renewable Energy Statistics 2024-25 (capacity+generation, CUF derived) + CEA CO2 Baseline Database v21.0 (grid factor)",
            source_url="https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/11/202511061627678782.pdf",
            source_confidence=PRIMARY,
            notes="CUF is DERIVED by dividing MNRE's official FY2024-25 generation by average installed "
            "capacity — not an officially-published CUF table (none was found). Blends old+new plants "
            "and all site qualities; individual projects range ~14-26%+.",
        ),
        dict(
            technology="Solar PV", region="India (MNRE/CERC regulatory tariff-setting benchmark)",
            capacity_factor_pct=19.0, mwh_per_mw_per_year=1664,
            grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1225,
            methodology=ACM0002_VMR0017,
            source_name="MNRE/CERC regulatory CUF benchmark used in tariff determination",
            source_url=None,
            source_confidence=SECONDARY,
            notes="The 19% figure is widely cited as the regulatory benchmark used in Indian solar tariff "
            "determinations; CERC's Renewable Energy Tariff Regulations 2024 is the likely primary source "
            "but was not fetched directly in this research pass.",
        ),
        dict(
            technology="Solar PV", region="India — Kamuthi Solar Park, Tamil Nadu (real operating project)",
            capacity_factor_pct=23.8, mwh_per_mw_per_year=2083,
            grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1533,
            methodology=ACM0002_VMR0017,
            source_name="Kamuthi Solar Power Project (648 MWp, ~1.35 TWh/yr observed)",
            source_url="https://en.wikipedia.org/wiki/Kamuthi_Solar_Power_Project",
            source_confidence=SECONDARY,
            notes="A high-performing tracker-equipped real project, shown to illustrate the real range "
            "above the national fleet average — not a typical/default figure.",
        ),
        dict(
            technology="Onshore wind", region="India (national fleet average, FY2024-25)",
            capacity_factor_pct=19.8, mwh_per_mw_per_year=1735,
            grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1277,
            methodology=ACM0002_VMR0017,
            source_name="MNRE Renewable Energy Statistics 2024-25 (capacity+generation, CUF derived) + CEA CO2 Baseline Database v21.0",
            source_url="https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/11/202511061627678782.pdf",
            source_confidence=PRIMARY,
            notes="Derived the same way as the solar fleet average. Site-level range is wide (~12-30%+) — "
            "older CDM-era Tamil Nadu/Gujarat sites averaged only ~11.8-18.5%, modern tall-tower turbines "
            "in good wind-class sites do meaningfully better.",
        ),
        dict(
            technology="Small hydro", region="India (national fleet average, FY2024-25)",
            capacity_factor_pct=26.2, mwh_per_mw_per_year=2290,
            grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1685,
            methodology=ACM0002_VMR0017,
            source_name="MNRE Renewable Energy Statistics 2024-25",
            source_url="https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/11/202511061627678782.pdf",
            source_confidence=PRIMARY,
            notes="Derived the same way as solar/wind fleet averages.",
        ),
        dict(
            technology="Biomass / bagasse / waste-to-energy power", region="India (national fleet average, FY2024-25)",
            capacity_factor_pct=16.2, mwh_per_mw_per_year=1415,
            grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1041,
            methodology=ACM0002_VMR0017,
            source_name="MNRE Renewable Energy Statistics 2024-25",
            source_url="https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/11/202511061627678782.pdf",
            source_confidence=PRIMARY,
            notes="MNRE's 'bio-power' category conflates biomass, bagasse cogeneration, and "
            "waste-to-energy — a true biomass-only figure would differ. Some biomass sub-types may also "
            "need a small project-emissions (PEy) deduction for fossil co-firing/transport, not applied here.",
        ),
        dict(
            technology="Offshore wind", region="International (no operational India project to derive a local figure)",
            capacity_factor_pct=44.0, mwh_per_mw_per_year=3854,
            grid_emission_factor_tco2_per_mwh=None, tco2e_per_mw_per_year=None,
            methodology=ACM0002_VMR0017,
            source_name="Real operating farms: Norther (Belgium) 43.1%, Alpha Ventus (Germany) 42-42.7%, European offshore fleet avg ~45.8%",
            source_url="https://en.wikipedia.org/wiki/Norther_Offshore_Wind_Farm",
            source_confidence=SECONDARY,
            notes="Deliberately left without a tCO2e/MW figure: the grid emission factor to multiply by "
            "depends entirely on which country's grid the project sits under — there's no single 'global "
            "offshore' EF. Use the mwh_per_mw_per_year figure with whatever host-country grid factor applies.",
        ),
    ]
    for spec in credit_benchmarks:
        db.add(models.CreditBenchmark(**spec))

    db.commit()
    db.close()

    print("Seed complete.\n")
    print(f"Demo login — every tenant uses password: {DEMO_PASSWORD}\n")
    print(f"{'Tenant':40} {'Email':35}")
    for name, email, _ in credentials:
        print(f"{name:40} {email:35}")
    print(
        "\nSuggested demo logins: demo@nordic-steelworks-ab.example (EU ETS operator), "
        "demo@hanseatic-container-lines.example (shipping), demo@iberia-metals-import-sl.example (CBAM), "
        "demo@meridian-carbon-trading-llp.example (trader), demo@transeuro-verification-bureau.example (verifier)."
    )


if __name__ == "__main__":
    run()
