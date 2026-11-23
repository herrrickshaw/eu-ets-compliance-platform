"""Seed tables: cbam exposure (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .tables_india_supply import PRIMARY, SECONDARY

# ---------------- India's real CBAM export exposure ----------------
# Sept 2026 research pass. India's Tradestat/DGCIS portal (tradestat.commerce.gov.in)
# confirmed to be a JS-only form with no scrapable data endpoint (checked directly via
# curl, not assumed) -- so this is built from two Lok Sabha Unstarred Question answers
# (Ministry of Steel, sourced from the Joint Plant Committee/JPC -- primary), a
# corroborating PIB release, and GTRI (Global Trade Research Initiative) analysis for
# the more recent/aluminium figures (secondary, think-tank). Distinct from the toy
# CbamGoodsImport declarant data used elsewhere in the CBAM module demo.
cbam_exposure = [
    # ---- Iron & Steel (HS 72/73) -- primary, Lok Sabha USQ 3980, 25 Mar 2025 ----
    dict(product_category="Iron & Steel", hs_chapter="72/73", period="FY2019-20",
         export_value_usd=1.45e9, export_volume_tonnes=1_950_000, yoy_change_pct=None,
         source_name="Lok Sabha Unstarred Question 3980, Ministry of Steel (JPC data)",
         source_url="https://steel.gov.in/sites/default/files/2025-04/lu%203980.pdf",
         source_confidence=PRIMARY,
         notes="UK was part of the EU figure through 2020-21 per the official answer's own footnote -- "
         "this and the next row are not directly comparable to 2021-22 onward."),
    dict(product_category="Iron & Steel", hs_chapter="72/73", period="FY2020-21",
         export_value_usd=1.91e9, export_volume_tonnes=2_510_000, yoy_change_pct=None,
         source_name="Lok Sabha Unstarred Question 3980, Ministry of Steel (JPC data)",
         source_url="https://steel.gov.in/sites/default/files/2025-04/lu%203980.pdf",
         source_confidence=PRIMARY,
         notes="Includes UK (see FY2019-20 note)."),
    dict(product_category="Iron & Steel", hs_chapter="72/73", period="FY2021-22",
         export_value_usd=4.28e9, export_volume_tonnes=3_580_000, yoy_change_pct=None,
         source_name="Lok Sabha Unstarred Question 3980, Ministry of Steel (JPC data)",
         source_url="https://steel.gov.in/sites/default/files/2025-04/lu%203980.pdf",
         source_confidence=PRIMARY, notes="EU-27 only, UK excluded from this year onward."),
    dict(product_category="Iron & Steel", hs_chapter="72/73", period="FY2022-23",
         export_value_usd=2.79e9, export_volume_tonnes=2_490_000, yoy_change_pct=None,
         source_name="Lok Sabha Unstarred Question 3980, Ministry of Steel (JPC data)",
         source_url="https://steel.gov.in/sites/default/files/2025-04/lu%203980.pdf",
         source_confidence=PRIMARY,
         notes="Corroborated by a separate PIB release (Ministry of Steel, 'Impact of CBAM on Indian "
         "Steel Industry', 17 Dec 2024, Release ID 2085233) citing the same JPC-sourced figures."),
    dict(product_category="Iron & Steel", hs_chapter="72/73", period="FY2023-24",
         export_value_usd=3.55e9, export_volume_tonnes=4_030_000, yoy_change_pct=None,
         source_name="Lok Sabha Unstarred Question 3980, Ministry of Steel (JPC data)",
         source_url="https://steel.gov.in/sites/default/files/2025-04/lu%203980.pdf",
         source_confidence=PRIMARY, notes=None),
    dict(product_category="Iron & Steel", hs_chapter="72/73", period="FY2024-25",
         export_value_usd=3.05e9, export_volume_tonnes=None, yoy_change_pct=-35.1,
         source_name="GTRI (Global Trade Research Initiative), via AlCircle, 23 Sep 2025",
         source_url="https://www.alcircle.com/news/indian-steel-and-aluminium-exports-to-eu-plunge-24-4-per-cent-ahead-of-cbam-rollout-gtri-reports-115600",
         source_confidence=SECONDARY,
         notes="Steep drop attributed to CBAM front-running by importers/exporters ahead of the "
         "definitive regime; volume figure not given in this source."),
    # ---- Iron & Steel -- HSN-level EU-import-from-India data, Eurostat Comext queried directly ----
    # ADDS to (doesn't replace) the Lok Sabha/GTRI fiscal-year rows above -- both are legitimately
    # primary/well-sourced, just measuring on different bases (India FY + India-reported export value
    # vs. EU calendar year + EU-reported CIF import value), so the totals don't match exactly and
    # shouldn't be expected to. This adds the CN-heading-level PRODUCT MIX the fiscal-year rows don't
    # have. Chapter 72/73 spans 35+ headings; 7204 (ferrous scrap) is excluded from CBAM entirely, and
    # heading 7202 (ferro-alloys) is a genuine split -- most sub-headings are excluded, but ferro-
    # manganese (7202 11/19), ferro-silicon (7202 21/29), ferro-silico-manganese (7202 30), and
    # ferro-chromium (7202 41/49) ARE covered and dominate India's actual 7202 exports (EUR 343.6M of
    # EUR 352.8M total 7202 value in 2024, i.e. 97.5% -- so the covered-subset figure is used
    # throughout, not the full HS4 total).
    dict(product_category="Iron & Steel", hs_chapter="72/73 (all CBAM headings)", period="2024 (EU imports from India, TOTAL, calendar year)",
         export_value_usd=4_979_605_790, export_volume_tonnes=None, yoy_change_pct=-3.0,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly, summed across 35 headings (72 excl. 7204 scrap; 73.01-73.08)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7208.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Calendar-year total: EUR 4,755.9M (2023) -> EUR 4,610.7M (2024, -3.0%) -> EUR "
         "3,649.7M (2025, -20.8%) -- USD approximate at ~1.08/1.05 EUR:USD. The 2025 drop is directionally "
         "consistent with GTRI's reported FY24->FY25 -35.1% (steel exports falling ahead of CBAM's "
         "definitive regime) even though the two figures use different year/reporting bases and "
         "shouldn't be expected to match exactly."),
    dict(product_category="Iron & Steel", hs_chapter="7208", period="2024 (EU imports from India, hot-rolled flat, not clad/plated/coated)",
         export_value_usd=1_123_763_662, export_volume_tonnes=1_584_475.511, yoy_change_pct=3.0,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7208.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="The single largest steel line (~23% of the sector total in 2024). Value: EUR 1,009.8M "
         "(2023) -> EUR 1,040.5M (2024) -> EUR 458.3M (2025, -56.0%) -- a sharp 2025 drop alongside a "
         "near-halving of volume (1,584,476t 2024 -> 789,495t 2025)."),
    dict(product_category="Iron & Steel", hs_chapter="7210", period="2024 (EU imports from India, flat, clad/plated/coated)",
         export_value_usd=948_265_364, export_volume_tonnes=1_007_722.431, yoy_change_pct=8.6,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7210.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Second-largest line. Value: EUR 808.3M (2023) -> EUR 878.0M (2024) -> EUR 689.2M "
         "(2025, -21.5%)."),
    dict(product_category="Iron & Steel", hs_chapter="7222", period="2024 (EU imports from India, other alloy steel bars/rods/angles)",
         export_value_usd=478_680_026, export_volume_tonnes=None, yoy_change_pct=-16.9,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7222.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Value: EUR 533.4M (2023) -> EUR 443.2M (2024) -> EUR 481.8M (2025) -- the one major "
         "line that ROSE in 2025 while the sector overall declined."),
    dict(product_category="Iron & Steel", hs_chapter="7202 (covered ferro-alloys only)", period="2024 (EU imports from India, ferro-Mn/Si/SiMn/Cr)",
         export_value_usd=371_107_858, export_volume_tonnes=None, yoy_change_pct=-11.3,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly, summed across 720211+720219+720221+720229+720230+720241+720249",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.720230.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Only ferro-manganese, ferro-silicon, ferro-silico-manganese, and ferro-chromium "
         "sub-headings of 7202 are CBAM-covered (ferro-molybdenum/tungsten/titanium/vanadium/"
         "niobium/phosphorus/magnesium/nickel and 'other' are excluded, like scrap) -- this is the "
         "covered-only figure, 97.5% of the full 7202 HS4 total. Ferro-silico-manganese (CN 720230) "
         "alone is EUR 152.3M, the single largest ferro-alloy sub-line. Covered-subset total: EUR "
         "387.5M (2023) -> EUR 343.6M (2024) -> EUR 354.8M (2025)."),
    dict(product_category="Iron & Steel", hs_chapter="7209", period="2024 (EU imports from India, cold-rolled flat)",
         export_value_usd=330_534_906, export_volume_tonnes=None, yoy_change_pct=7.3,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7209.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Stable/growing: EUR 285.3M (2023) -> EUR 306.1M (2024) -> EUR 304.3M (2025)."),
    dict(product_category="Iron & Steel", hs_chapter="all other steel headings (30+ CN4 lines)", period="2024 (EU imports from India, grouped remainder)",
         export_value_usd=1_727_254_175, export_volume_tonnes=None, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly, remainder after the 5 rows above",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7304.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Grouped for brevity (~34.7% of the sector total, spread across 30+ individually "
         "smaller headings). Largest individual components: semi-finished products (7207, EUR "
         "123.2M), other alloy steel flat-rolled (7219 stainless, EUR 197.9M), seamless tubes/pipes "
         "(7304, EUR 205.9M), other tubes/pipes (7306, EUR 127.6M), tube/pipe fittings (7307, EUR "
         "184.8M), structures (7308, EUR 133.4M), primary forms/ingots (7206, EUR 207.0M), stainless "
         "wire (7223, EUR 142.5M)."),
    # ---- Aluminium -- HSN-level EU-import-from-India data, Eurostat Comext queried directly ----
    # Supersedes an earlier "derived" estimate (arithmetically backed out of a GTRI combined
    # steel+aluminium aggregate, flagged low-confidence at the time) with real primary figures across
    # all 14 CBAM Annex I aluminium headings (7601,7603-7614,7616 -- 7602 scrap and 7615 tableware are
    # NOT covered). The derived estimate turned out to be materially overstated: real total is
    # ~$0.9-1.8B/yr depending on year, not the ~$2.8-3.0B previously estimated.
    dict(product_category="Aluminium", hs_chapter="76 (all 14 CBAM headings)", period="2024 (EU imports from India, TOTAL)",
         export_value_usd=902_587_282, export_volume_tonnes=None, yoy_change_pct=-49.8,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly, summed across 7601+7603-7614+7616",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7601.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Real total: EUR 1,666.1M (2023) -> EUR 835.7M (2024, -49.8%) -> EUR 903.9M (2025, "
         "+8.2%) -- USD approximate at ~1.08/1.05 EUR:USD. This REPLACES the earlier GTRI-arithmetic-"
         "derived estimate of ~$3.0B/$2.77B, which was overstated by roughly 3x -- likely because "
         "GTRI's 'combined steel+aluminium' aggregate used a different scope/basis than customs HS "
         "classification. The 2023->2024 near-halving predates CBAM's Jan 2026 definitive-phase start "
         "(unlike steel's FY24->FY25 drop, which GTRI attributed to CBAM front-running) -- this "
         "earlier aluminium decline likely reflects other market factors, not CBAM anticipation."),
    dict(product_category="Aluminium", hs_chapter="7601", period="2024 (EU imports from India, unwrought aluminium)",
         export_value_usd=675_445_879, export_volume_tonnes=256_497.277, yoy_change_pct=-55.4,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7601.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="By far the dominant aluminium line (~75-84% of the sector total every year). Steep "
         "decline: EUR 1,399.9M/589,906t (2023) -> EUR 625.4M/256,497t (2024) -> EUR 623.0M/247,621t "
         "(2025) -- volume more than halved from 2023 to 2024 and has stayed flat since.",
         ),
    dict(product_category="Aluminium", hs_chapter="7616", period="2024 (EU imports from India, other aluminium articles)",
         export_value_usd=77_472_442, export_volume_tonnes=5475.305, yoy_change_pct=-2.1,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7616.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Second-largest line, stable: EUR 73.1M (2023) -> EUR 71.7M (2024) -> EUR 76.4M "
         "(2025)."),
    dict(product_category="Aluminium", hs_chapter="7607", period="2025 (EU imports from India, aluminium foil -- growth line)",
         export_value_usd=75_323_150, export_volume_tonnes=17_540.212, yoy_change_pct=106.3,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7607.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="A genuine growth story running counter to the sector's overall decline: EUR 19.4M/"
         "4,074t (2023) -> EUR 33.8M/8,659t (2024) -> EUR 69.7M/17,540t (2025) -- value +74% and "
         "volume +103% year-on-year into 2025, more than 3x since 2023. Worth watching: could reflect "
         "Indian exporters shifting toward higher-value-added downstream products."),
    dict(product_category="Aluminium", hs_chapter="7605", period="2025 (EU imports from India, aluminium wire -- growth line)",
         export_value_usd=66_621_053, export_volume_tonnes=23_371.709, yoy_change_pct=94.2,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7605.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Another growth line: EUR 32.3M/12,636t (2023) -> EUR 31.8M/12,167t (2024, flat) -> "
         "EUR 61.7M/23,372t (2025, nearly doubled)."),
    dict(product_category="Aluminium", hs_chapter="7604", period="2024 (EU imports from India, bars/rods/profiles)",
         export_value_usd=21_652_470, export_volume_tonnes=None, yoy_change_pct=-48.5,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7604.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Declining: EUR 38.9M (2023) -> EUR 20.0M (2024) -> EUR 13.9M (2025)."),
    dict(product_category="Aluminium", hs_chapter="7606", period="2024 (EU imports from India, plates/sheets/strip)",
         export_value_usd=13_867_399, export_volume_tonnes=None, yoy_change_pct=-65.9,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7606.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Sharp decline: EUR 37.7M (2023) -> EUR 12.8M (2024) -> EUR 8.0M (2025)."),
    dict(product_category="Aluminium", hs_chapter="7614", period="2024 (EU imports from India, stranded wire/cables)",
         export_value_usd=22_117_220, export_volume_tonnes=None, yoy_change_pct=-5.4,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7614.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Stable: EUR 21.6M (2023) -> EUR 20.5M (2024) -> EUR 23.3M (2025)."),
    dict(product_category="Aluminium", hs_chapter="7603", period="2025 (EU imports from India, powders/flakes)",
         export_value_usd=9_866_526, export_volume_tonnes=None, yoy_change_pct=201.9,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7603.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Small but growing ~4x: EUR 2.3M (2023) -> EUR 3.0M (2024) -> EUR 9.1M (2025)."),
    dict(product_category="Aluminium", hs_chapter="7608/7609/7610/7611/7612/7613", period="2024 (EU imports from India, tubes/fittings/structures/reservoirs/casks/gas containers, grouped)",
         export_value_usd=17_930_055, export_volume_tonnes=None, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly, 6 small headings summed",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.7609.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Grouped for brevity -- all individually small: 7608 tubes/pipes EUR 1.2M, 7609 "
         "fittings EUR 4.3M, 7610 structures EUR 8.8M, 7611 reservoirs EUR 151 (negligible), 7612 "
         "casks/drums EUR 2.0M, 7613 compressed-gas containers EUR 0.27M (all 2024 figures)."),
    # ---- Cement -- HSN-level EU-import-from-India mirror data (Oct 2026 research pass) ----
    # CBAM Annex I cement-sector CN codes cross-checked across 3 secondary sources (cbamguide.com,
    # cbam-services.com, carbonchain.com) -- EUR-Lex primary text itself returned empty/bot-blocked.
    # Mirror data (EU's own import records, since India's own export-side portal is unscrapable) via
    # NOTE: an earlier pass noted Eurostat Comext returned 404/blocked for cement CN8 codes and used
    # WITS/UN Comtrade HS6 data instead (SECONDARY). That was a tooling gap in that session, not a
    # real API limitation -- the working query pattern (see 2507 00 80 kaolinic clay below, and every
    # other category in this table) was later found and used to re-query all real cement CN8 codes
    # directly (PRIMARY), which corroborate the earlier WITS figures closely (e.g. clinkers 2024:
    # WITS $790 vs Eurostat direct EUR 732 [~$791] -- effectively the same underlying customs record).
    dict(product_category="Cement", hs_chapter="2523", period="CY2023 (India global total, all destinations)",
         export_value_usd=45.5e6, export_volume_tonnes=None, yoy_change_pct=-13.4,
         source_name="trendeconomy.com, India HS 2523 export data 2012-2023",
         source_url="https://trendeconomy.com/data/h2/India/2523",
         source_confidence=SECONDARY,
         notes="India's TOTAL global cement export value for context -- EU is not in the top-5 "
         "destinations (Sri Lanka 66%, Maldives 19.3%, Nepal 4%, Bhutan 3.7%, UAE 1%). Not "
         "upgradeable to Eurostat/primary like the rows below: this one is deliberately a different, "
         "wider scope (global exports, all destinations), not an EU-import mirror, so there is "
         "nothing to re-query for this specific figure."),
    dict(product_category="Cement", hs_chapter="2523 30 00", period="2024 (EU imports from India, aluminous cement)",
         export_value_usd=94_158, export_volume_tonnes=309.775, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly (product=25233000)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.25233000.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="The single largest cement-sector CN8 line for 2024, but it's a one-off spike, not a "
         "trend: EUR 22 (2023) -> EUR 87,183 (2024) -> EUR 236 (2025). Still ~$94K at its peak -- "
         "immaterial next to steel/aluminium's billions."),
    dict(product_category="Cement", hs_chapter="2523 10/21/29/90 00", period="2024 (EU imports from India, clinkers + Portland + other hydraulic, grouped)",
         export_value_usd=7793, export_volume_tonnes=None, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly, summed across 25231000+25232100+25232900+25239000",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.25231000.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Grouped remainder of the CN 2523 cement lines (excluding aluminous cement above and "
         "kaolinic clay below). All four lines are rounding-error scale (EUR 732-4,138 each in 2024): "
         "clinkers (25231000, India's large volumes go to Bangladesh/Sri Lanka/Africa, not the EU), "
         "white cement (25232100), other Portland (25232900), other hydraulic (25239000). CONFIRMED: "
         "cement CBAM exposure is genuinely negligible for India at the real CN-code level, not just "
         "at the global-total level."),
    dict(product_category="Cement", hs_chapter="2507 00 80", period="2024 (EU imports from India, kaolinic clays -- CN8, precise)",
         export_value_usd=7_111_476, export_volume_tonnes=84_754.888, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly (product=25070080, reporter=EU27_2020, partner=IN)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.25070080.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="CORRECTS the earlier HS6-level estimate: true CN8 figure is EUR 6,584,700 (~$7.11M "
         "at ~1.08 USD/EUR, approximate) / 84,754.9 t for 2024, and EUR 6,078,690 (~$6.38M) / "
         "83,965.3 t for 2025 -- roughly HALF the earlier $13.8M HS6 figure, which also swept in "
         "non-CBAM-covered raw kaolin (CN 2507 00 20 = EUR 6,979,061 in 2024, almost exactly the "
         "other half). This is the single most material CBAM-relevant cement-sector line for India, "
         "even though still tiny next to steel/aluminium.",
         ),
    # ---- Fertilizers -- HSN-level EU-import-from-India mirror data ----
    # CBAM Annex I fertiliser scope is WIDER than a narrow urea-only assumption: all of CN 3102, plus
    # 2808 (nitric acid), 2814 (ammonia), 2834 21 00 (potassium nitrate -- easy to miss, sits in HS
    # ch.28 not ch.31), and 3105 except 3105 60 00 (P+K only, no nitrogen, explicitly carved out).
    # CN8 breakdown below (Eurostat Comext, queried directly, PRIMARY) supersedes the earlier
    # HS6-level "3102 (all)" WITS/UN Comtrade aggregate rows (SECONDARY) -- the two sources corroborate
    # closely (EUR 829,236 summed across these CN8 lines for 2024 vs. WITS's $897,550 HS6 aggregate
    # for the same year), giving confidence in both, but CN8 is the more precise and useful figure.
    dict(product_category="Fertilizers", hs_chapter="3102 10 (10+90)", period="2024 (EU imports from India, urea)",
         export_value_usd=637_300, export_volume_tonnes=1164.527, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly (31021010 higher-N + 31021090 other)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.31021090.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="The single largest fertiliser-sector CN8 line, as expected. EUR-denominated: "
         "31021010 (higher-N split) EUR 616,420 (2023) -> EUR 479,892 (2024) -> no trade recorded "
         "(2025); 31021090 (other) EUR 57,177 (2023) -> EUR 110,016 (2024) -> EUR 334,420 (2025), "
         "rising sharply. Still tiny relative to India's status as a large net urea IMPORTER overall "
         "-- this is a narrow specialty/blended export line, not bulk urea trade."),
    dict(product_category="Fertilizers", hs_chapter="3102 21/29", period="2024 (EU imports from India, ammonium sulphate)",
         export_value_usd=142_535, export_volume_tonnes=160.593, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly (31022100 crystals + 31022900 other)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.31022900.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="31022900 (bulk of this line) rose from EUR 131,698 (2024) to EUR 539,954 (2025) -- "
         "worth re-checking if this trend continues, though still a small absolute figure."),
    dict(product_category="Fertilizers", hs_chapter="3102 50", period="2024 (EU imports from India, sodium nitrate)",
         export_value_usd=114_548, export_volume_tonnes=125.254, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly (product=31025000)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.31025000.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Declining: EUR 133,070 (2023) -> EUR 106,063 (2024) -> EUR 32,867 (2025)."),
    dict(product_category="Fertilizers", hs_chapter="3102 60/80/90", period="2024 (EU imports from India, other nitrogenous fertiliser lines)",
         export_value_usd=1391, export_volume_tonnes=0.609, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly (31026000+31028000+31029000)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.31029000.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Rounding-error scale across all remaining CN8 lines under 3102 combined. CN 3102 30 "
         "(ammonium nitrate) and 3102 40 (ammonium nitrate/calcium carbonate mixtures) show NO trade "
         "recorded from India at all across 2023-2025 -- zero, not a data gap."),
    dict(product_category="Fertilizers", hs_chapter="2814 20 00", period="2024 (EU imports from India, ammonia, aqueous solution)",
         export_value_usd=6857, export_volume_tonnes=0.007, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly (product=28142000; anhydrous 28141000 shows no trade at all)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.28142000.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Supersedes an earlier WITS-sourced secondary figure ($6,870/0.007t for the same "
         "period) that corroborates almost exactly (EUR 6,349 [~$6,857] vs WITS's $6,870 -- same "
         "underlying customs record). Negligible -- consistent with India being a large net ammonia "
         "IMPORTER (2.2 MnT in 2022). Nitric acid (CN 2808) and UAN/N-mixtures (CN 3102 80) show "
         "India absent entirely from the EU's partner list for these lines -- zero, not a data gap."),
    dict(product_category="Fertilizers", hs_chapter="2834 21 00", period="2024 (EU imports from India, potassium nitrate)",
         export_value_usd=1_656_046, export_volume_tonnes=565.461, yoy_change_pct=176.8,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly (product=28342100)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.28342100.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Supersedes an earlier WITS-sourced secondary figure ($1,659,700 for the same period) "
         "that corroborates almost exactly (EUR 1,533,376 [~$1,656,046] vs WITS's $1,659,700). THE "
         "ONE REAL FERTILISER EXPORT LINE, and growing fast, which the single-year WITS figure "
         "didn't show: EUR 553,907 (2023) -> EUR 1,533,376 (2024, +176.8%) -> EUR 2,086,582 (2025, "
         "+36.1%), more than tripling over two years. India ranked 7th among all EU suppliers of "
         "potassium nitrate as of the 2024 figure (~0.49% of the EU's $337.9M total imports of this "
         "line -- worth re-checking given the growth trend). Easy to miss: this CN code sits in HS "
         "Chapter 28 (inorganic chemicals), not Chapter 31 (fertilisers), but is explicitly in "
         "CBAM Annex I's fertiliser-sector scope."),
    dict(product_category="Fertilizers", hs_chapter="3105 (excl. 3105 60 00)", period="2024 (EU imports from India, multi-nutrient N+P/N+K/N+P+K fertilisers)",
         export_value_usd=930_331, export_volume_tonnes=None, yoy_change_pct=93.8,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly (CN4 3105 total minus CN8 31056000, which CBAM excludes)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.3105.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Supersedes an earlier WITS-sourced secondary figure ($985,370 for the same period) "
         "that corroborates reasonably closely (EUR 861,417 [~$930,331] vs WITS's $985,370, ~5.6% "
         "apart -- likely a data-vintage/revision difference between Eurostat and the Comtrade mirror "
         "WITS uses). CN 3105 60 00 (P+K only, no nitrogen) is explicitly excluded from CBAM's "
         "fertiliser scope; this figure is the CN4 total (EUR 904,949 in 2024) minus that excluded "
         "line (EUR 43,532 in 2024). Also growing fast across the full window: EUR 444,457 total "
         "(2023, excluded line had zero trade that year) -> EUR 861,417 remainder (2024) -> EUR "
         "1,139,189 remainder (2025, total EUR 1,170,858 minus EUR 31,669 excluded)."),
    # ---- Hydrogen (CN 2804 10 00) -- upgraded to PRIMARY via direct Eurostat CN8 query ----
    dict(product_category="Hydrogen", hs_chapter="2804 10 00", period="2023-2025 (EU imports from India, calendar years, CBAM-covered CN8 only)",
         export_value_usd=0, export_volume_tonnes=0, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly at CN8 (2804 10 00)",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.28041000.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Directly confirms, at the exact CBAM-relevant CN8 code, the CSE (2024 study, via Down "
         "To Earth, 2 Jan 2026) claim that 'India does not currently export hydrogen ... to the EU.' "
         "Not literally zero every year: 2023 recorded EUR 334 (a single de minimis shipment), 2024 "
         "and 2025 both EUR 0 -- functionally no export industry, not a hard zero forever. Note the "
         "broader CN4 heading 2804 ('Hydrogen, rare gases and other non-metals') is NOT all-zero -- it "
         "shows real trade (EUR 154,046 in 2024) -- but that trade is in OTHER gases within the same "
         "heading (nitrogen 2804 30, oxygen 2804 40, silicon 2804 61/69, arsenic 2804 80; these "
         "CN8-identifiable lines sum to only EUR 43,396 of the EUR 154,046 CN4 total, with the "
         "remainder most likely confidentiality-suppressed at CN8 by Eurostat), not hydrogen itself, "
         "and none of it falls within CBAM's Annex I hydrogen scope (CN 2804 10 00 only). Worth "
         "periodic re-check given India's National Green Hydrogen Mission could change this within "
         "CBAM's own 2026-2034 phase-in horizon."),
    # ---- Electricity (CN 2716) -- upgraded to PRIMARY via direct Eurostat query ----
    dict(product_category="Electricity", hs_chapter="2716", period="2023-2025 (EU imports from India, calendar years)",
         export_value_usd=0, export_volume_tonnes=0, yoy_change_pct=None,
         source_name="Eurostat Comext SDMX API, DS-045409, queried directly",
         source_url="https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.2716.1.VALUE_IN_EUROS",
         source_confidence=PRIMARY,
         notes="Directly confirms the CSE (2024 study, via Down To Earth, 2 Jan 2026) claim of zero "
         "India-to-EU electricity trade, consistent with there being no direct India-EU grid "
         "interconnection: zero recorded EU imports of electricity from India in every year queried "
         "(2023, 2024, 2025). A genuinely zero-trade product code returns an empty but valid dataset "
         "in this API, distinguishable from an invalid code (which instead returns an explicit SDMX "
         "fault) -- so this is a confirmed absence of trade, not a query error."),
]
