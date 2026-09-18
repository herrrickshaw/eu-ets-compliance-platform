# India CCTS / Article 6.2 / comparative pricing — sourcing notes

The India module (`backend/app/modules/india_ccts/`) is seeded from a September 2026
research pass over public sources — **not** from a primary gazette text, and **not**
from any local repository. Before this research was done, a local
`gazette-translated-indexed` database (2,637 notifications, Ministry of Power +
Ministry of Environment both nominally covered) was checked and confirmed to
contain **zero** hits for "carbon credit", "GHG emission intensity", "CCTS", or
related terms — that corpus was not built for this topic and should not be assumed
to have this data in the future without re-checking.

## What's solid vs. what's genuinely uncertain

**Reasonably solid (secondary-sourced, multiple corroborating reports):**
- Aluminium, Cement, Chlor-Alkali, Pulp & Paper GEI targets — final, G.S.R. 739(E), 8 Oct 2025
- Petroleum Refining, Petrochemicals, Textiles GEI targets — final, MoEFCC notification, 16 Jan 2026
- ~490 total obligated entities across the 7 finalized sectors (not broken out per sector)
- Article 6.2's 13 eligible activities (MoEFCC/NDAIAPA, finalized 17 Feb 2023)
- Korea/China/Japan/EU pricing figures, each with a source URL (see the research
  agent's full report, reproduced in this session's transcript)

**Explicitly uncertain — do not present as settled fact without re-verifying:**
- **Fertilizer sector status is contested.** One source claims a final gazette
  notification (8 Oct 2025, alongside 4 other sectors); ICAP's detailed CCTS page
  lists only 7 finalized sectors and does **not** include fertilizer. Seeded with
  `status=CONTESTED`.
- **Iron & Steel is still draft.** Revised draft made public 2 Jul 2026, 60-day
  objection window running to roughly end-August 2026 — not yet legally binding.
  Seeded with `status=DRAFT`.
- **No official aggregate India Article 6.2 pipeline volume (tCO2e) is published
  anywhere** — confirmed data gap, not an oversight. The only concrete development
  found was a bilateral India-Japan Joint Crediting Mechanism (JCM) with no
  published volume figure.
- PIB primary press releases returned HTTP 403 to automated fetch during the
  *first* (demand-side) research pass — everything attributed to PIB in that pass
  is via secondary reporting that cites it, not a page read directly. **Update:**
  the *second* (supply-side capacity) research pass successfully fetched many PIB
  pages directly via `curl` (the WebFetch/browser tool block is consistent with
  the known ET/Hindu-style WAF block pattern — `curl` gets through where
  browser-based fetches don't, per `feedback_economic_times_blocked` in this
  environment's memory). Rows sourced from that second pass and tagged
  `source_confidence=primary` in `IndiaSupplyCapacity` genuinely are primary-source
  reads, not secondary reporting — see the per-row `source_url` fields.

## Supply-side capacity (`IndiaSupplyCapacity`) — what's solid vs. genuinely thin

A third research pass (Sept 2026) built a bottom-up supply-capacity model per
Article 6.2-eligible activity, since no official pipeline volume exists (see
above). Key findings, each with a primary PIB/MNRE/NITI Aayog/steel.gov.in/BEE
citation in the row's `source_url`:

- **Green hydrogen**: awarded production capacity (862,000 t/yr, ~17% of the 5
  MMT/yr 2030 target) and electrolyser manufacturing capacity (3,000 MW/yr) are
  solid, primary-sourced, current (May 2025) figures.
- **Green ammonia**: SECI's first tendered tranche (75,000 t/yr, Aug 2025) is
  real and cleared; the cumulative 724,000 t/yr figure is the *planned* total
  across 13 auctions, most not yet run.
- **Offshore wind**: the 30 GW-by-2030 target is aspirational and, as of this
  research, essentially unbacked by built capacity — India's first tender (500
  MW, Gujarat) drew **zero bids**. Only 1 GW is Cabinet-approved/funded via a
  viability-gap-funding scheme; nothing is under construction.
