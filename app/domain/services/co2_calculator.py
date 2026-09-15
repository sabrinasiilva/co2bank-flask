from app.domain.entities.transaction import Transaction
from app.domain.value_objects.carbon_footprint import CarbonFootprint

# Fatores de emissão por MCC (kg CO2e por R$ 100 gastos).
# Estimativa ilustrativa baseada em Doconomy/Åland Index + EEIO/DEFRA,
# calibrada para o perfil brasileiro (matriz elétrica limpa, alta emissão agropecuária).
# Não usar como dado auditado — ver README para contexto completo.
_MCC_FACTORS: dict[str, float] = {
    # Combustível / posto
    "5541": 30.0,
    "5542": 30.0,
    # Passagens aéreas
    **{str(mcc): 37.0 for mcc in range(3000, 3351)},
    # Hospedagem / hotel
    "7011": 12.0,
    # Restaurante / fast-food
    "5812": 10.0,
    "5814": 10.0,
    # Supermercado (peso maior pelo perfil agropecuário brasileiro)
    "5411": 8.0,
    # Transporte por app / táxi
    "4121": 8.5,
    # Moda / vestuário
    "5651": 6.5,
    "5699": 6.5,
    # Eletrônicos (peso menor pela matriz elétrica limpa)
    "5732": 5.0,
    "5722": 5.0,
    # Farmácia / saúde
    "5912": 3.0,
    # Assinaturas digitais / streaming
    "5815": 1.0,
    "5817": 1.0,
    # Educação
    "8211": 1.5,
    "8220": 1.5,
    # Serviços financeiros / Pix
    "6011": 0.35,
}

_DEFAULT_FACTOR = 5.0  # categoria não mapeada


def calculate_footprint(transaction: Transaction) -> CarbonFootprint:
    factor = _MCC_FACTORS.get(transaction.merchant_category_code, _DEFAULT_FACTOR)
    kg = (transaction.amount / 100.0) * factor
    return CarbonFootprint(kg_co2e=round(kg, 4))
