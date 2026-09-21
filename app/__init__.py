from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import get_config
from app.infrastructure.persistence.models import db
from app.interface.api.health import health_bp
from app.interface.api.auth import auth_bp
from app.interface.api.admin import admin_bp
from app.interface.api.transactions import transactions_bp
from app.interface.api.summary import summary_bp
from app.interface.api.rewards import rewards_bp


from app.interface.api.limits import limits_bp

def create_app(env: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(env))

    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)
    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(rewards_bp)
    
    
    app.register_blueprint(limits_bp)

    with app.app_context():
        db.create_all()

    return app