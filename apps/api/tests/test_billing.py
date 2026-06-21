from types import SimpleNamespace

import app.billing.providers as providers_module
import app.billing.routes as billing_routes
import pytest
from app.core.database import SessionLocal
from app.core.models import AuditLog, BillingEvent, Payment, Plan, SteamAccount, Subscription, User

from .conftest import csrf, login, make_admin_user, register


def test_billing_plans_include_saas_limits(client):
    response = client.get("/api/v1/billing/plans")

    assert response.status_code == 200
    plans = {plan["code"]: plan for plan in response.json()}
    assert {"trial", "starter", "pro", "ultra", "lifetime"}.issubset(plans)
    assert plans["trial"]["account_limit"] == 1
    assert plans["trial"]["active_session_limit"] == 0
    assert plans["pro"]["account_limit"] == 10


def test_registration_creates_trial_subscription(client):
    response = register(client)
    assert response.status_code == 200

    subscription = client.get("/api/v1/billing/subscription")
    assert subscription.status_code == 200
    payload = subscription.json()
    assert payload["plan_code"] == "trial"
    assert payload["status"] == "trialing"
    assert payload["active"] is True
    assert payload["account_limit"] == 1


def test_trial_account_limit_blocks_second_account(client):
    register(client)
    headers = {"X-CSRF-Token": csrf(client)}
    first = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Main", "username": "steam-a", "password": "steam-pass", "ownership_attested": True},
        headers=headers,
    )
    second = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Alt", "username": "steam-b", "password": "steam-pass", "ownership_attested": True},
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 402
    assert second.json()["detail"] == "Plan account limit reached"


def test_mock_checkout_waits_for_verified_webhook(client):
    register(client)
    checkout = client.post(
        "/api/v1/billing/checkout",
        json={"plan_code": "starter"},
        headers={"X-CSRF-Token": csrf(client)},
    )
    assert checkout.status_code == 200
    payment = checkout.json()
    assert payment["status"] == "pending"

    before = client.get("/api/v1/billing/subscription").json()
    assert before["plan_code"] == "trial"

    webhook_payload = {
        "event_id": "evt_starter_paid",
        "event_type": "payment.paid",
        "status": "paid",
        "provider_payment_id": f"mock_{payment['idempotency_key']}",
    }
    webhook = client.post("/api/v1/billing/webhook/mock", json=webhook_payload)
    duplicate = client.post("/api/v1/billing/webhook/mock", json=webhook_payload)

    assert webhook.status_code == 200
    assert duplicate.status_code == 200
    assert webhook.json()["event_id"] == duplicate.json()["event_id"]
    after = client.get("/api/v1/billing/subscription").json()
    assert after["plan_code"] == "starter"
    assert after["status"] == "active"

    db = SessionLocal()
    try:
        assert db.query(Payment).one().status == "paid"
        assert db.query(BillingEvent).count() == 1
        assert db.query(AuditLog).filter(AuditLog.action == "billing.subscription_activated").count() == 1
        subscription = db.query(Subscription).one()
        first_expires_at = subscription.expires_at
    finally:
        db.close()

    second_duplicate = client.post("/api/v1/billing/webhook/mock", json=webhook_payload)
    assert second_duplicate.status_code == 200
    db = SessionLocal()
    try:
        subscription = db.query(Subscription).one()
        assert subscription.expires_at == first_expires_at
        assert db.query(BillingEvent).count() == 1
        assert db.query(AuditLog).filter(AuditLog.action == "billing.subscription_activated").count() == 1
    finally:
        db.close()


def test_checkout_rejects_client_provider_tampering(client):
    register(client)

    response = client.post(
        "/api/v1/billing/checkout",
        json={"plan_code": "starter", "provider": "mock"},
        headers={"X-CSRF-Token": csrf(client)},
    )

    assert response.status_code == 422
    db = SessionLocal()
    try:
        assert db.query(Payment).count() == 0
    finally:
        db.close()


def test_mock_webhook_is_hidden_in_production(client, monkeypatch):
    monkeypatch.setattr(billing_routes, "get_settings", lambda: SimpleNamespace(environment="production"))

    response = client.post("/api/v1/billing/webhook/mock", json={"event_id": "evt_prod_mock", "status": "paid"})

    assert response.status_code == 404


def test_provider_for_rejects_mock_in_production(monkeypatch):
    monkeypatch.setattr(providers_module, "get_settings", lambda: SimpleNamespace(environment="production", billing_provider="mock"))

    with pytest.raises(ValueError, match="Mock billing provider is forbidden"):
        providers_module.provider_for()


