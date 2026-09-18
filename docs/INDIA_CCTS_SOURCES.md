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
- PIB primary press releases returned HTTP 403 to automated fetch during research —
  everything attributed to PIB above is via secondary reporting that cites it, not
  a page read directly.

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
