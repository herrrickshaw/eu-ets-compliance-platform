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


@router.post("/demand-model", response_model=schemas.DemandModelResponse)
def demand_model(
    req: schemas.DemandModelRequest, db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)
):
    overrides = {o.sector_id: o for o in req.overrides}
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


@router.get("/article6-activities", response_model=list[schemas.Article6ActivityOut])
def list_article6_activities(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.Article6EligibleActivity).order_by(models.Article6EligibleActivity.category).all()


@router.get("/carbon-prices", response_model=list[schemas.IndiaCarbonPriceOut])
def list_carbon_prices(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.IndiaCarbonPriceComparison).order_by(models.IndiaCarbonPriceComparison.market).all()
