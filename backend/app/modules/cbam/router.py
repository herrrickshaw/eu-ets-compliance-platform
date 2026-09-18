from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import models, schemas
from ...auth.deps import get_current_user, get_my_org_ids
from ...db import get_db

router = APIRouter(prefix="/api/cbam", tags=["CBAM"])


def _require_declarant_in_tenant(db: Session, declarant_id: int, tenant_id: int) -> models.CbamDeclarant:
    declarant = db.get(models.CbamDeclarant, declarant_id)
    if declarant is None:
        raise HTTPException(404, "Declarant not found")
    org = db.get(models.Organization, declarant.org_id)
    if org is None or org.tenant_id != tenant_id:
        raise HTTPException(403, "This declarant does not belong to your tenant")
    return declarant


@router.get("/declarants", response_model=list[schemas.CbamDeclarantOut])
def list_declarants(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    org_ids = get_my_org_ids(db, user.tenant_id)
    return db.query(models.CbamDeclarant).filter(models.CbamDeclarant.org_id.in_(org_ids)).all()


@router.get("/default-values", response_model=list[schemas.CbamDefaultValueOut])
def list_default_values(cn_code: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.CbamDefaultValue)
    if cn_code:
        q = q.filter(models.CbamDefaultValue.cn_code == cn_code)
    return q.all()


@router.get("/imports", response_model=list[schemas.CbamGoodsImportOut])
def list_imports(
    declarant_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    org_ids = get_my_org_ids(db, user.tenant_id)
    q = (
        db.query(models.CbamGoodsImport)
        .join(models.CbamDeclarant, models.CbamGoodsImport.declarant_id == models.CbamDeclarant.id)
        .filter(models.CbamDeclarant.org_id.in_(org_ids))
    )
    if declarant_id:
        q = q.filter(models.CbamGoodsImport.declarant_id == declarant_id)
    return q.all()


@router.post("/imports", response_model=schemas.CbamGoodsImportOut)
def create_import(
    req: schemas.CbamGoodsImportCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    """Trader Portal: declare an import consignment. Falls back to the EU default-value
    table (with its escalating mark-up) unless actual verified emissions are supplied —
    mirrors the CBAM Transitional Registry's 50%-default-value ceiling rule."""
    _require_declarant_in_tenant(db, req.declarant_id, user.tenant_id)

    if req.actual_direct_emissions_t is not None:
        direct_t = req.actual_direct_emissions_t
        indirect_t = req.actual_indirect_emissions_t or 0.0
        source = models.EmissionSource.ACTUAL_VERIFIED
    else:
        dv = (
            db.query(models.CbamDefaultValue)
            .filter_by(cn_code=req.cn_code, country=req.country_of_origin)
            .order_by(models.CbamDefaultValue.valid_from.desc())
            .first()
        )
        if dv is None:
            dv = (
                db.query(models.CbamDefaultValue)
                .filter_by(cn_code=req.cn_code, country="default")
                .order_by(models.CbamDefaultValue.valid_from.desc())
                .first()
            )
        if dv is None:
            raise HTTPException(404, f"No CBAM default value found for CN code {req.cn_code}")
        factor_direct = dv.direct_emissions_factor * (1 + dv.markup_pct / 100)
        factor_indirect = dv.indirect_emissions_factor * (1 + dv.markup_pct / 100)
        direct_t = round(req.quantity_t * factor_direct, 3)
        indirect_t = round(req.quantity_t * factor_indirect, 3)
        source = models.EmissionSource.DEFAULT_VALUE

    good_name = (
        db.query(models.CbamDefaultValue.good_name)
        .filter_by(cn_code=req.cn_code)
        .limit(1)
        .scalar()
        or req.cn_code
    )

    record = models.CbamGoodsImport(
        declarant_id=req.declarant_id,
        cn_code=req.cn_code,
        good_name=good_name,
        country_of_origin=req.country_of_origin,
        quantity_t=req.quantity_t,
        import_date=req.import_date,
        emission_source=source,
        direct_emissions_t=direct_t,
        indirect_emissions_t=indirect_t,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/declarations", response_model=list[schemas.CbamDeclarationOut])
def list_declarations(
    declarant_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    org_ids = get_my_org_ids(db, user.tenant_id)
    q = (
        db.query(models.CbamDeclaration)
        .join(models.CbamDeclarant, models.CbamDeclaration.declarant_id == models.CbamDeclarant.id)
        .filter(models.CbamDeclarant.org_id.in_(org_ids))
    )
    if declarant_id:
        q = q.filter(models.CbamDeclaration.declarant_id == declarant_id)
    return q.all()


@router.post("/declarations/{declarant_id}/{year}/{quarter}/reconcile", response_model=schemas.CbamDeclarationOut)
def reconcile_declaration(
    declarant_id: int,
    year: int,
    quarter: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Data Reconciliation for Monitoring & Control: roll up the quarter's imports
    into one declaration and net off certificates already held."""
    _require_declarant_in_tenant(db, declarant_id, user.tenant_id)

    imports = (
        db.query(models.CbamGoodsImport)
        .filter(
            models.CbamGoodsImport.declarant_id == declarant_id,
            models.CbamGoodsImport.import_date >= f"{year}-{(quarter - 1) * 3 + 1:02d}-01",
            models.CbamGoodsImport.import_date < f"{year if quarter < 4 else year + 1}-{(quarter * 3) % 12 + 1:02d}-01",
        )
        .all()
    )
    total_emissions = sum(i.direct_emissions_t + i.indirect_emissions_t for i in imports)

    held_certs = (
        db.query(models.CbamCertificate)
        .filter_by(declarant_id=declarant_id, status=models.CbamCertificateStatus.HELD)
        .all()
    )
    available_cert_qty = sum(c.quantity_t_co2 for c in held_certs)
    surrendered = min(total_emissions, available_cert_qty)

    remaining = surrendered
    for c in held_certs:
        if remaining <= 0:
            break
        take = min(c.quantity_t_co2, remaining)
        if take >= c.quantity_t_co2:
            c.status = models.CbamCertificateStatus.SURRENDERED
        remaining -= take

    decl = db.query(models.CbamDeclaration).filter_by(declarant_id=declarant_id, year=year, quarter=quarter).first()
    if decl is None:
        decl = models.CbamDeclaration(declarant_id=declarant_id, year=year, quarter=quarter, total_embedded_emissions_t=0)
        db.add(decl)

    decl.total_embedded_emissions_t = round(total_emissions, 3)
    decl.certificates_surrendered_t = round(surrendered, 3)
    decl.status = models.CbamDeclarationStatus.RECONCILED
    db.commit()
    db.refresh(decl)
    return decl


@router.get("/phase-in-schedule", response_model=list[schemas.CbamPhaseInScheduleOut])
def list_phase_in_schedule(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.CbamPhaseInSchedule).order_by(models.CbamPhaseInSchedule.year).all()


DEMAND_METHODOLOGY_NOTE = (
    "CBAM certificates are NOT volume-capped the way EU ETS allowances or voluntary carbon credits are — "
    "the EU sells as many as a declarant needs, priced weekly off the EUA auction average (Reg. (EU) "
    "2023/956 Art. 21). So there is no scarcity-driven supply-vs-demand gap to model here. The real gap is "
    "temporal: total_embedded_emissions_t is your full eventual liability (what you'll owe once free "
    "allocation to the equivalent EU ETS sector hits zero, in 2034); actual_obligation_t is what you "
    "actually owe this year, scaled by that year's cbam_factor_pct (2.5% in 2026, ramping to 100% by "
    "2034 per Reg. (EU) 2025/2083); deferred_liability_t is the difference — emissions you're not yet "
    "paying for, but will be as the phase-in advances. reference_price is this platform's latest seeded "
    "EUA price (illustrative, not a live feed) standing in for the weekly CBAM certificate price."
)


@router.get("/demand-analysis", response_model=schemas.CbamDemandAnalysisResponse)
def demand_analysis(year: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    org_ids = get_my_org_ids(db, user.tenant_id)
    declarant_ids = [
        d.id for d in db.query(models.CbamDeclarant).filter(models.CbamDeclarant.org_id.in_(org_ids)).all()
    ]

    imports = (
        db.query(models.CbamGoodsImport)
        .filter(
            models.CbamGoodsImport.declarant_id.in_(declarant_ids),
            models.CbamGoodsImport.import_date >= f"{year}-01-01",
            models.CbamGoodsImport.import_date < f"{year + 1}-01-01",
        )
        .all()
        if declarant_ids
        else []
    )
    total_embedded = sum(i.direct_emissions_t + i.indirect_emissions_t for i in imports)

    schedule = db.query(models.CbamPhaseInSchedule).filter_by(year=year).first()
    if schedule is None:
        schedule = (
            db.query(models.CbamPhaseInSchedule)
            .filter(models.CbamPhaseInSchedule.year >= year)
            .order_by(models.CbamPhaseInSchedule.year)
            .first()
        )
        if schedule is None:
            schedule = (
                db.query(models.CbamPhaseInSchedule).order_by(models.CbamPhaseInSchedule.year.desc()).first()
            )
    factor_pct = schedule.cbam_factor_pct if schedule else 100.0

    actual_obligation = total_embedded * (factor_pct / 100)
    deferred = total_embedded - actual_obligation

    eua = db.query(models.Instrument).filter_by(instrument_type=models.InstrumentType.EUA).first()
    latest_price = (
        db.query(models.PriceHistory)
        .filter_by(instrument_id=eua.id)
        .order_by(models.PriceHistory.price_date.desc())
        .first()
        if eua
        else None
    )

    return schemas.CbamDemandAnalysisResponse(
        year=year,
        declarant_count=len(declarant_ids),
        total_embedded_emissions_t=round(total_embedded, 3),
        cbam_factor_pct=factor_pct,
        actual_obligation_t=round(actual_obligation, 3),
        deferred_liability_t=round(deferred, 3),
        reference_price_eur_per_t=latest_price.price_eur if latest_price else None,
        reference_price_date=latest_price.price_date if latest_price else None,
        actual_obligation_cost_eur=round(actual_obligation * latest_price.price_eur, 2) if latest_price else None,
        full_liability_cost_eur=round(total_embedded * latest_price.price_eur, 2) if latest_price else None,
        methodology_note=DEMAND_METHODOLOGY_NOTE,
    )


@router.get("/demand-projection", response_model=schemas.CbamProjectionResponse)
def demand_projection(base_year: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Holds base_year's actual import volume constant and projects the obligation
    across the whole 2026-2034 phase-in schedule — the clearest way to see the ramp."""
    org_ids = get_my_org_ids(db, user.tenant_id)
    declarant_ids = [
        d.id for d in db.query(models.CbamDeclarant).filter(models.CbamDeclarant.org_id.in_(org_ids)).all()
    ]
    imports = (
        db.query(models.CbamGoodsImport)
        .filter(
            models.CbamGoodsImport.declarant_id.in_(declarant_ids),
            models.CbamGoodsImport.import_date >= f"{base_year}-01-01",
            models.CbamGoodsImport.import_date < f"{base_year + 1}-01-01",
        )
        .all()
        if declarant_ids
        else []
    )
    total_embedded = sum(i.direct_emissions_t + i.indirect_emissions_t for i in imports)

    eua = db.query(models.Instrument).filter_by(instrument_type=models.InstrumentType.EUA).first()
    latest_price = (
        db.query(models.PriceHistory)
        .filter_by(instrument_id=eua.id)
        .order_by(models.PriceHistory.price_date.desc())
        .first()
        if eua
        else None
    )
    price = latest_price.price_eur if latest_price else None

    schedule = db.query(models.CbamPhaseInSchedule).order_by(models.CbamPhaseInSchedule.year).all()
    years = [
        schemas.CbamProjectionYear(
            year=s.year,
            cbam_factor_pct=s.cbam_factor_pct,
            obligation_t=round(total_embedded * (s.cbam_factor_pct / 100), 3),
            obligation_cost_eur=round(total_embedded * (s.cbam_factor_pct / 100) * price, 2) if price else None,
        )
        for s in schedule
    ]

    return schemas.CbamProjectionResponse(
        base_year=base_year,
        total_embedded_emissions_t=round(total_embedded, 3),
        reference_price_eur_per_t=price,
        years=years,
        note=(
            f"Illustrative projection only: holds {base_year}'s actual embedded-emissions volume "
            "constant across every scheduled year — real import volumes and the EUA-linked certificate "
            "price will both move. Shows the shape of the phase-in ramp, not a forecast."
        ),
    )