- **CCUS**: the only national capacity figure found anywhere (NITI Aayog, Nov
  2022) is a 2050-horizon 750 Mt CO2/yr target — deliberately excluded from the
  gap-analysis totals as too distant to be comparable to CCTS's FY2025-27 window.
  No 2030-horizon CCUS figure exists. The only near-term figure is a single small
  ONGC pilot (~100 t CO2/day), sourced only from trade press, not a primary
  MoPNG/PIB document.
- **PAT scheme (BEE energy efficiency)**: BEE's own dashboard cites 25.78
  Million toe of cumulative energy savings (labeled "2025") but with **no
  matching current CO2-avoided figure**. The only CO2-avoided numbers found
  (97.01 Mt cumulative) cover Cycles I-II only (2012-2019) — Cycles III-VII
  actuals are missing from every source checked. This is a genuine, confirmed
  gap in BEE's public reporting, not a research shortfall.
- **Tidal/ocean energy**: confirmed genuinely negligible — India has zero
  operational capacity; two pilot attempts (Sundarbans, Gulf of Kutch) were both
  abandoned over cost.
- **CEA grid emission factor**: FY2024-25 weighted-average = 0.710 tCO2/MWh
  (Combined Margin 0.736), from CEA's own "CO2 Baseline Database for the Indian
  Power Sector v21.0" (Nov 2025) — the one figure in this whole module read
  directly from its primary source with high confidence, and the constant used
  throughout `seed_data.py` to convert MW capacity into potential avoided tCO2e.

**Capacity-factor assumptions used to convert MW → MWh/year** (35% for
FDRE/RTC, 42% for offshore wind, 30% blended for the Ladakh corridor) are
standard illustrative industry ranges, **explicitly not India-specific-sourced**
in any research pass — see each row's `conversion_note` in the seed data. If
replacing these, CEA/MNRE publish actual plant-load-factor (PLF/CUF) statistics
by state/region that would be a better source than these placeholders.

The gap-analysis endpoint (`POST /api/india/gap-analysis`) deliberately reports
**two separate supply totals** rather than one blended number: near-term
(awarded/operational/current, i.e. plausibly deliverable within the CCTS
FY2025-27 compliance window) and aspirational (2030/2050 policy targets, an
upper bound only). Blending them would be actively misleading given how far
some of these targets are from built capacity today.

## Capacity → credits benchmarks (`CreditBenchmark`) — real MRV methodology, real CFs

A follow-up research pass read the actual CDM ACM0002 and Verra VMR0017 (which
supersedes ACM0002/AMS-I.D for VCS from Apr 2026, and is the methodology family
Gold Standard also builds on) methodology text directly. Two corrections this
produced:

1. **No registry publishes a default capacity factor.** The real formula is
   `baseline emissions = actual metered generation (MWh) × grid emission factor
   (tCO2/MWh)` — capacity factor is a project-specific estimate a developer
   makes, not a methodology parameter. `CreditBenchmark` rows therefore use the
   best available *real* CF: derived from MNRE's own "Renewable Energy
   Statistics 2024-25" capacity+generation tables (solar ~17.5%, wind ~19.8%,
   small hydro ~26.2%, biomass/bagasse/WtE ~16.2% — these are MY OWN
   DERIVATION from official MNRE numbers, not an officially-published CUF
   table, since none was found), a regulatory tariff-setting benchmark (19%
   solar, widely cited in CERC tariff determinations), or a real operating
   project (Kamuthi Solar Park, Tamil Nadu, 648 MWp, ~23.8% observed CF).
2. **The correct India grid-emission-factor parameter for this kind of
   calculation is CEA's Combined Margin (CM), not a simple weighted
   average.** `CEA_GRID_FACTOR` in `seed_data.py` was corrected from 0.710
   (weighted average) to **0.736 tCO2/MWh** (Combined Margin, FY2024-25
   vintage) — this is literally the `EFy` term in the ACM0002/VMR0017 baseline
   equation. This correction, combined with fixing the Ladakh HVDC corridor's
   capacity-factor assumption (see below), meaningfully changed the gap-analysis
   result: near-term gap moved from ~2.3 Mt to ~10.4 Mt CO2e.

