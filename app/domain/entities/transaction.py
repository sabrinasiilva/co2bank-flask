from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transaction:
    id: str
    user_id: str
    merchant_category_code: str
    amount: float
    occurred_at: datetime
