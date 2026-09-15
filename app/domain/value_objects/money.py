from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "BRL"
