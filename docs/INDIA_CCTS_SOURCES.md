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

## Re-verifying this data

If this module is going into anything user-facing beyond a prototype demo, verify
against primary sources before publishing: BEE's Carbon Market page
(beeindia.gov.in), the actual G.S.R./S.O. gazette texts (egazette.gov.in), MoEFCC's
NDAIAPA authorization procedure documents, and the UNFCCC Article 6.2 Pipeline
tracker for any future India ITMO volume figures.
