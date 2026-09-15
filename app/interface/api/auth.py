from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash

from app.infrastructure.persistence.models import UserModel, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    required = ["name", "email", "cpf", "phone", "birth_date", "password"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    if UserModel.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "E-mail já cadastrado"}), 409

    if UserModel.query.filter_by(cpf=data["cpf"]).first():
        return jsonify({"error": "CPF já cadastrado"}), 409

    user = UserModel(
        name=data["name"],
        email=data["email"],
        cpf=data["cpf"],
        phone=data["phone"],
        birth_date=data["birth_date"],
        password_hash=generate_password_hash(data["password"]),
        co2_limit_kg=float(data.get("co2_limit_kg", 200.0)),
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({"token": token, "user": _serialize(user)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "E-mail e senha são obrigatórios"}), 400

    user = UserModel.query.filter_by(email=data["email"]).first()
    if not user or not check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "E-mail ou senha incorretos"}), 401

    token = create_access_token(identity=user.id)
    return jsonify({"token": token, "user": _serialize(user)}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user = UserModel.query.get(get_jwt_identity())
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify(_serialize(user)), 200


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
