from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import models, schemas
from ...db import get_db

router = APIRouter(prefix="/api/verification", tags=["Verification"])


@router.get("/records", response_model=list[schemas.VerificationRecordOut])
def list_records(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.VerificationRecord)
    if status:
        q = q.filter(models.VerificationRecord.status == status)
    return q.all()


@router.post("/decide", response_model=schemas.VerificationRecordOut)
def decide(req: schemas.VerifyRequest, db: Session = Depends(get_db)):
    """Stage -> verify -> commit, generalized across subject types (cadt pattern).
    On approval this also advances the underlying subject's own state machine
    (e.g. EmissionReport -> DOC_ISSUED, mirroring THETIS-MRV's Document of Compliance)."""
    record = (
        db.query(models.VerificationRecord)
        .filter_by(subject_type=req.subject_type, subject_id=req.subject_id)
        .order_by(models.VerificationRecord.id.desc())
        .first()
    )
    if record is None:
        record = models.VerificationRecord(
            subject_type=req.subject_type,
            subject_id=req.subject_id,
            verifier_org_id=req.verifier_org_id,
        )
        db.add(record)

    record.status = models.VerificationStatus.VERIFIED if req.approve else models.VerificationStatus.NON_CONFORMANCE
    record.findings = req.findings
    record.resolved_at = datetime.utcnow()

    if req.approve:
        if req.subject_type == models.VerificationSubjectType.EMISSION_REPORT.value:
            report = db.query(models.EmissionReport).get(req.subject_id)
            if report:
                report.status = models.EmissionReportStatus.DOC_ISSUED
        elif req.subject_type == models.VerificationSubjectType.CREDIT_UNIT_BATCH.value:
            unit = db.query(models.CreditUnit).get(req.subject_id)
            if unit and unit.status == models.CreditUnitStatus.STAGED:
                unit.status = models.CreditUnitStatus.ISSUED

    db.commit()
    db.refresh(record)
    return record
