from app.domain.entities.transaction import Transaction
from app.domain.value_objects.carbon_footprint import CarbonFootprint


def calculate_footprint(transaction: Transaction) -> CarbonFootprint:
    """Estima o CO2e de uma transação a partir da categoria (MCC) e valor.

    Fatores por categoria ainda não definidos — ver tabela de referência v0
    no README (metodologia Doconomy/Índice Åland, EEIO/DEFRA).
    """
    raise NotImplementedError
