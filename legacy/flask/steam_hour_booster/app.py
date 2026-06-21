from flask import Flask, jsonify, request

from .config import Config
from .extensions import init_extensions
from .security.encryption_service import EncryptionService


def create_app(config_object=None, **config_overrides):
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(config_object or Config)
    app.config.update(config_overrides)
    validate_security_config(app)
    app.config["ENCRYPTION_KEY"] = app.config.get("ENCRYPTION_KEY") or Config.load_encryption_key()

    app.extensions["encryption_service"] = EncryptionService(app.config["ENCRYPTION_KEY"])

    init_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_security_headers(app)
    return app


def validate_security_config(app: Flask) -> None:
    if app.config.get("TESTING"):
        return

    secret_key = app.config.get("SECRET_KEY")
    if not secret_key or len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY must be set from env and be at least 32 characters.")

    if not app.config.get("ENCRYPTION_KEY"):
        raise RuntimeError("ENCRYPTION_KEY must be set from env.")


def register_blueprints(app: Flask) -> None:
    from .accounts.routes import accounts_bp
    from .admin.routes import admin_bp
    from .auth.routes import auth_bp
    from .billing.routes import billing_bp
    from .games.routes import games_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(admin_bp)


def wants_json_response() -> bool:
    return request.is_json or request.accept_mimetypes.best == "application/json"


def json_error(message: str, status: int = 400, code: str = "bad_request"):
    payload = {
        "success": False,
        "error": message,
        "code": code,
    }
    return jsonify(payload), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def handle_bad_request(error):
        if wants_json_response():
            message = getattr(error, "description", None) or "Bad request"
            return json_error(message, 400, "bad_request")
        return getattr(error, "description", "Bad request"), 400

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        return json_error(str(error), 400, "validation_error")

    @app.errorhandler(404)
    def handle_not_found(_error):
        if wants_json_response():
            return json_error("Not found", 404, "not_found")
        return "Not found", 404

    @app.errorhandler(500)
    def handle_internal_error(_error):
        if wants_json_response():
            return json_error("Internal server error", 500, "internal_error")
        return "Internal server error", 500


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'",
        )
        return response
