
import re

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

from app.config import Config
from app.extensions import db, migrate, jwt, mail, redis_client
from app.models import User, AccountStatus, UserRole
from app.routes.auth import auth_bp
from app.routes.events import events_bp
from app.utils.token_blocklist import is_token_revoked
from app.routes.venues import venues_bp
from app.routes.seats import seats_bp
from app.routes.inventory import inventory_bp


def _swagger_path(path):
    """Convert Flask path parameters to OpenAPI path parameters."""
    return re.sub(r"<(?:[^:>]+:)?([^>]+)>", r"{\1}", path)


def _swagger_tag(endpoint):
    blueprint = endpoint.split(".", 1)[0]
    return {
        "auth": "Auth",
        "events": "Events",
        "venues": "Venues",
        "Seats": "Seats",
        "inventory": "Inventory",
        "health_check": "Health",
    }.get(blueprint, blueprint.replace("_", " ").title())


def _swagger_template(app):
    paths = {}
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/"):
            continue

        path = _swagger_path(rule.rule)
        path_item = paths.setdefault(path, {})
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            tag = _swagger_tag(rule.endpoint)
            operation = {
                "operationId": f"{rule.endpoint}_{method.lower()}",
                "summary": rule.endpoint.rsplit(".", 1)[-1].replace("_", " ").title(),
                "tags": [tag],
                "responses": {
                    "200": {
                        "description": "Request completed successfully."
                    },
                    "400": {
                        "description": "The request was invalid."
                    },
                    "401": {
                        "description": "Authentication is required."
                    },
                    "404": {
                        "description": "The requested resource was not found."
                    }
                }
            }
            path_parameters = re.findall(r"{([^}]+)}", path)
            if path_parameters:
                operation["parameters"] = [
                    {
                        "name": parameter,
                        "in": "path",
                        "required": True,
                        "type": "string"
                    }
                    for parameter in path_parameters
                ]
            path_item[method.lower()] = operation

    return {
        "swagger": "2.0",
        "info": {
            "title": "TicketMaster API",
            "description": "API endpoints for the TicketMaster backend.",
            "version": "1.0.0"
        },
        "basePath": "/",
        "schemes": ["http", "https"],
        "tags": [
            {"name": "Auth", "description": "Authentication and user account endpoints."},
            {"name": "Events", "description": "Event and occurrence endpoints."},
            {"name": "Venues", "description": "Venue endpoints."},
            {"name": "Seats", "description": "Seat endpoints."},
            {"name": "Inventory", "description": "Inventory management endpoints."},
            {"name": "Health", "description": "Service health endpoints."},
        ],
        "paths": paths
    }


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
    app.register_blueprint(events_bp)
    app.register_blueprint(venues_bp)
    app.register_blueprint(seats_bp)
    app.register_blueprint(inventory_bp)
    Swagger(
        app,
        config={
            "specs": [
                {
                    "endpoint": "ticketmaster_spec",
                    "route": "/api/swagger.json",
                    "rule_filter": lambda rule: rule.rule.startswith("/api/"),
                    "model_filter": lambda tag: True,
                }
            ],
            "specs_route": "/api/docs/",
        },
        template=_swagger_template(app),
        merge=True,
    )

    return app
