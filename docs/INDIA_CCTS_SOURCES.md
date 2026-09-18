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

## Re-verifying this data

If this module is going into anything user-facing beyond a prototype demo, verify
against primary sources before publishing: BEE's Carbon Market page
(beeindia.gov.in), the actual G.S.R./S.O. gazette texts (egazette.gov.in), MoEFCC's
NDAIAPA authorization procedure documents, and the UNFCCC Article 6.2 Pipeline
tracker for any future India ITMO volume figures.
