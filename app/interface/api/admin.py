from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.infrastructure.persistence.models import UserModel

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/users")
@jwt_required()
def list_users():
    users = UserModel.query.order_by(UserModel.created_at.desc()).all()
    return jsonify([_serialize(u) for u in users]), 200


def _serialize(user: UserModel) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "phone": user.phone,
        "birth_date": user.birth_date,
        "co2_limit_kg": user.co2_limit_kg,
        "created_at": user.created_at.isoformat(),
    }
