from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import models, schemas
from ...auth.deps import get_current_user, get_my_org_ids
from ...db import get_db

router = APIRouter(prefix="/api/shipping", tags=["Shipping MRV"])


@router.get("/vessels", response_model=list[schemas.VesselOut])
def list_vessels(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    org_ids = get_my_org_ids(db, user.tenant_id)
    return db.query(models.Vessel).filter(models.Vessel.org_id.in_(org_ids)).all()


@router.get("/monitoring-plans", response_model=list[schemas.MonitoringPlanOut])
def list_monitoring_plans(
    vessel_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    org_ids = get_my_org_ids(db, user.tenant_id)
    q = (
        db.query(models.MonitoringPlan)
        .join(models.Vessel, models.MonitoringPlan.vessel_id == models.Vessel.id)
        .filter(models.Vessel.org_id.in_(org_ids))
    )
    if vessel_id:
        q = q.filter(models.MonitoringPlan.vessel_id == vessel_id)
    return q.all()


@router.get("/voyages", response_model=list[schemas.VoyageOut])
def list_voyages(
    vessel_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    org_ids = get_my_org_ids(db, user.tenant_id)
    q = (
        db.query(models.Voyage)
        .join(models.Vessel, models.Voyage.vessel_id == models.Vessel.id)
        .filter(models.Vessel.org_id.in_(org_ids))
    )
    if vessel_id:
        q = q.filter(models.Voyage.vessel_id == vessel_id)
    return q.all()


@router.get("/emission-reports", response_model=list[schemas.EmissionReportOut])
def list_emission_reports(
    vessel_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    org_ids = get_my_org_ids(db, user.tenant_id)
    q = (
        db.query(models.EmissionReport)
        .join(models.Vessel, models.EmissionReport.vessel_id == models.Vessel.id)
        .filter(models.Vessel.org_id.in_(org_ids))
    )
    if vessel_id:
        q = q.filter(models.EmissionReport.vessel_id == vessel_id)
    return q.all()


@router.post("/emission-reports/submit", response_model=schemas.EmissionReportOut)
def submit_emission_report(
    req: schemas.SubmitEmissionReportRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Aggregate the year's voyages into a draft report, THETIS-MRV style: fuel -> CO2,
    weighting intra-EU legs at 100% ETS exposure and extra-EU legs at 50% (Art. 3ga MRV Reg)."""
    vessel = db.get(models.Vessel, req.vessel_id)
    if vessel is None:
        raise HTTPException(404, "Vessel not found")
    org = db.get(models.Organization, vessel.org_id)
    if org is None or org.tenant_id != user.tenant_id:
        raise HTTPException(403, "This vessel does not belong to your tenant")

    CO2_PER_TONNE_FUEL = 3.114  # IMO/EU standard VLSFO emission factor, tCO2 per tonne fuel

    voyages = (
        db.query(models.Voyage)
        .filter(
            models.Voyage.vessel_id == req.vessel_id,
            models.Voyage.departure_time >= datetime(req.year, 1, 1),
            models.Voyage.departure_time < datetime(req.year + 1, 1, 1),
        )
        .all()
    )
    if not voyages:
        raise HTTPException(404, "No voyages found for this vessel/year")

    total_co2 = sum(v.fuel_consumed_mt * CO2_PER_TONNE_FUEL for v in voyages)
    ets_eligible = sum(
        v.fuel_consumed_mt * CO2_PER_TONNE_FUEL * (1.0 if v.intra_eu else 0.5) for v in voyages
    )

    report = (
        db.query(models.EmissionReport)
        .filter_by(vessel_id=req.vessel_id, year=req.year)
        .first()
    )
    if report is None:
        report = models.EmissionReport(vessel_id=req.vessel_id, year=req.year, total_co2_t=0, ets_eligible_co2_t=0)
        db.add(report)

    report.total_co2_t = round(total_co2, 2)
    report.ets_eligible_co2_t = round(ets_eligible, 2)
    report.status = models.EmissionReportStatus.SUBMITTED
    db.commit()
    db.refresh(report)
    return report


@router.get("/ets-compliance-cost", response_model=list[schemas.ShippingEtsComplianceCostOut])
def list_ets_compliance_cost(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return (
        db.query(models.ShippingEtsComplianceCost)
        .order_by(models.ShippingEtsComplianceCost.category, models.ShippingEtsComplianceCost.id)
        .all()
    )
