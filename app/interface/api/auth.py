import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from app.infrastructure.persistence.models import UserModel, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# {token: (user_id, expiry)} — in-memory, tokens expire in 15 min
_reset_tokens: dict[str, tuple[str, datetime]] = {}


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
        face_photo=data.get("face_photo"),
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


@auth_bp.post("/forgot-password/verify")
def forgot_password_verify():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    cpf = (data.get("cpf") or "").strip()
    birth_date = (data.get("birth_date") or "").strip()

    if not email or not cpf or not birth_date:
        return jsonify({"error": "Campos obrigatórios ausentes"}), 400

    user = UserModel.query.filter(func.lower(UserModel.email) == email.lower()).first()

    cpf_digits = "".join(c for c in cpf if c.isdigit())
    stored_cpf_digits = "".join(c for c in user.cpf if c.isdigit())

    if not user or stored_cpf_digits != cpf_digits or user.birth_date != birth_date:
        return jsonify({"error": "Dados inválidos ou não encontrados"}), 401

    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = (user.id, datetime.now(timezone.utc) + timedelta(minutes=15))

    return jsonify({"reset_token": token}), 200


@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    token = (data.get("reset_token") or "").strip()
    new_password = data.get("new_password") or ""

    if not token or not new_password:
        return jsonify({"error": "Campos obrigatórios ausentes"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "A senha deve ter pelo menos 6 caracteres"}), 400

    entry = _reset_tokens.get(token)
    if not entry:
        return jsonify({"error": "Token inválido ou expirado"}), 401

    user_id, expiry = entry
    if datetime.now(timezone.utc) > expiry:
        del _reset_tokens[token]
        return jsonify({"error": "Token expirado. Reinicie o processo"}), 401

    user = UserModel.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    del _reset_tokens[token]

    return jsonify({"message": "Senha redefinida com sucesso"}), 200


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
