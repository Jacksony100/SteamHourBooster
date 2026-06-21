from flask import Blueprint, jsonify, redirect, render_template, request, session

from steam_hour_booster.auth.decorators import login_required
from steam_hour_booster.security.rate_limit import rate_limit

from .service import amount_for_plan, create_crypto_charge, verify_coinbase_webhook


billing_bp = Blueprint("billing", __name__)


@billing_bp.route("/no_subscription")
@login_required
def no_subscription():
    return render_template("no_subscription.html")


@billing_bp.route("/buy_subscription", methods=["GET", "POST"])
@login_required
@rate_limit("buy_subscription", limit=20, seconds=60)
def buy_subscription():
    if request.method == "GET":
        return render_template("buy_subscription.html")

    plan = request.form.get("plan") or request.form.get("subscription_duration")
    payment_method = request.form.get("payment_method", "crypto")
    if payment_method != "crypto":
        return "Неизвестный метод оплаты.", 400

    payment_url = create_crypto_charge(plan, amount_for_plan(plan))
    if not payment_url:
        return "Ошибка создания платежа. Попробуйте позже.", 500

    session["pending_plan"] = plan
    return redirect(payment_url)


@billing_bp.route("/coinbase/webhook", methods=["POST"])
@rate_limit("coinbase_webhook", limit=120, seconds=60)
def coinbase_webhook():
    if not verify_coinbase_webhook(request.get_data(), request.headers.get("X-CC-Webhook-Signature", "")):
        return jsonify({"success": False, "error": "Invalid webhook signature"}), 400

    # Placeholder: subscription changes must be applied only after verified
    # webhook event parsing or an explicit audited admin action.
    return jsonify({"success": True, "received": True})
