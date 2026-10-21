
from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.extensions import db, migrate, jwt, mail, redis_client
from app.models import User, AccountStatus, UserRole
from app.routes.auth import auth_bp
from app.utils.token_blocklist import is_token_revoked

def create_app(config_class=Config):
    app = Flask(__name__)

    # 1. Load the configuration.
    app.config.from_object(config_class)

    # TODO 2: Initialize SQLAlchemy.
    db.init_app(app)
    # TODO 3: Initialize Flask-Migrate.
    migrate.init_app(app, db)
    # TODO 4: Initialize JWTManager.
    jwt.init_app(app)
    # TODO 5: Initialize the token blocklist.
    @jwt.token_in_blocklist_loader

    def check_if_token_revoked(jwt_header, jwt_payload):
        return is_token_revoked(jwt_payload)

    mail.init_app(app)

    redis_client.init_app(app)
    # TODO 5: Configure CORS for your frontend origin.
    CORS(app=app,origins=[app.config.get("FRONTEND_ORIGIN")], supports_credentials=True)
    # TODO 6: Add GET /api/health.
    # It should return JSON indicating that the service is running.
    @app.route('/api/health')
    def health_check():
        return jsonify({"message" : "Application is up and running", "health" : "ok", "redis" : redis_client.ping()})

    # Inside create_app(), after initializing extensions:
    app.register_blueprint(auth_bp)
    
    return app
