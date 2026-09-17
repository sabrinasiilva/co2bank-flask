from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.domain.entities.transaction import Transaction
from app.domain.services.co2_calculator import calculate_footprint
from app.infrastructure.persistence.models import TransactionModel, UserModel, db

transactions_bp = Blueprint("transactions", __name__, url_prefix="/transactions")

_MCC_LABELS = {
    "5541": "Combustível", "5542": "Combustível",
    "7011": "Hospedagem",
    "5812": "Restaurante", "5814": "Restaurante",
    "5411": "Supermercado",
    "4121": "Transporte",
    "5651": "Moda", "5699": "Moda",
    "5732": "Eletrônicos", "5722": "Eletrônicos",
    "5912": "Farmácia",
    "5815": "Streaming", "5817": "Streaming",
    "8211": "Educação", "8220": "Educação",
    "6011": "Financeiro",
}


def _mcc_label(mcc: str) -> str:
    if mcc in _MCC_LABELS:
        return _MCC_LABELS[mcc]
    try:
        code = int(mcc)
        if 3000 <= code <= 3350:
            return "Passagem aérea"
    except ValueError:
        pass
    return "Outros"


@transactions_bp.post("")
@jwt_required()
def create_transaction():
    user_id = get_jwt_identity()
    user = UserModel.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    data = request.get_json(silent=True) or {}

    required = ["merchant_category_code", "amount"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        amount = float(data["amount"])
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "amount deve ser um número positivo"}), 400

    occurred_at_raw = data.get("occurred_at")
    if occurred_at_raw:
        try:
            occurred_at = datetime.fromisoformat(occurred_at_raw)
        except ValueError:
            return jsonify({"error": "occurred_at inválido, use ISO 8601 (ex: 2026-09-17T10:00:00)"}), 400
    else:
        occurred_at = datetime.now(timezone.utc)

    domain_tx = Transaction(
        id="",
        user_id=user_id,
        merchant_category_code=str(data["merchant_category_code"]),
        amount=amount,
        occurred_at=occurred_at,
    )
    footprint = calculate_footprint(domain_tx)

    tx = TransactionModel(
        user_id=user_id,
        merchant_name=data.get("merchant_name", ""),
        merchant_category_code=str(data["merchant_category_code"]),
        amount=amount,
        co2_kg=footprint.kg_co2e,
        occurred_at=occurred_at,
    )
    db.session.add(tx)
    db.session.commit()

    return jsonify(_serialize(tx)), 201


@transactions_bp.get("")
@jwt_required()
def list_transactions():
    user_id = get_jwt_identity()

    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    limit = request.args.get("limit", default=50, type=int)

    query = TransactionModel.query.filter_by(user_id=user_id)

    if month and year:
        query = query.filter(
            db.extract("month", TransactionModel.occurred_at) == month,
            db.extract("year", TransactionModel.occurred_at) == year,
        )
    elif year:
        query = query.filter(
            db.extract("year", TransactionModel.occurred_at) == year,
        )

    txs = query.order_by(TransactionModel.occurred_at.desc()).limit(limit).all()
    return jsonify([_serialize(t) for t in txs]), 200


def _serialize(tx: TransactionModel) -> dict:
    return {
        "id": tx.id,
        "merchant_name": tx.merchant_name,
        "merchant_category_code": tx.merchant_category_code,
        "category_label": _mcc_label(tx.merchant_category_code),
        "amount": tx.amount,
        "co2_kg": tx.co2_kg,
        "occurred_at": tx.occurred_at.isoformat(),
        "created_at": tx.created_at.isoformat(),
    }
