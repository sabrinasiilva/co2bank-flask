from dataclasses import dataclass


@dataclass
class Reward:
    user_id: str
    partner_name: str
    token_amount: float
