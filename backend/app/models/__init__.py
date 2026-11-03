"""
Shared data model for the whole platform.

Design borrows, deliberately, from real reference systems rather than inventing
a schema from scratch:
  - ETS core account/transaction shape  -> EU Union Registry
  - Shipping MRV workflow                -> EMSA THETIS-MRV state machine
  - CBAM sub-model split                 -> CBAM Transitional Registry
                                             (Trader Portal / Authorisation
                                             Management / Data Reconciliation)
  - Credit hierarchy + stage/verify/commit -> Chia-Network/cadt (CAD Trust)
  - Verification as a cross-cutting stage  -> cadt staged-write pattern,
                                             generalized across ETS/CBAM/credits
See docs/ARCHITECTURE.md for the full mapping and sources.
"""
from __future__ import annotations

from ..db import Base
from .base import (
    _now,
    db_enum,
)
from .cbam import (
    CbamAuthStatus,
    CbamCertificate,
    CbamCertificateStatus,
    CbamDeclarant,
    CbamDeclaration,
    CbamDeclarationStatus,
    CbamDefaultValue,
    CbamGoodsImport,
    CbamPhaseInSchedule,
    EmissionSource,
)
from .credits import (
    CreditIssuance,
    CreditMethodology,
    CreditProgram,
    CreditProject,
    CreditProjectStatus,
    CreditUnit,
    CreditUnitStatus,
)
from .ets import (
    AccountType,
    AllowanceAccount,
    AllowanceTransaction,
    AllowanceTxnType,
    ComplianceStatus,
    Installation,
)
from .india_ccts import (
    Article6Category,
    Article6EligibleActivity,
    CreditBenchmark,
    EtsCoreSystemStat,
    EuaTradingMarketStat,
    FigureType,
    GeiStatus,
    GlobalCarbonMarketStat,
    IndiaCarbonPriceComparison,
    IndiaCbamExportExposure,
    IndiaCctsSector,
    IndiaSupplyCapacity,
    ShippingEtsComplianceCost,
    SourceConfidence,
    VerificationIntegrityStat,
)
from .shipping import (
    EmissionReport,
    EmissionReportStatus,
    MonitoringPlan,
    MonitoringPlanStatus,
    Vessel,
    Voyage,
)
from .tenancy import (
    Organization,
    OrgType,
    Tenant,
    User,
    UserRole,
)
from .trading import (
    Instrument,
    InstrumentType,
    Order,
    OrderSide,
    OrderStatus,
    Position,
    PriceHistory,
    Trade,
)
from .verification import (
    VerificationRecord,
    VerificationStatus,
    VerificationSubjectType,
)

__all__ = [
    "Base",
    "db_enum",
    "_now",
    "Tenant",
    "UserRole",
    "User",
    "OrgType",
    "Organization",
    "Installation",
    "AccountType",
    "AllowanceAccount",
    "AllowanceTxnType",
    "AllowanceTransaction",
    "ComplianceStatus",
    "Vessel",
    "MonitoringPlanStatus",
    "MonitoringPlan",
    "Voyage",
    "EmissionReportStatus",
    "EmissionReport",
    "CbamAuthStatus",
    "CbamDeclarant",
    "CbamDefaultValue",
    "EmissionSource",
    "CbamGoodsImport",
    "CbamCertificateStatus",
    "CbamCertificate",
    "CbamDeclarationStatus",
    "CbamDeclaration",
    "CbamPhaseInSchedule",
    "CreditProgram",
    "CreditMethodology",
    "CreditProjectStatus",
    "CreditProject",
    "CreditIssuance",
    "CreditUnitStatus",
    "CreditUnit",
    "VerificationSubjectType",
    "VerificationStatus",
    "VerificationRecord",
    "InstrumentType",
    "Instrument",
    "OrderSide",
    "OrderStatus",
    "Order",
    "Trade",
    "Position",
    "PriceHistory",
    "GeiStatus",
    "SourceConfidence",
    "IndiaCctsSector",
    "Article6Category",
    "Article6EligibleActivity",
    "IndiaCarbonPriceComparison",
    "FigureType",
    "IndiaSupplyCapacity",
    "CreditBenchmark",
    "IndiaCbamExportExposure",
    "ShippingEtsComplianceCost",
    "GlobalCarbonMarketStat",
    "EuaTradingMarketStat",
    "EtsCoreSystemStat",
    "VerificationIntegrityStat",
]
