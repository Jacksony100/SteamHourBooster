from flask import Blueprint, redirect, render_template, request, session

from steam_hour_booster.security.rate_limit import rate_limit

from .decorators import login_required, subscription_required
from .service import record_login, register_user, verify_user


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
@login_required
@subscription_required
def index():
    return render_template(
        "index.html",
        username=session.get("username"),
        is_admin=session.get("is_admin"),
    )


@auth_bp.route("/register", methods=["GET", "POST"])
@rate_limit("register", limit=10, seconds=60)
def register():
    if request.method == "POST":
        success = register_user(request.form.get("username"), request.form.get("password"))
        if success:
            return redirect("/login")
        return render_template("register.html", error="Пользователь уже существует")
    return render_template("register.html", error=None)


@auth_bp.route("/login", methods=["GET", "POST"])
@rate_limit("login", limit=20, seconds=60)
def login():
    if request.method == "POST":
        user = verify_user(request.form.get("username"), request.form.get("password"))
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = user["is_admin"]
            record_login(user["id"], request.remote_addr or "unknown")
            return redirect("/")
        return render_template("login.html", error="Неверный логин/пароль или вы забанены")
    return render_template("login.html", error=None)


@auth_bp.route("/logout")
@rate_limit("logout", limit=60, seconds=60)
def logout():
    session.clear()
    return redirect("/login")
