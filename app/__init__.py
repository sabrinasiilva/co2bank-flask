from flask import Flask
from flask_cors import CORS

from config import get_config
from app.infrastructure.persistence.models import db
from app.interface.api.health import health_bp


def create_app(env: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(env))

    CORS(app)
    db.init_app(app)

    app.register_blueprint(health_bp)

    return app