**Also corrected as part of this pass**: the Ladakh Green Energy Corridor-II row
in `IndiaSupplyCapacity` originally used an arbitrary 30% "blended solar+wind"
capacity factor. With real India fleet averages in hand (solar ~17.5-19%, wind
~19.8-20%), this was corrected to 19% — dropping that row's potential avoided
emissions from 24.26 to 15.92 Mt CO2e/yr, which is most of why the near-term gap
widened. The offshore-wind rows' 42% CF assumption turned out to already be
reasonably grounded (real projects: Norther/Belgium 43.1%, Alpha Ventus/Germany
42-42.7%, European fleet average ~45.8%) and needed no change beyond the grid-
factor correction.

**Known access limits from this research pass**: `cdm.unfccc.int` (UNFCCC's own
PDD database) is protected by Incapsula bot-detection and could not be fetched
directly — the Indian solar/wind CDM project examples cited are search-
synthesized, only internally consistency-checked (recomputing implied CF from
stated generation/capacity), not independently verified against a primary PDD.
`cdmpipeline.org` (UNEP DTU's historical CDM/JI Pipeline aggregator, once the
best source for "CERs issued per MW" across the whole Indian portfolio) has
expired and is now a squatted domain — do not point future research at it.
CarbonPlan's OffsetsDB (`carbonplan.org/research/offsets-db`) is a live,
downloadable alternative confirming renewable energy is 88.1% of India's
historical credit issuance (wind 35.9%, centralized solar 26.3%), but row-level
per-project data was not pulled from it in this pass.

## "CMAI" and other quantifying bodies — what was and wasn't useful

The user asked to check "CMAI" specifically. Identified with high confidence as
the **Carbon Markets Association of India** (`cma-india.in`) — a policy-
advocacy/convening body (MoUs with IICA, AREAS, VCMI), **not a quantitative
data publisher**. No capacity-to-credits or issuance-benchmark figures exist on
its site or in its public materials; cite it only as a policy/industry-body
reference if at all, never as a methodology source.

Other bodies checked, condensed: **Ecosystem Marketplace**'s State of the VCM
2025 report has market-level volume/price by category (renewable energy: 22.3
MtCO2e transacted in 2024 at avg $2.67/t) but no per-MW figures. **IGES**'s JCM
database can't help yet — the India-Japan JCM Memorandum of Cooperation is only
from Aug 2025, too new for meaningful project data. **BeZero/Sylvera** (carbon
credit rating agencies) turned out to be largely out of scope — they focus on
nature-based/removal credits, not grid-connected renewable energy. **S&P
Global/ICE/LSEG** publish price/liquidity data, not engineering benchmarks.

