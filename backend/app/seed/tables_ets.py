"""Seed tables: ets (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .. import models

# ---- What the EU ETS system actually looks like at full scale, next to the 3-installation demo above ----
# All rows SECONDARY: sourced via ICAP's EU ETS policy summary (a well-maintained tracker, already
# used elsewhere in this platform for India CCTS research) and the EEA's own data-viewer page, both
# via WebFetch summarization rather than a primary document read page-by-page this session.
_SEC = models.SourceConfidence.SECONDARY

_ICAP_EU_ETS = "https://icapcarbonaction.com/en/ets/eu-emissions-trading-system-eu-ets"

_EEA_ETS_VIEWER = "https://www.eea.europa.eu/en/analysis/maps-and-charts/emissions-trading-viewer-1-dashboards"

ets_system_stats = [
    dict(category="system_scale", metric_label="EU ETS emissions cap — stationary installations + maritime",
         period="2026", value=1185.4, unit="Mt CO2e",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC,
         notes="2024/2025-specific cap figures were not separately available from this source; "
         "2026 is the nearest year with a clean published number."),
    dict(category="system_scale", metric_label="EU ETS emissions cap — aviation",
         period="2026", value=26.2, unit="Mt CO2e",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC, notes=None),
    dict(category="system_scale", metric_label="Share of total EU greenhouse gas emissions covered by EU ETS",
         period="2023", value=35, unit="% of EU total GHG emissions",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC, notes=None),
    dict(category="system_scale", metric_label="Stationary installations covered (active, current compliance year)",
         period="2024", value=8704, unit="installations",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC,
         notes="Distinct from the EEA data-viewer's >16,000 figure below -- that is a CUMULATIVE "
         "count across the whole 2005-2024 dataset (including installations that have since "
         "closed or exited the scheme), not the currently-active count for a single compliance "
         "year. Both figures are real, they just answer different questions -- not a contradiction."),
    dict(category="system_scale", metric_label="Aircraft operators covered",
         period="2024", value=393, unit="operators",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC, notes=None),
    dict(category="system_scale", metric_label="Shipping companies covered (EU ETS maritime extension)",
         period="2024", value=3313, unit="companies",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC,
         notes="Consistent with the '>3,000 shipping companies' figure already used on the "
         "Shipping MRV page, sourced there from the European Commission's COM(2025) 110 final."),
    dict(category="system_scale", metric_label="Installations tracked, cumulative (all-time, 2005-2024)",
         period="2005-2024 (cumulative, includes closed installations)", value=16000, unit="installations (approx.)",
         source_name="European Environment Agency (EEA), EU ETS data viewer page",
         source_url=_EEA_ETS_VIEWER, source_confidence=_SEC,
         notes="The EEA's own dashboard describes covering 'more than 16,000 stationary "
         "installations, 1,600 aircraft operators and 2,600 maritime operators' across its full "
         "2005-2024 dataset -- this is the all-time/cumulative figure, see the "
         "currently-active-installations row above for the single-year (2024) count."),
    dict(category="allocation", metric_label="Share of allowances distributed via auction",
         period="current trading phase", value=57, unit="% of allowances (up to)",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC, notes=None),
    dict(category="allocation", metric_label="Share of allowances freely allocated",
         period="current trading phase", value=43, unit="% of allowances (approx., remainder)",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC,
         notes="The complement of the auctioned share above, as stated directly by the same source."),
    dict(category="allocation", metric_label="Linear reduction factor (current phase)",
         period="2024-2027", value=4.3, unit="% per year (of 2008-2012 baseline emissions)",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC,
         notes="Up from 2.2%/yr for 2021-2023; rises again to 4.4%/yr from 2028 -- the cap "
         "shrinks faster each phase as the EU tightens toward its climate targets."),
    dict(category="market_stability_reserve", metric_label="MSR trigger threshold (surplus allowances)",
         period="ongoing", value=1096, unit="million allowances (surplus threshold)",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC,
         notes="When the total surplus of allowances in circulation exceeds this threshold, a "
         "share is automatically withdrawn from future auctions into the Market Stability Reserve."),
    dict(category="market_stability_reserve", metric_label="MSR annual withdrawal rate",
         period="ongoing", value=24, unit="% of surplus volume withdrawn/year",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC, notes=None),
    dict(category="compliance", metric_label="Non-compliance penalty",
         period="ongoing, 2013 base year, inflation-adjusted", value=100, unit="EUR/tCO2e",
         source_name="ICAP (International Carbon Action Partnership), EU ETS policy summary",
         source_url=_ICAP_EU_ETS, source_confidence=_SEC,
         notes="Charged per tonne for which no allowance was surrendered by the deadline -- this "
         "is IN ADDITION TO, not instead of, still having to surrender the missing allowances. "
         "This platform's own demo surrender workflow (Compliance & surrender table above) models "
         "the shortfall/deadline logic but not this penalty calculation."),
    dict(category="compliance", metric_label="Verified emissions, stationary installations",
         period="2024", value=920, unit="Mt CO2e",
         source_name="European Environment Agency (EEA) data, via search synthesis, not read directly this session",
         source_url=_EEA_ETS_VIEWER, source_confidence=_SEC,
         notes="Down 5.7% year-on-year -- largely driven by the power sector, where renewable "
         "electricity generation (mainly wind and solar) rose substantially while coal and gas "
         "generation both fell."),
]
