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
        ("Renewable energy with storage (stored component only)", models.Article6Category.MITIGATION, False),
        ("Solar thermal power", models.Article6Category.MITIGATION, False),
        ("Offshore wind", models.Article6Category.MITIGATION, False),
        ("Green hydrogen", models.Article6Category.MITIGATION, False),
        ("Compressed biogas", models.Article6Category.MITIGATION, False),
        ("Emerging mobility / fuel cells", models.Article6Category.MITIGATION, False),
        ("High-efficiency / high-end energy-efficiency technology", models.Article6Category.MITIGATION, True),
        ("Sustainable aviation fuel (SAF)", models.Article6Category.MITIGATION, False),
        ("Best Available Technologies (BAT) for hard-to-abate process improvement", models.Article6Category.MITIGATION, False),
        ("Tidal / ocean thermal / salt-gradient / wave / current energy", models.Article6Category.MITIGATION, False),
        ("HVDC transmission paired with renewable energy projects", models.Article6Category.MITIGATION, False),
        ("Green ammonia", models.Article6Category.ALTERNATE_MATERIALS, False),
        ("Carbon Capture, Utilization and Storage (CCUS)", models.Article6Category.REMOVAL, True),
    ]
    for name, category, also_offset in article6_activities:
        db.add(models.Article6EligibleActivity(category=category, name=name, also_ccts_offset_eligible=also_offset))

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
