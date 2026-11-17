"""CBAM calculations and shared queries (default-value mark-up, quarter windows, certificate
netting, phase-in factor lookup). Rule constants live in the seeded tables, not here."""
from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence

from sqlalchemy.orm import Session

from ... import models

DEFAULT_COUNTRY_KEY = "default"  # fallback country row in the CBAM default-value table
FULL_PHASE_IN_PCT = 100.0  # factor used when no phase-in schedule row exists


def marked_up_emissions(dv: Any, quantity_t: float) -> tuple[float, float]:
    """Direct/indirect embedded emissions (tCO2) for `quantity_t` tonnes using a default value
    row with its escalating mark-up, rounded to 3 dp."""
    factor_direct = dv.direct_emissions_factor * (1 + dv.markup_pct / 100)
    factor_indirect = dv.indirect_emissions_factor * (1 + dv.markup_pct / 100)
    return round(quantity_t * factor_direct, 3), round(quantity_t * factor_indirect, 3)


def find_default_value(db: Session, cn_code: str, country: str) -> Optional[models.CbamDefaultValue]:
    """Latest default value for the CN code and country, falling back to the 'default' country row."""
    for key in (country, DEFAULT_COUNTRY_KEY):
        dv = (
            db.query(models.CbamDefaultValue)
            .filter_by(cn_code=cn_code, country=key)
            .order_by(models.CbamDefaultValue.valid_from.desc())
            .first()
        )
        if dv is not None:
            return dv
    return None


def quarter_window(year: int, quarter: int) -> tuple[str, str]:
    """ISO date strings [start, end) for a calendar quarter."""
    start = f"{year}-{(quarter - 1) * 3 + 1:02d}-01"
    end = f"{year if quarter < 4 else year + 1}-{(quarter * 3) % 12 + 1:02d}-01"
    return start, end


def surrender_held_certificates(held_certs: Sequence[Any], total_emissions: float) -> float:
    """Net `total_emissions` off held certificates in order, marking fully used ones SURRENDERED.

    Returns the quantity surrendered (tCO2), capped at what is held."""
    available = sum(c.quantity_t_co2 for c in held_certs)
    surrendered = min(total_emissions, available)
    remaining = surrendered
    for c in held_certs:
        if remaining <= 0:
            break
        take = min(c.quantity_t_co2, remaining)
        if take >= c.quantity_t_co2:
            c.status = models.CbamCertificateStatus.SURRENDERED
        remaining -= take
    return surrendered


def total_embedded(imports: Iterable[Any]) -> float:
    """Sum of direct + indirect embedded emissions (tCO2) over imports."""
    return sum(i.direct_emissions_t + i.indirect_emissions_t for i in imports)


def tenant_declarant_ids(db: Session, tenant_org_ids: Sequence[int]) -> list[int]:
    rows = db.query(models.CbamDeclarant).filter(models.CbamDeclarant.org_id.in_(tenant_org_ids)).all()
    return [d.id for d in rows]


def imports_in_year(db: Session, declarant_ids: Sequence[int], year: int) -> list[models.CbamGoodsImport]:
    """Imports for the declarants dated within the calendar year ([] when there are no declarants)."""
    if not declarant_ids:
        return []
    return (
        db.query(models.CbamGoodsImport)
        .filter(
            models.CbamGoodsImport.declarant_id.in_(declarant_ids),
            models.CbamGoodsImport.import_date >= f"{year}-01-01",
            models.CbamGoodsImport.import_date < f"{year + 1}-01-01",
        )
        .all()
    )


def phase_in_for_year(db: Session, year: int) -> Optional[models.CbamPhaseInSchedule]:
    """Schedule row for the year, else the next later year, else the latest year on record."""
    schedule = db.query(models.CbamPhaseInSchedule).filter_by(year=year).first()
    if schedule is None:
        schedule = (
            db.query(models.CbamPhaseInSchedule)
            .filter(models.CbamPhaseInSchedule.year >= year)
            .order_by(models.CbamPhaseInSchedule.year)
            .first()
        )
        if schedule is None:
            schedule = db.query(models.CbamPhaseInSchedule).order_by(models.CbamPhaseInSchedule.year.desc()).first()
    return schedule


def latest_eua_price(db: Session) -> Optional[models.PriceHistory]:
    """Most recent seeded EUA price row (reference for CBAM certificate cost), or None."""
    eua = db.query(models.Instrument).filter_by(instrument_type=models.InstrumentType.EUA).first()
    if not eua:
        return None
    return (
        db.query(models.PriceHistory)
        .filter_by(instrument_id=eua.id)
        .order_by(models.PriceHistory.price_date.desc())
        .first()
    )
