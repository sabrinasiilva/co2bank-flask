from dataclasses import dataclass


@dataclass
class CarbonLimit:
    user_id: str
    month: str
    limit_kg_co2e: float
    consumed_kg_co2e: float
