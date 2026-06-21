from functools import wraps

from flask import redirect, session

from steam_hour_booster.app import json_error, wants_json_response

from .service import get_user, has_active_subscription, is_admin, touch_last_seen


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            if wants_json_response():
                return json_error("Authentication required", 401, "authentication_required")
            return redirect("/login")

        touch_last_seen(user_id)
        return fn(*args, **kwargs)

    return wrapped


def subscription_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = get_user(session.get("user_id"))
        if user and user.get("banned") == 1:
            if wants_json_response():
                return json_error("User is banned", 403, "user_banned")
            return "Вы забанены.", 403

        if not has_active_subscription(user):
            if wants_json_response():
                return json_error("Active subscription required", 402, "subscription_required")
            return redirect("/no_subscription")

        return fn(*args, **kwargs)

    return wrapped


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = get_user(session.get("user_id"))
        if not is_admin(user):
            if wants_json_response():
                return json_error("Admin access required", 403, "admin_required")
            return redirect("/")
        return fn(*args, **kwargs)

    return wrapped
