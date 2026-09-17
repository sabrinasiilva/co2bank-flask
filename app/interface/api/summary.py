from collections import defaultdict
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.infrastructure.persistence.models import TransactionModel, UserModel, db
from app.interface.api.transactions import _mcc_label

summary_bp = Blueprint("summary", __name__, url_prefix="/summary")


@summary_bp.get("/monthly")
@jwt_required()
def monthly_summary():
    user_id = get_jwt_identity()
    user = UserModel.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    now = datetime.now(timezone.utc)
    month = request.args.get("month", default=now.month, type=int)
    year = request.args.get("year", default=now.year, type=int)

    txs = TransactionModel.query.filter_by(user_id=user_id).filter(
        db.extract("month", TransactionModel.occurred_at) == month,
        db.extract("year", TransactionModel.occurred_at) == year,
    ).all()

    total_co2_kg = round(sum(t.co2_kg for t in txs), 4)
    total_spent_brl = round(sum(t.amount for t in txs), 2)

    category_co2: dict[str, float] = defaultdict(float)
    for t in txs:
        category_co2[_mcc_label(t.merchant_category_code)] += t.co2_kg

    top_categories = sorted(
        [{"category": k, "co2_kg": round(v, 4)} for k, v in category_co2.items()],
        key=lambda x: x["co2_kg"],
        reverse=True,
    )[:5]

    limit_kg = user.co2_limit_kg
    percentage_used = round((total_co2_kg / limit_kg) * 100, 1) if limit_kg > 0 else 0.0

    return jsonify({
        "month": month,
        "year": year,
        "total_co2_kg": total_co2_kg,
        "limit_kg": limit_kg,
        "percentage_used": percentage_used,
        "total_spent_brl": total_spent_brl,
        "transactions_count": len(txs),
        "top_categories": top_categories,
    }), 200