**CEEW was the one genuinely valuable additional find.** Their Aug 2025 issue
brief "Unlocking India's Voluntary Carbon Market: Challenges and the Path
Forward" (Kesh, Sharma, Chaturvedi) was fetched successfully via `curl` (where
an earlier attempt via WebFetch failed) and read directly, all 46 pages. The
PDF is saved locally at
[`docs/references/ceew_unlocking_indias_voluntary_carbon_market_2025.pdf`](references/ceew_unlocking_indias_voluntary_carbon_market_2025.pdf)
(original: https://ceew.in/sites/default/files/voluntary-carbon-offset-mechanism-and-challenges-in-carbon-credit-trading-scheme-market-for-india.pdf)
so the exact source text is available without re-fetching. Key figures pulled
into the platform:
- **India issued 278 million voluntary carbon credits between 2010 and 2022 —
  17% of global VCM supply** (their Introduction, citing Dyck et al. 2023 and
  S&P Global Commodity Insights).
- Of 598 India-linked Verra VCS projects (registered + unregistered) in their
  dataset: **Energy industries 46.06%, AFOLU 23.95%, Energy demand 23.62%,
  everything else combined just 6.37%** — a concentration pattern strikingly
  similar to the CCTS demand side's sector list.
- A global (not India-specific) additionality-risk data point worth flagging:
  since 2010, over 750 million voluntary carbon credits have been issued by
  1,700 renewable energy projects worldwide (~30% of all VCM credits), but
  these credits contributed **less than 4% of total revenue** for large-scale
  wind/hydro/solar installations (citing Loffler et al. 2024) — i.e. most such
  projects would very plausibly have been built anyway, a real financial-
  additionality concern for exactly the technology types this platform's
  supply-capacity model covers.
- The report itself is about *registration-process bottlenecks* (average
  Indian AFOLU project takes 1,689 days to register vs. 623 days for the rest
  of Asia; 71% of unregistered Indian energy-industries projects are already
  past the regional benchmark timeline), not capacity-to-credits engineering
  ratios — so it did not change any `CreditBenchmark` figures, only added
  market-scale context.

This confirms the general pattern already flagged in this document: reliable
quantitative capacity→credits ratios come from MNRE/CEA official statistics and
real project data (CDM PDDs, Kamuthi Solar Park), not from market-analysis or
policy-advocacy organizations, which publish volume/price/timeline data instead.

## The demand-model calculator is illustrative, not official

No public source publishes India's obligated-sector emissions or CCC demand/supply
in tCO2e. The `default_volume_mt` and `default_intensity_tco2_per_t` fields on each
`IndiaCctsSector` row are editable illustrative assumptions:
- Steel, aluminium, cement, and fertilizer intensities are reused from this
  platform's own CBAM default-value table (`CbamDefaultValue`) for internal
  consistency — those are real EU-published default values, reasonably
  representative of order-of-magnitude industrial emission intensity, but not
  India-specific official BEE baselines.
- Chlor-alkali, pulp & paper, petroleum refining, petrochemicals, and textiles
  intensities, and all sector production volumes, are rough order-of-magnitude
  estimates from general background knowledge, not independently verified in this
  research pass.

The `/api/india/demand-model` endpoint computes `baseline_emissions = volume x
intensity` and `illustrative_abatement_pool = baseline_emissions x
target_reduction_pct_avg`, and accepts per-sector overrides so this can be
re-modeled with better assumptions as real data becomes available.

## Ethanol/biofuel — investigated and deliberately excluded from international supply

A dedicated research pass (Sept 2026) checked whether Brazil (RenovaBio/CBIOs),
the USA (RFS RINs, California LCFS, the 45Z Clean Fuel Production Credit), the
EU (RED III), or India's own Ethanol Blended Petrol (EBP) programme could
plausibly supply carbon credits into India's Article 6.2/CCTS demand-supply
picture. Conclusion: **no**, for two independent and reinforcing reasons, with
one narrow future watch-item — reflected in the `Article6EligibleActivity`
model as an explicit `internationally_tradeable=False` row (`Ethanol / 1G
crop-based biofuel (India's EBP programme)`), not a silent omission.

**1. No international inflow pathway exists.** CBIOs, RINs, 45Z, and California
LCFS credits are domestic/state compliance instruments; the EU's RED III
doesn't even generate a discrete tradeable credit unit (certified biofuel just
gets a zero emission factor under EU ETS — an accounting convention, not a
credit). None of the three jurisdictions has a bilateral Article 6.2 agreement
with India. Brazil is separately drafting its own Article 6.2 ITMO framework
(public consultation opened Jul 2026), but that's a distinct instrument from
CBIOs, is being courted toward China rather than India in public reporting, and
it's unconfirmed whether ethanol activities would even qualify under Brazil's
own future eligible-activity list.

**2. India's own ethanol program is excluded from the Article 6.2 list by
design, not oversight — confirmed two independent ways**: MoEFCC/NDAIAPA's
13-category list, and the eligible-activities list under the newly-operational
India-Japan Joint Crediting Mechanism (JCM, MoC signed Aug 2025 — India's first
live Article 6.2 bilateral framework), which mirrors the same 13 categories.
Three converging structural reasons: (a) EBP/E20 (India crossed 20% blending
around Nov 2025, ~5 years ahead of schedule, mandatory nationwide from Apr
2026) is a national *mandate*, so its reduction is business-as-usual, not
additional; (b) BEE's one bioenergy CCTS Offset methodology (BM 001) requires
dedicated plantations, incompatible with India's existing sugarcane/maize/rice
1G feedstock base; (c) a real, documented food-security/ILUC-style
controversy — maize's share of ethanol feedstock rose from ~6% (ESY2022-23) to
~50% (ESY2024-25), with ~29% of India's 2024-25 maize crop diverted to ethanol
and 5.2 million tonnes of rice pulled from state reserves.

