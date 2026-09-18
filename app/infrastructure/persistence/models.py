import uuid
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _uuid():
    return str(uuid.uuid4())


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.String(10), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    co2_limit_kg = db.Column(db.Float, nullable=False, default=200.0)
    face_photo = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    transactions = db.relationship("TransactionModel", backref="user", lazy=True)


class TransactionModel(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    merchant_name = db.Column(db.String(120))
    merchant_category_code = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    co2_kg = db.Column(db.Float, nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
