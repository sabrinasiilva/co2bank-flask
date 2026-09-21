from collections import defaultdict
from datetime import datetime, timezone
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.infrastructure.persistence.models import TransactionModel, UserModel, db
from app.infrastructure.ai_advisor.advisor import warn_if_needed
from app.interface.api.transactions import _mcc_label

limits_bp = Blueprint("limits", __name__, url_prefix="/check-limit")


@limits_bp.post("")
@jwt_required()
def check_limit():
    user_id = get_jwt_identity()
    user = UserModel.query.get(user_id)

    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    now = datetime.now(timezone.utc)

    txs = TransactionModel.query.filter_by(user_id=user_id).filter(
        db.extract("month", TransactionModel.occurred_at) == now.month,
        db.extract("year",  TransactionModel.occurred_at) == now.year,
    ).all()

    total_co2 = sum(t.co2_kg for t in txs)
    pct = (total_co2 / user.co2_limit_kg * 100) if user.co2_limit_kg > 0 else 0

    cat: dict[str, float] = defaultdict(float)
    for t in txs:
        cat[_mcc_label(t.merchant_category_code)] += t.co2_kg

    top = sorted(
        [{"category": k, "co2_kg": round(v, 2)} for k, v in cat.items()],
        key=lambda x: x["co2_kg"], reverse=True
    )[:3]

    return jsonify(warn_if_needed(user, pct, top)), 200
