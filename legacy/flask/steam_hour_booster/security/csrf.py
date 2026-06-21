from flask import abort, current_app, request, session
from secrets import token_urlsafe


def get_csrf_token() -> str:
    if "_csrf_token" not in session:
        session["_csrf_token"] = token_urlsafe(32)
    return session["_csrf_token"]


def init_csrf(app):
    app.jinja_env.globals["csrf_token"] = get_csrf_token

    @app.before_request
    def enforce_csrf_when_enabled():
        if not current_app.config.get("CSRF_ENABLED"):
            return None
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return None
        if request.path in current_app.config.get("CSRF_EXEMPT_PATHS", set()):
            return None
        token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not token or token != session.get("_csrf_token"):
            abort(400, description="Invalid CSRF token")
        return None
