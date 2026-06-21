from app.billing.service import sync_default_plans
from app.core.database import SessionLocal
from app.core.models import AuditLog, Payment, Plan, SessionStatus, SteamSession, User

from .conftest import activate_subscription, csrf, login, make_admin_user, register


def _admin_login(client):
    make_admin_user()
    login(client, "admin", "admin-password")


def _create_online_account_with_game(client):
    create = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Main", "username": "steam-a", "password": "steam-pass", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )
    assert create.status_code == 200
    account_id = create.json()["id"]
    assert client.post(f"/api/v1/steam-accounts/{account_id}/login", json={}, headers={"X-CSRF-Token": csrf(client)}).status_code == 200
    assert client.put(f"/api/v1/games/{account_id}", json={"app_ids": [730]}, headers={"X-CSRF-Token": csrf(client)}).status_code == 200
    return account_id


def test_admin_control_center_routes_are_admin_only(client):
    register(client)

    for method, path in [
        ("get", "/api/v1/admin/overview"),
        ("get", "/api/v1/admin/users"),
        ("get", "/api/v1/admin/payments"),
        ("get", "/api/v1/admin/audit"),
        ("get", "/api/v1/admin/subscription-changes"),
    ]:
        response = getattr(client, method)(path)
        assert response.status_code == 403


def test_admin_overview_users_detail_payments_and_audit(client):
    register(client, "alice", "secret123")
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf(client)})

    db = SessionLocal()
    try:
        sync_default_plans(db)
        alice = db.query(User).filter(User.username == "alice").one()
        plan = db.query(Plan).filter(Plan.code == "pro").one()
        db.add(
            Payment(
                user_id=alice.id,
                plan_id=plan.id,
                provider="mock",
                provider_payment_id="mock_admin_test",
                idempotency_key="pay_admin_test",
                status="paid",
                amount_cents=plan.price_cents,
                currency="USD",
            )
        )
        db.commit()
    finally:
        db.close()

    _admin_login(client)
    overview = client.get("/api/v1/admin/overview")
    users = client.get("/api/v1/admin/users?query=alice&filter=subscribed&page=1&page_size=10")
    user_id = users.json()["items"][0]["id"]
    detail = client.get(f"/api/v1/admin/users/{user_id}")
    payments = client.get("/api/v1/admin/payments")
    audit = client.get("/api/v1/admin/audit")

    assert overview.status_code == 200
    assert overview.json()["payments_total_cents"] == 1900
    assert users.status_code == 200
    assert users.json()["total"] == 1
    assert detail.status_code == 200
    assert detail.json()["user"]["username"] == "alice"
    assert detail.json()["payments"][0]["status"] == "paid"
    assert payments.status_code == 200
    assert payments.json()[0]["username"] == "alice"
    assert audit.status_code == 200


def test_admin_self_revoke_requires_confirmation(client):
    _admin_login(client)
    me = client.get("/api/v1/auth/me").json()
    headers = {"X-CSRF-Token": csrf(client)}

    denied = client.patch(f"/api/v1/admin/users/{me['id']}", json={"is_admin": False}, headers=headers)
    allowed = client.patch(
        f"/api/v1/admin/users/{me['id']}",
        json={"is_admin": False, "confirm_self_admin_revoke": True, "reason": "explicit self revoke test"},
        headers=headers,
    )

    assert denied.status_code == 400
    assert denied.json()["detail"] == "Self admin revoke requires explicit confirmation"
    assert allowed.status_code == 200
    assert allowed.json()["is_admin"] is False


def test_admin_force_logout_sessions_stops_user_sessions_and_writes_audit(client):
    register(client, "alice", "secret123")
    activate_subscription("alice")
    account_id = _create_online_account_with_game(client)
    started = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})
    assert started.status_code == 200
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf(client)})

    db = SessionLocal()
    try:
        alice_id = db.query(User).filter(User.username == "alice").one().id
    finally:
        db.close()

    _admin_login(client)
    response = client.post(
        f"/api/v1/admin/users/{alice_id}/force-logout-sessions",
        json={"reason": "support request"},
        headers={"X-CSRF-Token": csrf(client)},
    )

    assert response.status_code == 200
    assert response.json()["stopped_sessions"] == 1

    db = SessionLocal()
    try:
        session = db.query(SteamSession).filter(SteamSession.user_id == alice_id).one()
        assert session.status == SessionStatus.stopped.value
        assert db.query(AuditLog).filter(AuditLog.action == "admin.force_logout_sessions").count() == 1
    finally:
        db.close()


def test_failed_login_is_counted_without_logging_password(client):
    register(client, "alice", "secret123")
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf(client)})
    failed = login(client, "alice", "wrong-password")
    _admin_login(client)
    overview = client.get("/api/v1/admin/overview")

    assert failed.status_code == 401
    assert overview.json()["failed_logins"] == 1

    db = SessionLocal()
    try:
        event = db.query(AuditLog).filter(AuditLog.action == "auth.login_failed").one()
        assert "wrong-password" not in event.metadata_json
    finally:
        db.close()
