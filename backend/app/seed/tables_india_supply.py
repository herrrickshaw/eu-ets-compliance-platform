"""Seed tables: india supply (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .. import models

# ---------------- India supply-capacity (Article 6.2 gap analysis) ----------------
# Sourced from a Sept 2026 research pass reading primary PIB/MNRE/MoPNG/NITI Aayog/
# steel.gov.in/BEE documents directly where noted; secondary trade-press cited only
# where no primary figure could be located. A follow-up research pass reading the
# actual CDM ACM0002 / Verra VMR0017 methodology text confirmed the correct baseline
# factor for this kind of calculation is CEA's Combined Margin (CM) — not a simple
# weighted average — so this uses CM = 0.736 tCO2/MWh (FY2024-25 vintage), from CEA
# "CO2 Baseline Database for the Indian Power Sector v21.0", Nov 2025,
# https://cea.nic.in/wp-content/uploads/baseline/2025/12/User_Guide_V_21.0.pdf
# Capacity-factor assumptions below are a mix of: (a) real India national
# fleet-average CUFs derived from MNRE's own capacity+generation statistics
# (solar ~17.5-19%, wind ~20%; see docs/INDIA_CCTS_SOURCES.md and the
# credit_benchmarks table for the full derivation), used where directly
# applicable, (b) a tender's own stated minimum demand-fulfilment ratio for firm
# FDRE-RTC supply, and (c) illustrative assumptions for enabling-infrastructure
# rows where no direct benchmark exists — each row's conversion_note says which.
CEA_GRID_FACTOR = 0.736  # tCO2/MWh, Combined Margin, FY2024-25 vintage, CEA CO2 Baseline Database v21.0 (primary)

AT = models.FigureType.ASPIRATIONAL_TARGET

AO = models.FigureType.AWARDED_OPERATIONAL

CA = models.FigureType.CURRENT_ACTUAL

PRIMARY = models.SourceConfidence.PRIMARY

SECONDARY = models.SourceConfidence.SECONDARY

supply_rows = [
    # ---- Renewable energy with storage (FDRE) ----
    dict(
        activity_key="re_storage",
        metric_label="MNRE FDRE bidding trajectory (annual issuance target)",
        value=50, unit="GW/year (FY2023-24 to FY2027-28)", figure_type=AT,
        as_of_date=date(2026, 4, 2),
        source_name="PIB — Ministry of Power, Electricity Generation from Non-Conventional Sources",
        source_url="https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=2248342",
        source_confidence=PRIMARY,
        conversion_note="Annual issuance PACE, not a cumulative installed/awarded capacity figure — "
        "no aggregate GW-awarded total found on any primary source, so not converted to tCO2e.",
        potential_avoided_mt_co2e=None,
    ),
    dict(
        activity_key="re_storage",
        metric_label="SECI FDRE-RTC Tranche-V awarded (1 GW round-the-clock; one tender, not a national tally)",
        value=1.0, unit="GW (contracted round-the-clock supply, Aug 2026 award)", figure_type=AO,
        as_of_date=date(2026, 8, 7),
        source_name="pv-magazine India (secondary — SECI's own results page could not be reached)",
        source_url="https://www.pv-magazine-india.com/2026/08/07/secis-1-gw-fdre-rtc-power-tender-discovers-inr-5-25-kwh-tariff/",
        source_confidence=SECONDARY,
        conversion_note="1,000 MW contracted RTC supply x 90% minimum annual demand-fulfilment ratio "
        "(the tender's own stated floor, so this is a lower bound on delivered energy) x 8,760 h = "
        "7,884 GWh/yr x CEA Combined Margin 0.736 tCO2/MWh = 5.80 Mt CO2e/yr. Replaces an earlier "
        "row that applied an unsourced 35% capacity factor to 2.5 GW (1.5 GW FDRE + 1 GW RTC): the "
        "tender's contracted MW is firm supply with a stated 90% annual DFR, not installed "
        "solar/wind nameplate, so a plain-RE capacity factor was the wrong basis; and the 1.5 GW FDRE "
        "half could not be confirmed against any source read this session, so it is dropped rather "
        "than kept. Winners: Kengeri Prime 180 MW, Resolven Four 150, Hexa Climate 150, Hero Solar "
        "120, EMIF II 100, Purvah 70, Juniper Green 230 (INR 5.25-5.26/kWh, 25-yr PPAs). Awarded, "
        "not yet operating.",
        potential_avoided_mt_co2e=5.80,
    ),
    # ---- Solar thermal power ----
    dict(
        activity_key="solar_thermal",
        metric_label="Installed CSP (concentrated solar thermal) capacity",
        value=228.5, unit="MW (JNNSM Phase-I, 2014-15; effectively stalled since)", figure_type=CA,
        as_of_date=date(2015, 3, 31),
        source_name="MNRE Physical Achievements page (no current figure listed) / secondary reviews for the historical number",
        source_url="https://mnre.gov.in/en/physical-progress/",
        source_confidence=SECONDARY,
        conversion_note="MNRE's current CST page tracks only industrial-heat market potential (6.45 "
        "GWth), not power generation, and CSP is absent from MNRE's official installed-capacity table "
        "— confirming this is genuinely negligible today, not a data gap.",
        potential_avoided_mt_co2e=None,
    ),
    # ---- Offshore wind ----
    dict(
        activity_key="offshore_wind",
        metric_label="Cabinet-approved VGF offshore wind capacity",
        value=1000, unit="MW (500 MW Gujarat + 500 MW Tamil Nadu)", figure_type=AO,
        as_of_date=date(2024, 6, 19),
        source_name="PIB — Cabinet approves VGF scheme for Offshore Wind Energy Projects",
        source_url="https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2026700",
        source_confidence=PRIMARY,
        conversion_note="1,000 MW x 42% offshore capacity factor (real observed international offshore "
        "project range 42-46% — Norther Belgium 43.1%, Alpha Ventus Germany 42-42.7%, European fleet "
        "avg ~45.8%; India has no operational offshore wind to derive its own CF, so the international "
        "low end is used) x 8,760 h x CEA Combined Margin 0.736 tCO2/MWh = 2.71 Mt CO2e/yr. IMPORTANT: "
        "SECI's first 500 MW Gujarat tender (issued Sep 2024) drew ZERO bids by its extended Jul 2025 "
        "deadline — this capacity is funded/approved but nothing is under construction yet.",
        potential_avoided_mt_co2e=2.71,
    ),
    dict(
        activity_key="offshore_wind",
        metric_label="National offshore wind policy target",
        value=30, unit="GW by 2030", figure_type=AT,
        as_of_date=date(2018, 9, 1),
        source_name="MNRE offshore wind policy (widely reported; exact primary PIB URL not located)",
        source_url="https://mnre.gov.in/en/off-shore-wind/",
        source_confidence=SECONDARY,
        conversion_note="30,000 MW x 42% CF (same real international-project-derived assumption as "
        "above) x 8,760 h x CEA Combined Margin 0.736 tCO2/MWh = 81.2 Mt CO2e/yr IF fully built by "
        "2030. Given the first tender drew zero bids, treat this as a distant upper bound, not a "
        "plausible near-term figure.",
        potential_avoided_mt_co2e=81.2,
    ),
    # ---- Green hydrogen ----
    dict(
        activity_key="green_hydrogen",
        metric_label="Green hydrogen production capacity awarded (SIGHT scheme)",
        value=862000, unit="tonnes H2/year (19 companies, as of May 2025)", figure_type=AO,
        as_of_date=date(2025, 5, 1),
        source_name="PIB — Unlocking India's Green Hydrogen Production Potential",
        source_url="https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251112690301.pdf",
        source_confidence=PRIMARY,
        conversion_note="862,000 tH2/yr x 9.5 tCO2/tH2 grey-hydrogen (SMR) displacement factor "
        "(standard industry range 9-10 tCO2/tH2, midpoint used — not India-specific-sourced) = 8.19 "
        "Mt CO2e/yr. Most of this awarded capacity is still under construction, not yet producing.",
        potential_avoided_mt_co2e=8.19,
    ),
    dict(
        activity_key="green_hydrogen",
        metric_label="National Green Hydrogen Mission 2030 target",
        value=5_000_000, unit="tonnes H2/year by 2030", figure_type=AT,
        as_of_date=date(2025, 5, 1),
        source_name="PIB — Unlocking India's Green Hydrogen Production Potential",
        source_url="https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251112690301.pdf",
        source_confidence=PRIMARY,
        conversion_note="5 MMT/yr x 9.5 tCO2/tH2 = 47.5 Mt CO2e/yr IF fully built by 2030. Awarded "
        "capacity so far (862,000 t/yr, see above) is only ~17% of this target.",
        potential_avoided_mt_co2e=47.5,
    ),
    # ---- Compressed biogas ----
    dict(
        activity_key="cbg",
        metric_label="CBG plants commissioned (SATAT+MDA+BAM+DPI+CFA, cumulative)",
        value=200, unit="plants", figure_type=CA,
        as_of_date=date(2026, 8, 6),
        source_name="PIB — Cabinet approves GOBARdhan (National Unified Scheme for Compressed Biogas)",
        source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2295480",
        source_confidence=PRIMARY,
        conversion_note="Plant count only — no verified average per-plant output figure found to "
        "convert to tCO2e.",
        potential_avoided_mt_co2e=None,
    ),
    dict(
        activity_key="cbg",
        metric_label="Cumulative CBG output (secondary, unverified against a primary document)",
        value=920, unit="tonnes/day (~336,000 t/yr)", figure_type=CA,
        as_of_date=date(2026, 1, 1),
        source_name="Minister statement reported by Tribune/Energetica/Sunday Guardian",
        source_url=None,
        source_confidence=SECONDARY,
        conversion_note="920 t/day x 365 = 335,800 t/yr x 2.68 tCO2/t fossil-fuel-(CNG/diesel)-"
        "displacement factor (standard biomethane accounting convention, not India-specific-sourced) "
        "= 0.90 Mt CO2e/yr. Both the output figure and the conversion factor are unverified.",
        potential_avoided_mt_co2e=0.90,
    ),
    dict(
        activity_key="cbg",
        metric_label="GOBARdhan revised target",
        value=None, unit="~10x current production (no absolute baseline published)", figure_type=AT,
        as_of_date=date(2026, 8, 6),
        source_name="PIB — Cabinet approves GOBARdhan",
        source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2295480",
        source_confidence=PRIMARY,
        conversion_note="Cabinet states a 'nearly ten-fold' increase from current levels but does not "
        "restate an absolute MMT target (the old 15 MMT SATAT target appears superseded) — not "
        "quantifiable without an official baseline.",
        potential_avoided_mt_co2e=None,
    ),
    dict(
        activity_key="cbg",
        metric_label="Indore Gobar-Dhan CBG plant (EverEnviro/IEISL) — named-project example",
        value=550, unit="tonnes/day wet MSW processed -> ~15-18 t/day CBG (~17,000 kg/day peak, 100% "
        "capacity utilisation reported 2024)", figure_type=CA,
        as_of_date=date(2022, 2, 19),
        source_name="Multiple trade press (iamrenew, Natural Gas World, Down To Earth); EverEnviro's own site for the VCS project claim",
        source_url="https://www.everenviro.com/renewable.html",
        source_confidence=SECONDARY,
        conversion_note="IMPORTANT CORRECTION to a common framing: this is NOT 'Indore Municipal "
        "Corporation (IMC) procuring carbon credits from EverEnviro.' Verified structure: IMC supplies "
        "segregated wet waste under a 20-year PPP and receives an annual royalty (~Rs 2.5 crore) from "
        "EverEnviro's subsidiary IEISL, plus buys back CBG for city buses at a discount — IMC is the "
        "waste supplier/fuel buyer, not a credit buyer. EverEnviro/IEISL (set up by Eversource Capital "
        "in 2019 — a bootstrapped company, NOT an IOC joint venture for this plant; a separate "
        "IOC-EverEnviro JV formed Oct 2024 covers only future plants) claims (own website + LinkedIn) "
        "the plant is registered under Verra VCS as 'Project 4650', ~130,000 tCO2e/yr PROJECTED. "
        "CHECKED DIRECTLY on registry.verra.org (Sept 2026): Project ID 4650 returns an explicit "
        "'unable to load project details' error, while a control ID (191, a real Chinese hydropower "
        "project) renders correctly on the same URL pattern — the registry itself works, so this is "
        "strong evidence 4650 is NOT a valid/existing public VCS project ID, contradicting EverEnviro's "
        "own citation. Treat the VCS registration claim as unconfirmed-to-false, not merely "
        "unverified, until EverEnviro publishes a correct/working project ID. Separately, IMC DOES "
        "generate its own carbon-credit revenue "
        "(Rs 50 lakh in 2020 rising to ~Rs 8-9 crore cumulative) — but via its smart-city arm ISCDL and "
        "EKI Energy Services, from THREE DIFFERENT, smaller municipal projects (a separate "
        "bio-methanation plant, a compost plant, a 1.5 MW solar plant) registered under VCS around Jan "
        "2020 — two years before this EverEnviro plant existed. Both threads are voluntary-market VCS "
        "projects that predate India's CCTS Offset Mechanism (which only started Jan 2025 and excludes "
        "pre-2025 projects) — cite as a pre-CCTS voluntary-market precedent, not a current domestic "
        "Offset Mechanism case. Not converted to a potential_avoided_mt_co2e figure here since the "
        "130,000 tCO2e/yr number is company-projected, not independently confirmed.",
        potential_avoided_mt_co2e=None,
    ),
    # ---- Emerging mobility / fuel cells ----
    dict(
        activity_key="mobility",
        metric_label="Sanctioned hydrogen mobility pilots",
        value=37, unit="vehicles (15 FCEV + 22 H2-ICE) + 9 refuelling stations", figure_type=AO,
        as_of_date=date(2025, 3, 3),
        source_name="PIB — MNRE hydrogen mobility pilot sanction",
        source_url="https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=2107795",
        source_confidence=PRIMARY,
        conversion_note="Pilot-scale (37 vehicles, ₹208 crore); not meaningfully quantifiable against "
        "sector-scale demand. Commissioning expected ~18-24 months from the Mar 2025 announcement.",
        potential_avoided_mt_co2e=None,
    ),
    # ---- High-efficiency / energy-efficiency technology (BEE PAT scheme) ----
    dict(
        activity_key="energy_efficiency",
        metric_label="PAT scheme cumulative energy savings",
        value=25.78, unit="Million toe cumulative (BEE dashboard, labeled 2025)", figure_type=CA,
        as_of_date=date(2025, 1, 1),
        source_name="BEE — Perform, Achieve and Trade (PAT) programme page",
        source_url="https://beeindia.gov.in/en/programmes/perform-achieve-and-trade-pat",
        source_confidence=PRIMARY,
        conversion_note="No matching current CO2-avoided figure is published alongside this "
        "energy-savings number; a toe-to-tCO2e conversion would require assuming a specific fuel mix "
        "and was not attempted to avoid fabricating false precision.",
        potential_avoided_mt_co2e=None,
    ),
    dict(
        activity_key="energy_efficiency",
        metric_label="PAT Cycle I+II CO2 avoided (dated, incomplete)",
        value=97.01, unit="Mt CO2 cumulative avoided, Cycles I-II only (2012-2019)", figure_type=CA,
        as_of_date=date(2022, 3, 29),
        source_name="PIB — Status of Implementation of NMEEE",
        source_url="https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1811051",
        source_confidence=PRIMARY,
        conversion_note="This is a CUMULATIVE figure since 2012 (a stock), not an annual rate — using "
        "it in an annual-basis gap analysis would misrepresent it. Cycles III-VII actuals (2019 "
        "onward) are missing from every source found. Excluded from the quantifiable total for this "
        "reason, not because the number itself is unsourced.",
        potential_avoided_mt_co2e=None,
    ),
    # ---- Sustainable Aviation Fuel ----
    dict(
        activity_key="saf",
        metric_label="SAF blending mandate volume (2028, 2% blend, international ops)",
        value=0.19, unit="MMT SAF/year (midpoint estimate)", figure_type=AT,
        as_of_date=date(2028, 1, 1),
        source_name="PIB (mandate) + PPAC Flash Report (ATF consumption baseline for conversion)",
        source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2163273",
        source_confidence=PRIMARY,
        conversion_note="0.19 MMT/yr x 3.16 tCO2/t (standard jet-fuel combustion factor) x 80% "
        "lifecycle-reduction assumption (typical ICAO/IATA SAF figure) = 0.48 Mt CO2e/yr. Both "
        "conversion factors are standard aviation-industry conventions, not verified in this "
        "India-specific research pass. Mandate applies to international operations only.",
        potential_avoided_mt_co2e=0.48,
    ),
    dict(
        activity_key="saf",
        metric_label="PIB's own stated SAF decarbonization potential",
        value=22.5, unit="Mt CO2/year (PIB's own claim, midpoint of 20-25)", figure_type=AT,
        as_of_date=date(2025, 9, 3),
        source_name="PIB — SAF a practical and immediate solution to decarbonize aviation",
        source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2163273",
        source_confidence=PRIMARY,
        conversion_note="A direct claim from the PIB release itself (not independently derived); "
        "adoption-rate/time-horizon assumptions behind the 20-25 Mt figure are unstated. Excluded "
        "from the quantifiable total to avoid double-counting with the mandate-derived row above — "
        "shown for context only.",
        potential_avoided_mt_co2e=None,
    ),
    # ---- BAT for hard-to-abate sectors ----
    dict(
        activity_key="bat_hard_to_abate",
        metric_label="Green Steel certified production (FY2025-26)",
        value=12.4, unit="MMT green steel (<2.2 tCO2e/tfs threshold), 90 units certified", figure_type=CA,
        as_of_date=date(2026, 3, 31),
        source_name="Ministry of Steel — Green Steel Initiative",
        source_url="https://steel.gov.in/green-steel-initiative",
        source_confidence=PRIMARY,
        conversion_note="A production-volume and intensity-THRESHOLD figure, not an avoided-emissions "
        "figure — converting it would require a counterfactual (non-green-steel) baseline intensity "
        "that isn't published. No aggregate national BAT-adoption abatement target exists for any "
        "hard-to-abate sector.",
        potential_avoided_mt_co2e=None,
    ),
    # ---- Tidal / ocean energy ----
    dict(
        activity_key="tidal",
        metric_label="Operational tidal/ocean energy capacity",
        value=0, unit="MW (both pilot attempts — 3.75 MW Sundarbans, 50 MW Gulf of Kutch — dropped)", figure_type=CA,
        as_of_date=date(2026, 1, 1),
        source_name="Secondary reporting (Down To Earth/Mongabay/Business Standard); no primary MNRE figure located",
        source_url=None,
        source_confidence=SECONDARY,
        conversion_note="Genuinely negligible — confirmed zero operational capacity, not a data gap. "
        "An MNRE Action Plan reportedly targets 100 MW demonstration by 2027 but could not be "
        "verified against a primary document this session.",
        potential_avoided_mt_co2e=0,
    ),
    # ---- HVDC transmission paired with renewables ----
    dict(
        activity_key="hvdc",
        metric_label="Ladakh Green Energy Corridor-II (RE capacity enabled)",
        value=13, unit="GW RE + 12 GWh BESS, 480 km HVDC line, targeted FY2029-30", figure_type=AO,
        as_of_date=date(2023, 10, 18),
        source_name="PIB — CCEA approves Green Energy Corridor Phase-II (Ladakh)",
        source_url="https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1968732",
        source_confidence=PRIMARY,
        conversion_note="13,000 MW x 19% blended solar+wind capacity factor (real India national "
        "fleet-average CUFs: solar ~17.5-19% MNRE-derived/regulatory benchmark, wind ~19.8-20% — "
        "averaged; Ladakh's own high-altitude solar resource could run higher but no site-specific "
        "figure was found) x 8,760 h x CEA Combined Margin 0.736 tCO2/MWh = 15.92 Mt CO2e/yr. "
        "Cabinet-approved and funded (₹20,773.70 crore, 40% CFA) — infrastructure under "
        "implementation, targeted completion FY2029-30, not yet operational.",
        potential_avoided_mt_co2e=15.92,
    ),
    # ---- Green ammonia ----
    dict(
        activity_key="green_ammonia",
        metric_label="SECI green ammonia procurement tendered (SIGHT Mode-2A)",
        value=724000, unit="tonnes/year (cumulative across 13 planned auctions)", figure_type=AO,
        as_of_date=date(2025, 8, 6),
        source_name="PIB — SECI conducts first-ever auction for Green Ammonia procurement",
        source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2153006",
        source_confidence=PRIMARY,
        conversion_note="724,000 t/yr x 2.0 tCO2/t grey-ammonia (SMR-based) displacement factor "
        "(typical range 1.8-2.4 tCO2/t, midpoint used — not India-specific-sourced) = 1.45 Mt CO2e/yr. "
        "Only the first 75,000 t/yr tranche (to Paradeep Phosphates, Aug 2025) has actually cleared; "
        "the remaining ~649,000 t/yr is still to be auctioned.",
        potential_avoided_mt_co2e=1.45,
    ),
    # ---- CCUS ----
    dict(
        activity_key="ccus",
        metric_label="NITI Aayog CCUS capture potential (2050)",
        value=750, unit="Mt CO2/year by 2050", figure_type=AT,
        as_of_date=date(2022, 11, 29),
        source_name="NITI Aayog — CCUS Policy Framework and Deployment Mechanism in India",
        source_url="https://www.niti.gov.in/sites/default/files/2022-11/CCUS-Report.pdf",
        source_confidence=PRIMARY,
        conversion_note="Already in the correct unit (Mt CO2/year captured) — no physical conversion "
        "needed. But this is a 2050-horizon target, 20+ years beyond the CCTS demand model's "
        "FY2025-27 window; including it in a near-term (or even a 2030-aspirational) gap analysis "
        "would be wildly misleading, so it is deliberately excluded from BOTH totals despite having a "
        "numeric value. No 2030-horizon CCUS figure exists from any source found.",
        potential_avoided_mt_co2e=None,
    ),
    dict(
        activity_key="ccus",
        metric_label="ONGC Gandhar CCS pilot (unverified against a primary MoPNG source)",
        value=100, unit="tonnes CO2/day captured (~36,500 t/yr)", figure_type=CA,
        as_of_date=date(2025, 6, 1),
        source_name="Trade press (Carbon Herald, iamrenew.com) citing ONGC statements",
        source_url=None,
        source_confidence=SECONDARY,
        conversion_note="100 t/day x 365 = 36,500 t/yr = 0.0365 Mt CO2e/yr. A single small pilot, not "
        "sector-scale — but the only near-term CCUS figure found anywhere, primary or secondary.",
        potential_avoided_mt_co2e=0.0365,
    ),
]
