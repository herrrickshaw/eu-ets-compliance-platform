"""Seed tables: verification (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .tables_ets import _SEC

# ---- What real MRV/verification integrity looks like, next to the 2-record demo queue above ----
# All rows SECONDARY (search synthesis, not a primary document read directly this session). The
# integrity_controversy rows are additionally CONTESTED -- Verra publicly disputes the investigation's
# framing -- flagged explicitly rather than presented as settled fact.
_GUARDIAN_VERRA_2023 = "https://www.theguardian.com/environment/2023/jan/18/revealed-forest-carbon-offsets-biggest-provider-worthless-verra-aoe"

_VERRA_RESPONSE = "https://verra.org/verra-response-guardian-rainforest-carbon-offsets/"

integrity_stats = [
    dict(category="integrity_controversy", metric_label="Verra REDD+ credits alleged as 'phantom credits'",
         period="2023 investigation (Guardian/Die Zeit/SourceMaterial)", value=90, unit="% (alleged, CONTESTED)",
         source_name="The Guardian, Die Zeit, SourceMaterial joint investigation, Jan 2023",
         source_url=_GUARDIAN_VERRA_2023, source_confidence=_SEC,
         notes="The investigation's central claim: >90% of Verra's rainforest (REDD+) offset "
         "credits examined were likely 'phantom credits' not representing real emissions "
         "reductions, based partly on a 2022 University of Cambridge study finding deforestation "
         "threat had been overstated by ~400% on average across Verra projects. VERRA PUBLICLY "
         "DISPUTES this characterization (see verra_response row) -- treat as a contested, not "
         "settled, finding. Directly relevant to this page: it's exactly the kind of failure a "
         "verification/audit stage is meant to catch, and a reminder that third-party "
         "accreditation alone doesn't guarantee it does."),
    dict(category="integrity_controversy", metric_label="Verra REDD+ credits alleged to have zero/limited climate benefit",
         period="2023 investigation", value=94, unit="% (alleged, CONTESTED)",
         source_name="The Guardian, Die Zeit, SourceMaterial joint investigation, Jan 2023",
         source_url=_GUARDIAN_VERRA_2023, source_confidence=_SEC,
         notes="The investigation's more specific claim: of the credits analyzed, 94% should not "
         "have been approved at all under Verra's own stated methodology, due to zero or limited "
         "verifiable benefit to the climate."),
    dict(category="integrity_controversy", metric_label="Verra's own response to the investigation",
         period="2023", value=None, unit="qualitative",
         source_name="Verra, official response statement", source_url=_VERRA_RESPONSE,
         source_confidence=_SEC,
         notes="Verra's position: the investigation's methodology and conclusions are inaccurate, "
         "and REDD+ projects are not 'consistently and substantively over-issuing' credits as "
         "characterized. This remains a genuinely unresolved dispute in the field as of this "
         "research -- included here for both sides, not as a verdict."),
    dict(category="integrity_controversy", metric_label="Verra's share of all VCM offset approvals",
         period="as of 2023 investigation", value=75, unit="% of all VCM offsets",
         source_name="The Guardian, Die Zeit, SourceMaterial joint investigation, Jan 2023",
         source_url=_GUARDIAN_VERRA_2023, source_confidence=_SEC,
         notes="Consistent with Verra/VCS's well-established position as the largest single VCM "
         "registry, referenced elsewhere in this platform's Credit sourcing page. A dominant "
         "registry's integrity issues have outsized market-wide impact for exactly this reason."),
    dict(category="integrity_controversy", metric_label="Rainforest (REDD+) program share of Verra's own approvals",
         period="as of 2023 investigation", value=40, unit="% of Verra's approved credits",
         source_name="The Guardian, Die Zeit, SourceMaterial joint investigation, Jan 2023",
         source_url=_GUARDIAN_VERRA_2023, source_confidence=_SEC, notes=None),
    dict(category="integrity_response", metric_label="Carbon-crediting programs with ICVCM Core Carbon Principle (CCP) approval",
         period="end of Nov 2025", value=7, unit="programs",
         source_name="ICVCM (Integrity Council for the Voluntary Carbon Market), via search synthesis",
         source_url="https://icvcm.org/core-carbon-principles/", source_confidence=_SEC,
         notes="ICVCM's CCP label is the market's institutional response to exactly the kind of "
         "integrity controversy above -- a post-hoc quality assessment layered on top of existing "
         "registries (Verra, Gold Standard, ACR, etc.), not a replacement for them."),
    dict(category="integrity_response", metric_label="Methodologies with CCP approval",
         period="end of Nov 2025", value=36, unit="methodologies",
         source_name="ICVCM (Integrity Council for the Voluntary Carbon Market), via search synthesis",
         source_url="https://icvcm.org/core-carbon-principles/", source_confidence=_SEC,
         notes="Up from an initial cohort approved in June 2024 -- CCP-labeling is still an "
         "actively expanding, recent (since 2023) framework, not yet covering the whole market."),
    dict(category="integrity_response", metric_label="Carbon credits eligible for the CCP label (initial cohort)",
         period="June 2024", value=27, unit="million credits",
         source_name="ICVCM (Integrity Council for the Voluntary Carbon Market), via search synthesis",
         source_url="https://icvcm.org/core-carbon-principles/", source_confidence=_SEC,
         notes="The initial approved-methodology cohort only -- likely larger now given the "
         "additional methodology approvals through Nov 2025, but no updated total figure was "
         "found and confirmed this session, so this earlier figure is shown rather than an "
         "unverified guess at the current one."),
]
