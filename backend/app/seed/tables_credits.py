"""Seed tables: credits (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .tables_shipping import _M, _P, _S

# ---- How big is the global carbon-credit market, and who has what share -----
# VCM rows are PRIMARY (Ecosystem Marketplace/Forest Trends' State of the Voluntary Carbon
# Market 2025, read directly). Compliance-market rows are SECONDARY (World Bank State and
# Trends of Carbon Pricing 2025, via search synthesis, not a primary document read directly
# in this session) -- confidence is marked honestly per row rather than uniformly.
_EM_SOVCM_2025 = "https://www.ecosystemmarketplace.com/publications/2025-state-of-the-voluntary-carbon-market-sovcm/"

_WB_CARBON_PRICING_2025 = "https://www.worldbank.org/en/publication/state-and-trends-of-carbon-pricing"

market_stats = [
    dict(category="compliance_market", metric_label="Global compliance carbon market notional value",
         period="2025", value=950, unit="USD billion",
         source_name="World Bank, State and Trends of Carbon Pricing 2025", source_url=_WB_CARBON_PRICING_2025,
         source_confidence=_S,
         notes="Mandatory cap-and-trade / baseline-and-credit systems only (EU ETS, China ETS, "
         "California, South Korea, etc.) -- excludes the voluntary market entirely, which is a "
         "separate, much smaller pool (see vcm_headline rows below)."),
    dict(category="compliance_market", metric_label="Global compliance carbon market coverage",
         period="2025", value=12, unit="Gt CO2e",
         source_name="World Bank, State and Trends of Carbon Pricing 2025", source_url=_WB_CARBON_PRICING_2025,
         source_confidence=_S, notes="Emissions covered by mandatory carbon-pricing instruments worldwide."),
    dict(category="compliance_market", metric_label="EU ETS share of global compliance market VALUE",
         period="2025", value=85, unit="% of global compliance value",
         source_name="Carbon Credits (secondary synthesis of World Bank/market data)",
         source_url="https://carboncredits.com/a-guide-to-compliance-carbon-credit-markets/",
         source_confidence=_S,
         notes="The EU ETS dominates by DOLLAR VALUE despite covering a minority of global "
         "compliance VOLUME (see next row) -- a high EUA price (~$80/tCO2e in 2025) against "
         "China's much lower ~$11/tCO2e explains most of the gap between value share and "
         "volume share."),
    dict(category="compliance_market", metric_label="EU ETS share of global compliance market VOLUME",
         period="2025", value=40, unit="% of global compliance volume",
         source_name="Carbon Credits (secondary synthesis of World Bank/market data)",
         source_url="https://carboncredits.com/a-guide-to-compliance-carbon-credit-markets/",
         source_confidence=_S,
         notes="China's national ETS covers more tonnage than any single scheme, including the "
         "EU's, but at a far lower price -- so it leads on volume while trailing badly on value."),
    dict(category="compliance_market", metric_label="EU ETS average allowance (EUA) price",
         period="2025 (first 9 months)", value=80, unit="USD/tCO2e",
         source_name="Carbon Credits (secondary synthesis)", source_url="https://carboncredits.com/a-guide-to-compliance-carbon-credit-markets/",
         source_confidence=_S, notes=None),
    dict(category="compliance_market", metric_label="China national ETS average price",
         period="2025", value=11, unit="USD/tCO2e",
         source_name="Carbon Credits (secondary synthesis)", source_url="https://carboncredits.com/a-guide-to-compliance-carbon-credit-markets/",
         source_confidence=_S, notes=None),
    dict(category="vcm_headline", metric_label="Voluntary carbon market (VCM) total transaction volume",
         period="2024", value=84.4, unit="Mt CO2e",
         source_name="Ecosystem Marketplace / Forest Trends, State of the Voluntary Carbon Market 2025",
         source_url=_EM_SOVCM_2025, source_confidence=_P,
         notes="Down 25% from 112.4 Mt in 2023 -- the third straight year of decline. This is a "
         "LOWER BOUND: EM's methodology is actual transaction data voluntarily reported by 82 "
         "market-participant respondents in 2024 (down from 97 in 2023), not a modeled total "
         "addressable market."),
    dict(category="vcm_headline", metric_label="Voluntary carbon market (VCM) total transaction value",
         period="2024", value=535.1, unit="USD million",
         source_name="Ecosystem Marketplace / Forest Trends, State of the Voluntary Carbon Market 2025",
         source_url=_EM_SOVCM_2025, source_confidence=_P,
         notes="Down 29% from $754.5M in 2023. Similar total value to 2020 ($534M) but achieved "
         "with only 40% of 2020's transaction volume, given higher average prices since."),
    dict(category="vcm_headline", metric_label="VCM average credit price",
         period="2024", value=6.34, unit="USD/tCO2e",
         source_name="Ecosystem Marketplace / Forest Trends, State of the Voluntary Carbon Market 2025",
         source_url=_EM_SOVCM_2025, source_confidence=_P,
         notes="Down 6% from $6.71 in 2023, but still more than double the 2020 average price "
         "-- prices have stayed structurally higher even as volume/value have fallen."),
    dict(category="vcm_headline", metric_label="VCM credits retired",
         period="2024", value=181.5, unit="Mt CO2e",
         source_name="Ecosystem Marketplace / Forest Trends, State of the Voluntary Carbon Market 2025",
         source_url=_EM_SOVCM_2025, source_confidence=_P,
         notes="Down only slightly from 189.4 Mt in 2023, and far more stable than transaction "
         "volume/value -- suggesting real end-user demand for offsetting has held up even as "
         "market liquidity/turnover has fallen. Retirements have exceeded new transactions for "
         "two straight years, implying inventories of the most sought-after credit types are "
         "shrinking."),
    dict(category="vcm_headline", metric_label="VCM cumulative transacted volume (all-time)",
         period="pre-2005 to 2024", value=2500, unit="Mt CO2e",
         source_name="Ecosystem Marketplace / Forest Trends, State of the Voluntary Carbon Market 2025",
         source_url=_EM_SOVCM_2025, source_confidence=_P, notes="~2.5 billion tonnes transacted since the market's earliest data."),
    dict(category="vcm_headline", metric_label="VCM cumulative transacted value (all-time)",
         period="pre-2005 to 2024", value=11_300, unit="USD million",
         source_name="Ecosystem Marketplace / Forest Trends, State of the Voluntary Carbon Market 2025",
         source_url=_EM_SOVCM_2025, source_confidence=_P, notes=None),
    dict(category="vcm_category_share", metric_label="Forestry & Land Use -- share of 2024 VCM value",
         period="2024", value=64.0, unit="% of VCM value",
         source_name="Ecosystem Marketplace / Forest Trends, State of the Voluntary Carbon Market 2025",
         source_url=_EM_SOVCM_2025, source_confidence=_P,
         notes="$342.5M of $535.1M total, 37.0 Mt volume -- the dominant VCM category, roughly "
         "flat YoY. Within it, REDD+ is still the largest sub-type by volume (13.6 Mt) but is "
         "losing share fast (-52% volume, -63% value YoY) while Improved Forest Management is "
         "growing explosively (+242% volume, +216% value) as buyers rotate toward it."),
    dict(category="vcm_category_share", metric_label="Renewable Energy -- share of 2024 VCM value",
         period="2024", value=11.1, unit="% of VCM value",
         source_name="Ecosystem Marketplace / Forest Trends, State of the Voluntary Carbon Market 2025",
         source_url=_EM_SOVCM_2025, source_confidence=_P,
         notes="$59.5M of $535.1M total, 22.3 Mt volume -- the second-largest category by volume "
         "but in steady decline (-23% volume, -48% value, -31% price YoY) as the category matures "
         "out of additionality concerns."),
    dict(category="vcm_category_share", metric_label="Removal-type credits -- share of 2024 VCM volume",
         period="2024", value=5, unit="% of VCM volume",
         source_name="Ecosystem Marketplace / Forest Trends, State of the Voluntary Carbon Market 2025",
         source_url=_EM_SOVCM_2025, source_confidence=_P,
         notes="Still a small minority of volume (vs. emission-reduction credits) despite "
         "carrying a 381% average price premium over reduction credits in 2024 (up from 245% in "
         "2023) -- a real and growing quality/scarcity premium, not yet matched by supply."),
    dict(category="context", metric_label="VCM value as a share of global compliance market value",
         period="2024/2025 (different reference years, see notes)", value=0.06, unit="% of compliance-market value",
         source_name="This platform's own calculation, not a published comparison figure",
         source_url=None, source_confidence=_M,
         notes="$535.1M (VCM, 2024) / $950,000M (global compliance markets, 2025) = ~0.056%, "
         "rounded to 0.06%. Combines two different sources on two different reference years "
         "(the closest available for each), so treat as an order-of-magnitude orientation, not a "
         "precise like-for-like ratio -- but the scale gap it illustrates (roughly three orders "
         "of magnitude) is real and not an artifact of the year mismatch: compliance markets are "
         "not a marginally bigger version of the VCM, they are a categorically different scale of "
         "market."),
]
