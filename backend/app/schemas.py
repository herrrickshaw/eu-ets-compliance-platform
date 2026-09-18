from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Auth / multi-tenancy ----
class TenantOut(OrmBase):
    id: int
    name: str
    slug: str


class UserOut(OrmBase):
    id: int
    tenant_id: int
    email: str
    role: str


class RegisterRequest(BaseModel):
    tenant_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    tenant: TenantOut


class MeResponse(BaseModel):
    user: UserOut
    tenant: TenantOut


# ---- Organizations ----
class OrganizationOut(OrmBase):
    id: int
    name: str
    org_type: str
    country: str | None
    lei_or_eori: str | None


# ---- ETS core ----
class InstallationOut(OrmBase):
    id: int
    org_id: int
    name: str
    country: str
    sector: str
    ets_scheme: str


class AllowanceAccountOut(OrmBase):
    id: int
    org_id: int
    installation_id: int | None
    account_type: str
    instrument: str
    balance: float


class ComplianceStatusOut(OrmBase):
    id: int
    installation_id: int
    year: int
    verified_emissions_t: float
    free_allocation_t: float
    allowances_surrendered_t: float
    surrender_deadline: date
    status: str


class SurrenderRequest(BaseModel):
    installation_id: int
    year: int
    amount_t: float


# ---- Shipping MRV ----
class VesselOut(OrmBase):
    id: int
    org_id: int
    imo_number: str
    name: str
    vessel_type: str
    gross_tonnage: float


class MonitoringPlanOut(OrmBase):
    id: int
    vessel_id: int
    version: int
    status: str
    methodology: str
    submitted_at: datetime | None


class VoyageOut(OrmBase):
    id: int
    vessel_id: int
    departure_port: str
    arrival_port: str
    departure_time: datetime
    arrival_time: datetime
    distance_nm: float
    fuel_type: str
    fuel_consumed_mt: float
    intra_eu: bool


class EmissionReportOut(OrmBase):
    id: int
    vessel_id: int
    year: int
    total_co2_t: float
    ets_eligible_co2_t: float
    status: str


class SubmitEmissionReportRequest(BaseModel):
    vessel_id: int
    year: int


# ---- CBAM ----
class CbamDeclarantOut(OrmBase):
    id: int
    org_id: int
    eori_number: str
    auth_status: str


class CbamDefaultValueOut(OrmBase):
    cn_code: str
    good_name: str
    country: str
    direct_emissions_factor: float
    indirect_emissions_factor: float
    markup_pct: float
    valid_from: date


class CbamGoodsImportOut(OrmBase):
    id: int
    declarant_id: int
    cn_code: str
    good_name: str
    country_of_origin: str
    quantity_t: float
    import_date: date
    emission_source: str
    direct_emissions_t: float
    indirect_emissions_t: float


class CbamGoodsImportCreate(BaseModel):
    declarant_id: int
    cn_code: str
    country_of_origin: str
    quantity_t: float
    import_date: date
    actual_direct_emissions_t: float | None = None
    actual_indirect_emissions_t: float | None = None


class CbamDeclarationOut(OrmBase):
    id: int
    declarant_id: int
    year: int
    quarter: int
    total_embedded_emissions_t: float
    certificates_surrendered_t: float
    status: str


class CbamPhaseInScheduleOut(OrmBase):
    id: int
    year: int
    free_allocation_pct: float
    cbam_factor_pct: float
    note: str | None


class CbamDemandAnalysisResponse(BaseModel):
    year: int
    declarant_count: int
    total_embedded_emissions_t: float  # full liability at 100% CBAM factor
    cbam_factor_pct: float
    actual_obligation_t: float
    deferred_liability_t: float
    reference_price_eur_per_t: float | None
    reference_price_date: date | None
    actual_obligation_cost_eur: float | None
    full_liability_cost_eur: float | None
    methodology_note: str


class CbamProjectionYear(BaseModel):
    year: int
    cbam_factor_pct: float
    obligation_t: float
    obligation_cost_eur: float | None


class CbamProjectionResponse(BaseModel):
    base_year: int
    total_embedded_emissions_t: float
    reference_price_eur_per_t: float | None
    years: list[CbamProjectionYear]
    note: str


# ---- Credits ----
class CreditProjectOut(OrmBase):
    id: int
    program_id: int
    methodology_id: int
    developer_org_id: int
    name: str
    country: str
    status: str


class CreditUnitOut(OrmBase):
    id: int
    issuance_id: int
    quantity: float
    status: str
    current_owner_org_id: int | None


