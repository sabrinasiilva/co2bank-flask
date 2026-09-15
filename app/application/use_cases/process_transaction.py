from app.domain.entities.transaction import Transaction


def process_transaction(transaction: Transaction) -> None:
    """Orquestra: calcular CO2, atualizar limite mensal, disparar alerta se preciso."""
    raise NotImplementedError
