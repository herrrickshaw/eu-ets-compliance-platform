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
from .tables_cbam import cbam_phase_in, default_values
from .tables_cbam_exposure import cbam_exposure
from .tables_credit_benchmarks import credit_benchmarks
from .tables_credits import market_stats
from .tables_ets import ets_system_stats
from .tables_india_ccts import article6_activities, india_prices, india_sectors
from .tables_india_supply import supply_rows
from .tables_shipping import ets_cost, routes
from .tables_tenancy import org_specs
from .tables_trading import market_reality, start_price
from .tables_verification import integrity_stats

random.seed(42)

DEMO_PASSWORD = "demo1234"


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _init_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    return db


def _seed_tenancy(db):
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

    return credentials, orgs


def _seed_ets(db, orgs):
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
    for spec in ets_system_stats:
        db.add(models.EtsCoreSystemStat(**spec))
    db.flush()

    return power


def _seed_shipping(db, orgs):
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
    for spec in ets_cost:
        db.add(models.ShippingEtsComplianceCost(**spec))
    db.flush()


def _seed_cbam(db, orgs):
    # ---------------- Module 3: CBAM ----------------
    declarant1 = models.CbamDeclarant(org_id=orgs["importer1"].id, eori_number="ES1234567890", auth_status=models.CbamAuthStatus.AUTHORISED)
    declarant2 = models.CbamDeclarant(org_id=orgs["importer2"].id, eori_number="LT9876543210", auth_status=models.CbamAuthStatus.AUTHORISED)
    db.add_all([declarant1, declarant2])
    db.flush()
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
    for year, free_pct, cbam_pct, note in cbam_phase_in:
        db.add(models.CbamPhaseInSchedule(year=year, free_allocation_pct=free_pct, cbam_factor_pct=cbam_pct, note=note))


def _seed_credits(db, orgs):
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
    for spec in market_stats:
        db.add(models.GlobalCarbonMarketStat(**spec))
    db.flush()

    return credit_units, project1


def _seed_verification(db, credit_units, orgs, power):
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
    for spec in integrity_stats:
        db.add(models.VerificationIntegrityStat(**spec))
    db.flush()


def _seed_trading(db, project1, orgs):
    # ---------------- Module 6: Trading ----------------
    eua = models.Instrument(instrument_type=models.InstrumentType.EUA, symbol="EUA-DEC26")
    cbam_cert = models.Instrument(instrument_type=models.InstrumentType.CBAM_CERTIFICATE, symbol="CBAM-CERT")
    vcs_credit = models.Instrument(instrument_type=models.InstrumentType.VOLUNTARY_CREDIT, symbol="VCS-REDD-BR", reference_credit_project_id=project1.id)
    db.add_all([eua, cbam_cert, vcs_credit])
    db.flush()
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
    for spec in market_reality:
        db.add(models.EuaTradingMarketStat(**spec))
    db.flush()


def _seed_india_ccts(db):
    for spec in india_sectors:
        db.add(models.IndiaCctsSector(**spec))
    a6 = {}
    for key, name, category, also_offset in article6_activities:
        obj = models.Article6EligibleActivity(
            category=category, name=name, also_ccts_offset_eligible=also_offset, internationally_tradeable=True
        )
        db.add(obj)
        db.flush()
        a6[key] = obj

    # Ethanol/1G biofuel — investigated (Sept 2026) and deliberately kept OUT of the
    # internationally-tradeable set. Confirmed two independent ways: MoEFCC's 13-category
    # Article 6.2 list, and the newly-mirrored India-Japan JCM eligible-activities list —
    # neither includes ethanol/liquid biofuel. Reasons: India's EBP/E20 blending is a
    # national MANDATE, so its reduction is business-as-usual, not additional; and there's
    # a real, documented food-security/ILUC-style controversy (maize's share of ethanol
    # feedstock rose from ~6% to ~50% of the feedstock mix in three years). Brazil's CBIOs,
    # the US's RINs/45Z/LCFS, and the EU's RED III biofuel mechanism are likewise domestic/
    # regional compliance instruments, not ITMOs, with no bilateral Article 6.2 channel to
    # India — none of those can be modeled as inbound international supply either.
    # Kept domestic-only: BEE's CCTS Offset Mechanism Phase 1 does cover the "energy" and
    # "agriculture" sectors ethanol production falls under, so it's plausibly eligible for
    # DOMESTIC obligated-entity compliance demand the same way CCUS/energy-efficiency are
    # marked also_ccts_offset_eligible below (sector-level eligibility, not a
    # methodology-confirmed one-to-one fit) — BEE's one bioenergy methodology (BM 001) as
    # currently written requires dedicated plantations, which doesn't cleanly cover India's
    # existing sugarcane/maize/rice feedstock base. 2G/cellulosic ethanol (non-food
    # feedstock) would fit BM 001 better; no evidence a dedicated methodology is imminent.
    a6["ethanol"] = models.Article6EligibleActivity(
        category=models.Article6Category.MITIGATION,
        name="Ethanol / 1G crop-based biofuel (India's EBP programme)",
        also_ccts_offset_eligible=True,
        internationally_tradeable=False,
        notes="Domestic-only: not on MoEFCC's Article 6.2 list (confirmed absent, and absent from the "
        "mirrored India-Japan JCM list too) — the EBP/E20 mandate fails the additionality test, and "
        "maize-feedstock diversion (6%->50% of feedstock in 3 years) raises a real food-security/ILUC "
        "concern. Sector-level domestic CCTS Offset eligibility (energy/agriculture) is plausible in "
        "principle, but BEE's one bioenergy methodology (BM 001) requires dedicated plantations, "
        "incompatible with India's existing sugarcane/maize/rice feedstock — not a clean methodology fit "
        "for 1G ethanol as it stands. Brazil's CBIOs, US RINs/45Z/LCFS, and the EU's RED III mechanism "
        "are domestic/regional compliance instruments, not internationally-transferable ITMOs, with no "
        "bilateral Article 6.2 channel to India — excluded as a source of inbound international supply "
        "for the same reason. 2G/cellulosic ethanol is a plausible future addition if BEE issues a "
        "dedicated methodology; no evidence this is imminent.",
    )
    db.add(a6["ethanol"])
    for spec in india_prices:
        db.add(models.IndiaCarbonPriceComparison(**spec))

    return a6


def _seed_india_supply(db, a6):
    for spec in supply_rows:
        spec = dict(spec)
        spec["activity_id"] = a6[spec.pop("activity_key")].id
        db.add(models.IndiaSupplyCapacity(**spec))


def _seed_credit_benchmarks(db):
    for spec in credit_benchmarks:
        db.add(models.CreditBenchmark(**spec))


def _seed_cbam_exposure(db):
    for spec in cbam_exposure:
        db.add(models.IndiaCbamExportExposure(**spec))


def _commit_and_report(db, credentials):
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


def run():
    db = _init_schema()
    credentials, orgs = _seed_tenancy(db)
    power = _seed_ets(db, orgs)
    _seed_shipping(db, orgs)
    _seed_cbam(db, orgs)
    credit_units, project1 = _seed_credits(db, orgs)
    _seed_verification(db, credit_units, orgs, power)
    _seed_trading(db, project1, orgs)
    a6 = _seed_india_ccts(db)
    _seed_india_supply(db, a6)
    _seed_credit_benchmarks(db)
    _seed_cbam_exposure(db)
    _commit_and_report(db, credentials)


if __name__ == "__main__":
    run()
