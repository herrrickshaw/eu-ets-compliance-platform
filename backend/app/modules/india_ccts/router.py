from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import models, schemas
from ...auth.deps import get_current_user
from ...db import get_db

router = APIRouter(prefix="/api/india", tags=["India CCTS"])

METHODOLOGY_NOTE = (
    "Illustrative demand model, not an official BEE/MoEFCC figure: no public source publishes "
    "obligated-sector emissions or CCC demand in tCO2e. baseline_emissions = volume_mt x intensity "
    "(a rough national output at a per-sector baseline emission intensity); "
    "illustrative_abatement_pool = baseline_emissions x target_reduction_pct_avg, i.e. the scale of "
    "reduction obligated entities must find (organically or via CCC purchase) if they do not "
    "otherwise improve. Sector notification status/entity counts/target % are sourced (see "
    "source_note per sector); volume_mt and intensity_tco2_per_t are editable illustrative "
    "assumptions — override them via the overrides list to model your own scenario."
)


@router.get("/sectors", response_model=list[schemas.IndiaCctsSectorOut])
def list_sectors(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.IndiaCctsSector).order_by(models.IndiaCctsSector.name).all()


def _compute_demand(db: Session, overrides_list: list[schemas.SectorAssumptionOverride]) -> schemas.DemandModelResponse:
    overrides = {o.sector_id: o for o in overrides_list}
    sectors = db.query(models.IndiaCctsSector).order_by(models.IndiaCctsSector.name).all()

    rows = []
    total = 0.0
    for s in sectors:
        override = overrides.get(s.id)
        volume = (override.volume_mt if override and override.volume_mt is not None else s.default_volume_mt)
        intensity = (
            override.intensity_tco2_per_t
            if override and override.intensity_tco2_per_t is not None
            else s.default_intensity_tco2_per_t
        )
        target_pct = s.target_reduction_pct_avg or 0.0

        baseline_mt_co2e = volume * intensity
        pool_mt_co2e = baseline_mt_co2e * (target_pct / 100)
        total += pool_mt_co2e

        rows.append(
            schemas.SectorDemandOut(
                sector_id=s.id,
                sector_key=s.key,
                sector_name=s.name,
                status=s.status.value,
                volume_mt=volume,
                intensity_tco2_per_t=intensity,
                target_reduction_pct_avg=target_pct,
                baseline_emissions_mt_co2e=round(baseline_mt_co2e, 2),
                illustrative_abatement_pool_mt_co2e=round(pool_mt_co2e, 2),
            )
        )

    return schemas.DemandModelResponse(
        sectors=rows, total_illustrative_demand_mt_co2e=round(total, 2), methodology_note=METHODOLOGY_NOTE
    )


@router.post("/demand-model", response_model=schemas.DemandModelResponse)
def demand_model(
    req: schemas.DemandModelRequest, db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)
):
    return _compute_demand(db, req.overrides)


@router.get("/article6-activities", response_model=list[schemas.Article6ActivityOut])
def list_article6_activities(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.Article6EligibleActivity).order_by(models.Article6EligibleActivity.category).all()


@router.get("/carbon-prices", response_model=list[schemas.IndiaCarbonPriceOut])
def list_carbon_prices(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.IndiaCarbonPriceComparison).order_by(models.IndiaCarbonPriceComparison.market).all()


@router.get("/supply-capacity", response_model=list[schemas.IndiaSupplyCapacityOut])
def list_supply_capacity(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.IndiaSupplyCapacity).order_by(models.IndiaSupplyCapacity.activity_id).all()


