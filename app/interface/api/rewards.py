from collections import defaultdict
from datetime import datetime, timezone

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.infrastructure.persistence.models import TransactionModel, UserModel

rewards_bp = Blueprint("rewards", __name__, url_prefix="/rewards")

_ALL_REWARDS = [
    {
        "id": "first_step",
        "title": "Primeiro Passo",
        "description": "Registre sua primeira transação",
        "icon": "foot_print",
    },
    {
        "id": "green_mind",
        "title": "Consciência Verde",
        "description": "Fique abaixo de 50% do limite de CO2 em um mês",
        "icon": "eco",
    },
    {
        "id": "planet_guardian",
        "title": "Guardião do Planeta",
        "description": "Fique abaixo de 25% do limite de CO2 em um mês",
        "icon": "shield",
    },
    {
        "id": "diversified",
        "title": "Consumidor Diversificado",
        "description": "Use 3 ou mais categorias de gastos diferentes",
        "icon": "category",
    },
    {
        "id": "two_months",
        "title": "Dois Meses no Verde",
        "description": "Fique abaixo do limite por 2 meses seguidos",
        "icon": "calendar",
    },
]


@rewards_bp.get("")
@jwt_required()
def get_rewards():
    user_id = get_jwt_identity()
    user = UserModel.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    txs = TransactionModel.query.filter_by(user_id=user_id).all()
    limit = user.co2_limit_kg

    earned_ids: dict[str, str] = {}

    # Primeiro Passo
    if txs:
        first_tx = min(txs, key=lambda t: t.created_at)
        earned_ids["first_step"] = first_tx.created_at.isoformat()

    # Consumidor Diversificado
    categories = {t.merchant_category_code for t in txs}
    if len(categories) >= 3:
        earned_ids["diversified"] = datetime.now(timezone.utc).isoformat()

    # Agrupando por mês para calcular recompensas mensais
    monthly: dict[tuple, list] = defaultdict(list)
    for t in txs:
        key = (t.occurred_at.year, t.occurred_at.month)
        monthly[key].append(t)

    green_months = []
    for (year, month), month_txs in monthly.items():
        co2 = sum(t.co2_kg for t in month_txs)
        pct = (co2 / limit * 100) if limit > 0 else 0

        if pct < 50:
            ref_date = month_txs[0].occurred_at.isoformat()
            green_months.append((year, month, pct, ref_date))

            if "green_mind" not in earned_ids:
                earned_ids["green_mind"] = ref_date

        if pct < 25 and "planet_guardian" not in earned_ids:
            earned_ids["planet_guardian"] = month_txs[0].occurred_at.isoformat()

    # Dois Meses no Verde (meses consecutivos abaixo do limite, qualquer %)
    months_under = sorted(
        [
            (y, m)
            for (y, m), mt in monthly.items()
            if sum(t.co2_kg for t in mt) < limit
        ]
    )
    for i in range(1, len(months_under)):
        prev_y, prev_m = months_under[i - 1]
        cur_y, cur_m = months_under[i]
        next_month = (prev_m % 12) + 1
        next_year = prev_y + (1 if prev_m == 12 else 0)
        if cur_y == next_year and cur_m == next_month:
            if "two_months" not in earned_ids:
                earned_ids["two_months"] = f"{cur_y}-{cur_m:02d}-01T00:00:00"
            break

    result = []
    for reward in _ALL_REWARDS:
        rid = reward["id"]
        earned = rid in earned_ids
        result.append({
            **reward,
            "earned": earned,
            "earned_at": earned_ids.get(rid),
        })

    total_earned = sum(1 for r in result if r["earned"])

    return jsonify({
        "total_earned": total_earned,
        "total": len(_ALL_REWARDS),
        "rewards": result,
    }), 200