**Kept as a domestic-only row, not a supply gap.** Per the sector-level logic
already used for CCUS/energy-efficiency (`also_ccts_offset_eligible=True`
reflects Phase-1 CCTS Offset sector coverage — energy/agriculture here — not a
methodology-confirmed one-to-one fit), ethanol is marked
`also_ccts_offset_eligible=True`: plausibly usable for India's own *domestic*
CCTS compliance demand at the sector level, even though BM 001 as written
doesn't cleanly cover existing 1G feedstock. It stays `internationally_tradeable
=False` and is excluded from every Article 6.2 international-supply
calculation in this platform. Avoided-emissions figures for ethanol blending
were also found to be genuinely inconsistent across official Indian sources
(Minister Gadkari cited 73.6 Mt CO2e avoided from E20; a separate NITI-linked
figure cites ~93 Mt CO2e since ESY2014-15; another report cites 54.4 Mt "in a
decade") — flagged rather than picked, since none of these are used in any
calculation here.

**Narrow watch-item**: 2G/cellulosic ethanol (non-food biomass feedstock) is
structurally more compatible with BM 001's plantation-style logic and avoids
the food-security objection. If NDAIAPA revises its 13-category list (reviewable
roughly every 3 years) or BEE issues a dedicated 2G methodology, that specific
sub-activity could plausibly graduate to `internationally_tradeable=True` — but
there is no evidence this is imminent as of this research pass.

## India's CBAM export exposure (`IndiaCbamExportExposure`) — Eurostat Comext direct-query methodology

A separate research thread (Sept 2026) built out `IndiaCbamExportExposure`:
what India actually exports to the EU in the six CBAM-covered goods
categories (cement, fertilizers, aluminium, iron & steel, hydrogen,
electricity). The intended primary source was India's own government
export-statistics portal
(Tradestat/DGCIS), but that site is a JS-rendered form with no stable query
URL and was confirmed unscrapable. The fallback — used for all four
categories — is the **EU's own mirror data**: Eurostat Comext records every
tonne and euro the EU imports *from* India, which is definitionally the
same trade flow as "India exports to the EU," just recorded on the buyer's
side. This is a real primary source (an official EU statistical agency
publishing its own customs-derived import records), not a derived or
modeled estimate, even though it isn't literally an Indian government
document.

**Working query pattern**, discovered via a HEAD-request redirect check
and confirmed against the live API:
```
https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020.IN.{CN_CODE}.1.{INDICATOR}?format=SDMX-CSV&startPeriod={YEAR}&endPeriod={YEAR}
```
`A`=annual, `EU27_2020`=reporter, `IN`=partner (India), `1`=flow (import),
`{CN_CODE}`=CN4/CN6/CN8 product code, `{INDICATOR}`=`VALUE_IN_EUROS` or
`QUANTITY_IN_100KG` (`QUANTITY_IN_KG` is not a valid indicator and returns
an SDMX fault). Omitting the indicator returns all available indicators
for that code/year. An invalid or non-existent product code returns a
distinct `INVALID_QUERY_DIMENSION_VALUE` SOAP fault, which is how several
wrong/retired CN codes were caught during this research rather than
silently returning zero.

**Repeatable per-category workflow**: (1) verify the exact CBAM Annex I
CN-code scope for the sector via web search — several sectors turned out
to have partial-heading exclusions, not clean HS-chapter cutoffs (see
steel below); (2) query Eurostat Comext directly per code and year;
(3) cross-check the sum against any existing independently-sourced
aggregate (WITS, GTRI, Lok Sabha answers) as a sanity check, not a
replacement; (4) write seed rows with full `source_url`/`notes`
provenance; (5) reseed, restart, verify via the API and in the browser,
then commit.

**Cement**: expanded from one vague global-total row to 6 rows. Caught a
real overstatement in the process — the earlier HS6-level estimate for
kaolinic clay (CN 2507 00 80, sourced from Comtrade/WITS at $13.8M) turned
out, once queried at the true CN8 level, to have folded in non-CBAM-covered
raw kaolin (CN 2507 00 20) alongside the actually-covered kaolinic clay —
the real CN 2507 00 80 figure is roughly half that, ~€6.58M in 2024.

**Fertilizers**: expanded first to 6 WITS-sourced secondary rows, then the
`3102` (all) aggregate rows were replaced with 4 precise CN8-level primary
rows (urea, ammonium sulphate, sodium nitrate, other minor 3102 lines),
since Eurostat's product-level granularity let the aggregate be broken
apart into its real components instead of estimated as one bucket.

**Aluminium**: the earlier figures (~$3.0B/$2.77B) were *derived* — backed
out arithmetically from a GTRI press figure that combined steel and
aluminium into one aggregate. Once queried directly, the real Eurostat
totals were materially lower (~€835.7M-1,666.1M depending on year, i.e.
~$0.9-1.8B) — roughly 3x smaller than the derived estimate. Replaced
entirely (not added alongside) with 10 primary rows: a TOTAL plus the 7
largest individual CN-heading lines and one grouped-remainder row for
several smaller headings. The GTRI aggregate's scope/basis vs. customs HS
classification is the likely explanation for the gap, though this wasn't
independently confirmed.

**Iron & Steel** (most recent pass, most structurally complex — 35+
individual CN4 headings vs. aluminium's ~14): unlike aluminium, the
existing Lok Sabha/PIB fiscal-year rows (FY2019-20 through FY2024-25,
already primary-sourced from a written Parliament answer, plus one
GTRI-sourced FY2024-25 secondary row) were **kept, not replaced** — the
new Eurostat rows were **added** as a complementary CN-level breakdown.
The two sets of rows use genuinely different, non-comparable bases (India
fiscal year + India-self-reported export value, vs. EU calendar year +
EU-reported CIF import value), so their totals were never expected to
match and neither one supersedes the other; the Eurostat rows exist to
supply the *product-mix* detail (which specific steel goods, at what
value) that the fiscal-year aggregate rows don't carry.

Scope verification for steel surfaced a real nuance that was resolved
*before* writing any figures, not corrected after the fact: CBAM Annex I
covers Chapter 72 (22 headings; CN 7204, ferrous scrap, is explicitly
excluded) plus all of Chapter 73 (7301-7308) — 35 headings in total. Within
that, heading **7202 (ferro-alloys) is itself only partially covered**:
most 7202 sub-headings (ferro-molybdenum, -tungsten, -titanium, -vanadium,
-niobium, -phosphorus, -magnesium, -nickel, "other") are excluded from
CBAM like scrap is; only ferro-manganese (7202 11/19), ferro-silicon
(7202 21/29), ferro-silico-manganese (7202 30), and ferro-chromium
(7202 41/49) are actually covered. These 7 covered CN6 codes were queried
individually and summed (€343.6M of India's €352.8M total 7202 exports to
the EU in 2024, i.e. 97.5% of the heading) rather than using the raw HS4
total, so the seeded figure reflects only the CBAM-covered subset.

Seven new primary rows were added: a 2024 TOTAL across all 35 headings
(€4,610.7M / ~$4.98B — with 2023 at €4,755.9M and 2025 at €3,649.7M in the
row's notes, showing a directional -20.8% 2024→2025 drop broadly
consistent with, though not numerically reconciled to, GTRI's separately-
reported FY24→FY25 -35.1% figure), the five largest individual CN
headings by value (7208 hot-rolled flat ~$1.12B, 7210 coated/clad flat
~$948M, 7222 other alloy bars ~$479M, 7202-covered ferro-alloys ~$371M,
7209 cold-rolled flat ~$331M), and one grouped-remainder row (~$1.73B
across the other 30+ smaller headings, largest components named in its
`notes` field: 7207 semis, 7219 stainless flat, 7304 seamless tubes, 7306
other tubes, 7307 fittings, 7308 structures, 7206 primary forms, 7223
stainless wire).

**Hydrogen and electricity**: originally seeded as two secondary rows,
each a single sentence from a Centre for Science and Environment (CSE)
2024 study (via Down To Earth, 2 Jan 2026) stating India exports neither
to the EU. Both were upgraded to primary confidence by querying Eurostat
directly across 2023-2025, which confirmed the claim but with more
precision than the secondary source offered:
- **Electricity (CN 2716)** is genuinely, cleanly zero every year
  queried — Eurostat returns a valid-but-empty dataset for a real product
  code with no recorded trade, which is distinguishable in this API from
  querying an invalid code (that returns an explicit SDMX fault instead).
  Consistent with there being no direct India-EU grid interconnection.
- **Hydrogen is *not* a hard zero every year**: the CBAM-relevant CN8 code
  (2804 10 00) shows EUR 334 in 2023 (a single de minimis shipment), then
  EUR 0 in 2024 and 2025 — functionally no export industry, but a more
  precise finding than "zero." A second, easy-to-misread trap surfaced
  here too: the broader CN4 heading 2804 ("Hydrogen, rare gases and other
  non-metals") is **not** all-zero — it shows real trade (EUR 154,046 in
  2024) — but that trade is entirely in *other* gases sharing the same
  4-digit heading (nitrogen, oxygen, silicon, arsenic), not hydrogen
  itself, and none of it is CBAM-covered (Annex I's hydrogen scope is CN
  2804 10 00 specifically, not all of 2804). Querying only at CN4 without
  narrowing to the CN8 hydrogen-specific code would have wrongly
  suggested a nonzero hydrogen export flow.

**Closing out the remaining secondary rows** (a follow-up pass, same Sept
2026 session): after cement/fertilizer/aluminium/steel/hydrogen/
electricity were each given at least one primary pass, several individual
product-line rows within cement and fertilizers were still resting on
WITS/UN Comtrade secondary citations rather than a direct Eurostat query
-- these were closed out too, upgrading every row in the table to primary
except two that are deliberately left secondary (see below):
- **Cement's clinkers, white/other Portland, and aluminous/other-hydraulic
  lines** (previously 4 secondary WITS rows) were re-queried directly at
  CN8 and consolidated into 2 primary rows (the single largest line,
  aluminous cement 2523 30 00, plus a grouped remainder of the other four
  tiny lines) -- corroborating WITS almost exactly (e.g. clinkers 2024:
  WITS $790 vs Eurostat direct EUR 732 [~$791], same underlying customs
  record). Also fixed a stale code comment claiming Eurostat Comext
  "returned 404/blocked" for cement CN8 queries -- that was a tooling gap
  from an earlier session, contradicted by every other category in this
  table successfully querying Eurostat directly since.
- **Fertilizers' ammonia (2814), potassium nitrate (2834 21 00), and 3105
  multi-nutrient-blend lines** (previously 3 secondary WITS rows) were
  re-queried directly and corroborate WITS closely (potassium nitrate:
  WITS $1,659,700 vs Eurostat $1,656,046 for the same period). The
  multi-year Eurostat query surfaced a real trend the single-year WITS
  snapshot couldn't show: potassium nitrate more than tripled from EUR
  553,907 (2023) to EUR 2,086,582 (2025), and the 3105 blends line nearly
  tripled too (EUR 444,457 to EUR 1,139,189 over the same window,
  excluding CBAM-excluded CN 3105 60 00 throughout).
- **Two rows are deliberately left secondary, not overlooked**: cement's
  "CY2023 India global total, all destinations" row (a genuinely
  different, wider scope than an EU-import mirror -- there is nothing to
  re-query against Eurostat for that specific figure) and steel's
  FY2024-25 GTRI row (kept alongside, not replaced by, the primary
  Eurostat rows, for the same different-measurement-basis reason
  explained in the steel section above).

**A note on cross-verification, applied consistently across all four
categories**: the WITS/Comtrade/GTRI secondary figures were never treated
as wrong by default — they were used as the trigger to go get the primary
Eurostat figure, and in most cases (fertilizer's individual product lines,
steel's overall direction of travel) they corroborated reasonably well
once the scope was matched correctly. The two real corrections found
(cement's kaolinic-clay overstatement, aluminium's ~3x-high derived
estimate) were both caught *because* Eurostat was queried directly, not
assumed from the secondary source.

## Re-verifying this data

If this module is going into anything user-facing beyond a prototype demo, verify
against primary sources before publishing: BEE's Carbon Market page
(beeindia.gov.in), the actual G.S.R./S.O. gazette texts (egazette.gov.in), MoEFCC's
NDAIAPA authorization procedure documents, and the UNFCCC Article 6.2 Pipeline
tracker for any future India ITMO volume figures.