class CreditPurchaseRequest(BaseModel):
    unit_id: int
    buyer_org_id: int


# ---- Verification ----
class VerificationRecordOut(OrmBase):
    id: int
    subject_type: str
    subject_id: int
    verifier_org_id: int
    status: str
    findings: str | None
    submitted_at: datetime
    resolved_at: datetime | None


class VerifyRequest(BaseModel):
    subject_type: str
    subject_id: int
    verifier_org_id: int
    approve: bool
    findings: str | None = None


# ---- Trading ----
class InstrumentOut(OrmBase):
    id: int
    instrument_type: str
    symbol: str
    reference_credit_project_id: int | None


class OrderOut(OrmBase):
    id: int
    org_id: int
    instrument_id: int
    side: str
    quantity: float
    limit_price_eur: float
    status: str
    created_at: datetime


class OrderCreate(BaseModel):
    org_id: int
    instrument_id: int
    side: str
    quantity: float
    limit_price_eur: float


class TradeOut(OrmBase):
    id: int
    buy_order_id: int
    sell_order_id: int
    instrument_id: int
    quantity: float
    price_eur: float
    executed_at: datetime


class PositionOut(OrmBase):
    id: int
    org_id: int
    instrument_id: int
    quantity: float
    avg_cost_eur: float


class PriceHistoryOut(OrmBase):
    price_date: date
    price_eur: float


# ---- India CCTS ----
class IndiaCctsSectorOut(OrmBase):
    id: int
    key: str
    name: str
    status: str
    notification_ref: str | None
    notification_date: date | None
    baseline_year: str
    compliance_years: str
    obligated_entities_est: int | None
    target_reduction_pct_low: float | None
    target_reduction_pct_high: float | None
    target_reduction_pct_avg: float | None
    default_volume_mt: float
    default_intensity_tco2_per_t: float
    source_confidence: str
    source_note: str | None


class SectorAssumptionOverride(BaseModel):
    sector_id: int
    volume_mt: float | None = None
    intensity_tco2_per_t: float | None = None


class DemandModelRequest(BaseModel):
    overrides: list[SectorAssumptionOverride] = []


class SectorDemandOut(BaseModel):
    sector_id: int
    sector_key: str
    sector_name: str
    status: str
    volume_mt: float
    intensity_tco2_per_t: float
    target_reduction_pct_avg: float
    baseline_emissions_mt_co2e: float
    illustrative_abatement_pool_mt_co2e: float


class DemandModelResponse(BaseModel):
    sectors: list[SectorDemandOut]
    total_illustrative_demand_mt_co2e: float
    methodology_note: str


class Article6ActivityOut(OrmBase):
    id: int
    category: str
    name: str
    also_ccts_offset_eligible: bool
    internationally_tradeable: bool
    notes: str | None


class IndiaCarbonPriceOut(OrmBase):
    id: int
    market: str
    instrument: str
    price_native: float
    price_native_high: float | None
    currency: str
    price_usd: float | None
    price_eur: float | None
    price_date: date
    trend_note: str | None
    source_confidence: str


class IndiaSupplyCapacityOut(OrmBase):
    id: int
    activity_id: int
    metric_label: str
    value: float | None
    unit: str
    figure_type: str
    as_of_date: date | None
    source_name: str
    source_url: str | None
    source_confidence: str
    conversion_note: str | None
    potential_avoided_mt_co2e: float | None


class CreditBenchmarkOut(OrmBase):
    id: int
    technology: str
    region: str
    capacity_factor_pct: float | None
    mwh_per_mw_per_year: float | None
    grid_emission_factor_tco2_per_mwh: float | None
    tco2e_per_mw_per_year: float | None
    methodology: str
    source_name: str
    source_url: str | None
    source_confidence: str
    notes: str | None


class CapacityToCreditsRequest(BaseModel):
    benchmark_id: int
    capacity_mw: float


class CapacityToCreditsResponse(BaseModel):
    benchmark: CreditBenchmarkOut
    capacity_mw: float
    estimated_annual_mwh: float | None
    estimated_annual_tco2e: float | None
    note: str


class GapAnalysisResponse(BaseModel):
    total_demand_mt_co2e: float
    total_near_term_supply_mt_co2e: float  # awarded_operational + current_actual rows only
    total_aspirational_supply_mt_co2e: float  # aspirational_target rows only — long-range upper bound, not available now
    near_term_gap_mt_co2e: float  # positive = demand exceeds near-term quantifiable supply
    supply_rows_excluded_no_conversion: list[str]
    demand_methodology_note: str
    supply_methodology_note: str
