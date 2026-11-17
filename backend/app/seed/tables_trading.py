"""Seed tables: trading (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .tables_shipping import _P, _S

start_price = 68.0

# ---- What the REAL EUA/carbon-derivatives market looks like, next to the demo order book above ----
# Most rows PRIMARY: read directly from ICE's own 24 Jan 2025 press release, "ICE Announces Record
# Environmental Market Trading in 2024". 2025-year figures and the EEX/ICE structural note are
# SECONDARY -- search-synthesized, not read directly from ICE's follow-up 2025 release this session
# (that fetch was rate-limited).
_ICE_2024_RELEASE = "https://ir.theice.com/press/news-details/2025/ICE-Announces-Record-Environmental-Market-Trading-in-2024/default.aspx"

market_reality = [
    dict(category="ice_trading_volume", metric_label="ICE environmental futures/options contracts traded",
         period="2024", value=20.4, unit="million contracts",
         source_name="ICE (Intercontinental Exchange), press release, 24 Jan 2025", source_url=_ICE_2024_RELEASE,
         source_confidence=_P,
         notes="Record year, up ~40% YoY, with record average daily volume and participation. "
         "Covers ICE's full environmental portfolio (EUA, UKA, North American schemes, RECs, "
         "RINs, voluntary credits), not EUAs alone."),
    dict(category="ice_trading_volume", metric_label="ICE environmental markets notional value traded",
         period="2024", value=1, unit="USD trillion (at least; 4th consecutive year)",
         source_name="ICE (Intercontinental Exchange), press release, 24 Jan 2025", source_url=_ICE_2024_RELEASE,
         source_confidence=_P, notes=None),
    dict(category="ice_trading_volume", metric_label="ICE EUA + UKA futures/options, physically delivered value",
         period="2024", value=40, unit="USD billion",
         source_name="ICE (Intercontinental Exchange), press release, 24 Jan 2025", source_url=_ICE_2024_RELEASE,
         source_confidence=_P,
         notes="Combined EU Carbon Allowance (EUA) + UK Carbon Allowance (UKA) figure -- ICE's "
         "release does not break these two out separately. ICE describes its EUA futures/options "
         "as 'the world's most liquid carbon derivatives market.' Most contracts are cash-settled, "
         "not physically delivered -- this figure is specifically the physical-delivery subset."),
    dict(category="ice_trading_volume", metric_label="ICE cumulative carbon allowances traded (since launch)",
         period="cumulative, since launch to end-2024", value=166, unit="billion allowances",
         source_name="ICE (Intercontinental Exchange), press release, 24 Jan 2025", source_url=_ICE_2024_RELEASE,
         source_confidence=_P, notes="Across ICE's full global environmental portfolio, all allowance-type products combined."),
    dict(category="ice_trading_volume", metric_label="ICE cumulative voluntary carbon credits traded (since launch)",
         period="cumulative, since launch to end-2024", value=6, unit="billion credits",
         source_name="ICE (Intercontinental Exchange), press release, 24 Jan 2025", source_url=_ICE_2024_RELEASE,
         source_confidence=_P, notes=None),
    dict(category="market_structure", metric_label="Dominant EUA futures/options trading venue",
         period="ongoing", value=None, unit="qualitative",
         source_name="ICE press release (24 Jan 2025) + secondary market-structure reporting",
         source_url=_ICE_2024_RELEASE, source_confidence=_S,
         notes="EUA futures also list on EEX (European Energy Exchange, Leipzig), but the vast "
         "majority of EUA futures/options trading volume happens on ICE Futures Europe -- "
         "structurally different roles, not direct competition: EEX operates the EU's official "
         "primary auction platform (where new allowances first enter the market on behalf of the "
         "European Commission/member states), while ICE dominates secondary/derivatives trading. "
         "No precise ICE-vs-EEX volume percentage was found and verified this session -- 'vast "
         "majority' is the most specific claim the sources support."),
    dict(category="market_structure", metric_label="ICE environmental futures/options contracts traded",
         period="2025", value=20.9, unit="million contracts",
         source_name="ICE (Intercontinental Exchange), reported via search synthesis, not read directly this session",
         source_url="https://ir.theice.com/press/news-details/2026/ICEs-Environmental-Market-Trading-Reaches-Record-Highs-in-2025/default.aspx",
         source_confidence=_S,
         notes="Up ~4% vs. the 2024 record. The primary press release fetch was rate-limited (HTTP "
         "429) during this session's research -- this figure is via search summary only, not "
         "independently confirmed against the source document the way the 2024 figures above were."),
    dict(category="market_structure", metric_label="ICE environmental markets, physically delivered value",
         period="2025", value=117, unit="USD billion",
         source_name="ICE (Intercontinental Exchange), reported via search synthesis, not read directly this session",
         source_url="https://ir.theice.com/press/news-details/2026/ICEs-Environmental-Market-Trading-Reaches-Record-Highs-in-2025/default.aspx",
         source_confidence=_S, notes="5th consecutive year of $1 trillion+ notional value traded, per the same search summary."),
    dict(category="context", metric_label="Real-world EUA average price (for comparison against the demo instrument)",
         period="2024", value=64, unit="EUR/tCO2e",
         source_name="European Commission, COM(2025) 110 final, Section 6.1",
         source_url="https://climate.ec.europa.eu/document/download/1bb8387b-bdc4-4489-9d76-7ff30239704d_en?filename=First+report+on+the+implementation+of+the+ETS+extension+to+maritime+transport.pdf",
         source_confidence=_P,
         notes="This platform's own demo EUA instrument (EUA-DEC26, above) starts its simulated "
         "random-walk price series at EUR68/t -- deliberately close to this real 2024 average -- "
         "for orientation only, not a live price feed. Same primary source already used for the "
         "Shipping MRV compliance-cost figures."),
]