SUPPLY_METHODOLOGY_NOTE = (
    "No official Article 6.2 pipeline volume (tCO2e) is published for India, so supply is proxied "
    "bottom-up from MNRE/MoPNG/PIB/CEA/BEE/NITI Aayog/Ministry of Steel capacity and target records per "
    "eligible activity. Each row is tagged aspirational_target (a 2030/2050-type policy goal, not yet "
    "built), awarded_operational (capacity actually awarded/funded/under construction/running), or "
    "current_actual (a measured to-date figure). near_term_supply sums only awarded_operational + "
    "current_actual rows — the honest 'what could plausibly deliver credits within the CCTS FY2025-27 "
    "compliance window' figure. aspirational_supply sums only aspirational_target rows separately — a "
    "long-range (2030, in one case 2050) upper bound, NOT available supply today; do not add it to "
    "near-term supply. Rows with no defensible physical-to-tCO2e conversion, or where the time horizon "
    "is too far out to be comparable at all (e.g. a 2050 CCUS target), are excluded entirely rather than "
    "zero-filled — see supply_rows_excluded_no_conversion and each row's conversion_note."
)


@router.post("/gap-analysis", response_model=schemas.GapAnalysisResponse)
def gap_analysis(
    req: schemas.DemandModelRequest, db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)
):
    demand = _compute_demand(db, req.overrides)

    supply_rows = db.query(models.IndiaSupplyCapacity).all()
    near_term_total = 0.0
    aspirational_total = 0.0
    excluded = []
    for row in supply_rows:
        if row.potential_avoided_mt_co2e is None:
            excluded.append(f"{row.metric_label} ({row.source_name})")
        elif row.figure_type == models.FigureType.ASPIRATIONAL_TARGET:
            aspirational_total += row.potential_avoided_mt_co2e
        else:
            near_term_total += row.potential_avoided_mt_co2e

    return schemas.GapAnalysisResponse(
        total_demand_mt_co2e=demand.total_illustrative_demand_mt_co2e,
        total_near_term_supply_mt_co2e=round(near_term_total, 2),
        total_aspirational_supply_mt_co2e=round(aspirational_total, 2),
        near_term_gap_mt_co2e=round(demand.total_illustrative_demand_mt_co2e - near_term_total, 2),
        supply_rows_excluded_no_conversion=excluded,
        demand_methodology_note=METHODOLOGY_NOTE,
        supply_methodology_note=SUPPLY_METHODOLOGY_NOTE,
    )


@router.get("/credit-benchmarks", response_model=list[schemas.CreditBenchmarkOut])
def list_credit_benchmarks(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.CreditBenchmark).order_by(models.CreditBenchmark.technology).all()


@router.post("/capacity-to-credits", response_model=schemas.CapacityToCreditsResponse)
def capacity_to_credits(
    req: schemas.CapacityToCreditsRequest, db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)
):
    """Real CDM ACM0002 / Verra VMR0017 formula: annual generation (MWh) x grid
    emission factor (tCO2/MWh). No registry defines a fixed default capacity
    factor — it's a project-specific estimate, not a methodology parameter — so
    this uses each benchmark's best-available real capacity-factor figure."""
    b = db.get(models.CreditBenchmark, req.benchmark_id)
    if b is None:
        raise HTTPException(404, "Benchmark not found")

    mwh = None
    tco2e = None
    if b.mwh_per_mw_per_year is not None:
        mwh = round(req.capacity_mw * b.mwh_per_mw_per_year, 2)
    if b.tco2e_per_mw_per_year is not None:
        tco2e = round(req.capacity_mw * b.tco2e_per_mw_per_year, 2)

    note = (
        f"{req.capacity_mw} MW x {b.mwh_per_mw_per_year or '?'} MWh/MW/yr "
        f"x {b.grid_emission_factor_tco2_per_mwh or '?'} tCO2/MWh ({b.methodology}). "
        "This is an estimate from a benchmark capacity factor, not metered generation — "
        "real crediting under ACM0002/VMR0017 always uses actual metered output."
    )
    return schemas.CapacityToCreditsResponse(
        benchmark=b, capacity_mw=req.capacity_mw, estimated_annual_mwh=mwh, estimated_annual_tco2e=tco2e, note=note
    )