def test_unknown_webhook_provider_returns_controlled_error(client):
    response = client.post("/api/v1/billing/webhook/not-a-provider", json={"event_id": "evt_unknown"})

    assert response.status_code == 400
    assert "Unsupported billing provider" in response.json()["detail"]


def test_provider_mismatch_does_not_mutate_payment_or_subscription(client):
    register(client)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "alice").one()
        plan = db.query(Plan).filter(Plan.code == "starter").one()
        payment = Payment(
            user_id=user.id,
            plan_id=plan.id,
            provider="mock",
            provider_payment_id="mock_pay_provider_mismatch",
            idempotency_key="pay_provider_mismatch",
            checkout_url="/billing/pending?payment=pay_provider_mismatch",
            status="pending",
            amount_cents=plan.price_cents,
            currency="USD",
        )
        db.add(payment)
        db.commit()
    finally:
        db.close()

    coinbase_payload = {
        "event": {
            "id": "evt_coinbase_mismatch",
            "type": "charge:confirmed",
            "data": {
                "id": "coinbase_charge_mismatch",
                "timeline": [{"status": "COMPLETED"}],
                "metadata": {"idempotency_key": "pay_provider_mismatch"},
            },
        }
    }
    response = client.post("/api/v1/billing/webhook/coinbase", json=coinbase_payload, headers={"X-CC-Webhook-Signature": "invalid"})

    assert response.status_code == 200
    assert response.json()["payment_id"] is None
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.idempotency_key == "pay_provider_mismatch").one()
        subscription = db.query(Subscription).filter(Subscription.user_id == payment.user_id).one()
        event = db.query(BillingEvent).one()
        assert payment.status == "pending"
        assert subscription.plan_code == "trial"
        assert event.payment_id is None
    finally:
        db.close()


def test_invalid_coinbase_signature_records_unverified_event_without_activation(client):
    register(client)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "alice").one()
        plan = db.query(Plan).filter(Plan.code == "starter").one()
        payment = Payment(
            user_id=user.id,
            plan_id=plan.id,
            provider="coinbase",
            provider_payment_id="charge_invalid_signature",
            idempotency_key="pay_coinbase_invalid_signature",
            checkout_url="https://commerce.coinbase.com/charges/charge_invalid_signature",
            status="pending",
            amount_cents=plan.price_cents,
            currency="USD",
        )
        db.add(payment)
        db.commit()
    finally:
        db.close()

    payload = {
        "event": {
            "id": "evt_coinbase_invalid_signature",
            "type": "charge:confirmed",
            "data": {
                "id": "charge_invalid_signature",
                "timeline": [{"status": "COMPLETED"}],
                "metadata": {"idempotency_key": "pay_coinbase_invalid_signature"},
            },
        }
    }
    response = client.post("/api/v1/billing/webhook/coinbase", json=payload, headers={"X-CC-Webhook-Signature": "invalid"})

    assert response.status_code == 200
    assert response.json()["verified"] is False
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.idempotency_key == "pay_coinbase_invalid_signature").one()
        subscription = db.query(Subscription).filter(Subscription.user_id == payment.user_id).one()
        event = db.query(BillingEvent).one()
        assert payment.status == "pending"
        assert subscription.plan_code == "trial"
        assert event.verified is False
        assert event.created_at is not None
    finally:
        db.close()


def test_admin_can_change_extend_and_cancel_subscription(client):
    register(client, "alice", "secret123")
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf(client)})
    make_admin_user()
    login(client, "admin", "admin-password")

    db = SessionLocal()
    try:
        alice = db.query(User).filter(User.username == "alice").one()
        alice_id = alice.id
    finally:
        db.close()

    headers = {"X-CSRF-Token": csrf(client)}
    grant = client.patch(
        f"/api/v1/admin/users/{alice_id}/subscription",
        json={"plan_code": "ultra", "status": "active", "extend_days": 30, "reason": "support grant"},
        headers=headers,
    )
    cancel = client.patch(
        f"/api/v1/admin/users/{alice_id}/subscription",
        json={"status": "canceled", "reason": "manual test"},
        headers=headers,
    )

    assert grant.status_code == 200
    assert grant.json()["plan_code"] == "ultra"
    assert grant.json()["account_limit"] == 30
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "canceled"

    db = SessionLocal()
    try:
        sub = db.query(Subscription).filter(Subscription.user_id == alice_id).one()
        assert sub.manual_override is True
        assert db.query(AuditLog).filter(AuditLog.action == "admin.subscription_update").count() == 2
        assert db.query(SteamAccount).count() == 0
    finally:
        db.close()
