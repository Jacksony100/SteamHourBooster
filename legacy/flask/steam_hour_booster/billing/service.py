import logging
import hmac
from hashlib import sha256

import requests
from flask import current_app

logger = logging.getLogger(__name__)

PLAN_AMOUNTS = {
    "1_week": "10.00",
    "1_month": "15.00",
    "3_months": "25.00",
    "6_months": "40.00",
    "12_months": "70.00",
    "lifetime": "150.00",
}


def amount_for_plan(plan: str) -> str:
    return PLAN_AMOUNTS.get(plan, "0.00")


def create_crypto_charge(plan: str, amount: str, currency: str = "USD") -> str | None:
    api_key = current_app.config.get("COINBASE_API_KEY")
    if not api_key:
        logger.warning("Coinbase API key is not configured")
        return None

    headers = {
        "X-CC-Api-Key": api_key,
        "X-CC-Version": "2018-03-22",
        "Content-Type": "application/json",
    }
    payload = {
        "name": f"Подписка {plan}",
        "description": f"Подписка по тарифу: {plan}",
        "local_price": {
            "amount": amount,
            "currency": currency,
        },
        "pricing_type": "fixed_price",
    }
    try:
        response = requests.post(
            current_app.config["COINBASE_CHARGE_URL"],
            headers=headers,
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["data"]["hosted_url"]
    except Exception:
        logger.exception("Unable to create Coinbase charge")
        return None


def verify_coinbase_webhook(raw_body: bytes, signature: str) -> bool:
    secret = current_app.config.get("COINBASE_WEBHOOK_SECRET")
    if not secret or not signature:
        logger.warning("Coinbase webhook rejected: missing signature configuration")
        return False

    expected = hmac.new(secret.encode("utf-8"), raw_body, sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
