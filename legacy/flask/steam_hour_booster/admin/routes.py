from flask import Blueprint, redirect, render_template, request, session

from steam_hour_booster.auth.decorators import admin_required, login_required
from steam_hour_booster.security.rate_limit import rate_limit

from .service import list_users, update_user_admin_state


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin", methods=["GET", "POST"])
@login_required
@admin_required
@rate_limit("admin_update", limit=60, seconds=60)
def admin_panel():
    if request.method == "POST":
        update_user_admin_state(request.form, actor_user_id=session.get("user_id"))
        return redirect("/admin")

    query = request.args.get("q", "")
    return render_template("admin.html", users=list_users(query), query=query)
