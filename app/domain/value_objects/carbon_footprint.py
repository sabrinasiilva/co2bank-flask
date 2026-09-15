from dataclasses import dataclass


@dataclass(frozen=True)
class CarbonFootprint:
    kg_co2e: float
