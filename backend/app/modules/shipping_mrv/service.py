"""Pure emission arithmetic for shipping MRV (no DB access)."""
from __future__ import annotations

from typing import Iterable, Protocol

CO2_PER_TONNE_FUEL = 3.114  # IMO/EU standard VLSFO emission factor, tCO2 per tonne fuel
INTRA_EU_ETS_SHARE = 1.0  # intra-EU legs: 100% ETS exposure
EXTRA_EU_ETS_SHARE = 0.5  # extra-EU legs: 50% ETS exposure (Art. 3ga MRV Reg)


class VoyageLike(Protocol):
    fuel_consumed_mt: float
    intra_eu: bool


def summarise_voyages(voyages: Iterable[VoyageLike]) -> tuple[float, float]:
    """Return (total_co2_t, ets_eligible_co2_t) for voyages with fuel in tonnes (unrounded)."""
    voyages = list(voyages)
    total_co2 = sum(v.fuel_consumed_mt * CO2_PER_TONNE_FUEL for v in voyages)
    ets_eligible = sum(
        v.fuel_consumed_mt * CO2_PER_TONNE_FUEL * (INTRA_EU_ETS_SHARE if v.intra_eu else EXTRA_EU_ETS_SHARE)
        for v in voyages
    )
    return total_co2, ets_eligible
