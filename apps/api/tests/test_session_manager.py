from app.core.database import SessionLocal
from app.core.models import SessionEvent, SessionStatus, SteamSession
from app.sessions.adapters import MockSteamClientAdapter, set_steam_client_adapter

from .conftest import activate_subscription, csrf, register


def _create_online_account_with_game(client, label: str = "Main", app_id: int = 730) -> int:
    create = client.post(
        "/api/v1/steam-accounts",
        json={"label": label, "username": f"steam-{label}", "password": "steam-pass", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )
    assert create.status_code == 200
    account_id = create.json()["id"]
    login = client.post(f"/api/v1/steam-accounts/{account_id}/login", json={}, headers={"X-CSRF-Token": csrf(client)})
    assert login.status_code == 200
    games = client.put(f"/api/v1/games/{account_id}", json={"app_ids": [app_id]}, headers={"X-CSRF-Token": csrf(client)})
    assert games.status_code == 200
    return account_id


def test_cannot_start_session_without_subscription_capacity(client):
    register(client)
    account_id = _create_online_account_with_game(client)

    denied = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})

    assert denied.status_code == 402
    assert denied.json()["detail"] == "Plan active session limit reached"


def test_cannot_start_session_for_another_users_account(client):
    register(client, "alice", "secret123")
    activate_subscription("alice")
    account_id = _create_online_account_with_game(client)

    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf(client)})
    register(client, "bob", "secret123")
    denied = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})

    assert denied.status_code == 404


def test_cannot_exceed_plan_active_session_limit(client):
    register(client)
    activate_subscription(plan_code="starter")
    first_account = _create_online_account_with_game(client, "Main", 730)
    second_account = _create_online_account_with_game(client, "Alt", 570)

    first = client.post("/api/v1/sessions", json={"account_id": first_account}, headers={"X-CSRF-Token": csrf(client)})
    second = client.post("/api/v1/sessions", json={"account_id": second_account}, headers={"X-CSRF-Token": csrf(client)})

    assert first.status_code == 200
    assert second.status_code == 402
    assert second.json()["detail"] == "Plan active session limit reached"


def test_start_session_is_idempotent(client):
    register(client)
    activate_subscription()
    account_id = _create_online_account_with_game(client)

    first = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})
    second = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["status"] == SessionStatus.running.value


def test_stop_session_is_idempotent(client):
    register(client)
    activate_subscription()
    account_id = _create_online_account_with_game(client)
    started = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})
    session_id = started.json()["id"]

    first = client.post(f"/api/v1/sessions/{session_id}/stop", headers={"X-CSRF-Token": csrf(client)})
    second = client.post(f"/api/v1/sessions/{session_id}/stop", headers={"X-CSRF-Token": csrf(client)})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == SessionStatus.stopped.value
    assert second.json()["status"] == SessionStatus.stopped.value


def test_mock_client_start_errors_are_recorded(client):
    register(client)
    activate_subscription()
    account_id = _create_online_account_with_game(client)
    set_steam_client_adapter(MockSteamClientAdapter(fail_start=True))

    response = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})

    assert response.status_code == 400
    db = SessionLocal()
    try:
        session = db.query(SteamSession).one()
        assert session.status == SessionStatus.error.value
        assert "failed to start" in (session.error_message or "")
        assert db.query(SessionEvent).filter(SessionEvent.event_type == "session_error").count() == 1
    finally:
        db.close()


def test_session_events_written(client):
    register(client)
    activate_subscription()
    account_id = _create_online_account_with_game(client)
    started = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})
    session_id = started.json()["id"]
    client.post(f"/api/v1/sessions/{session_id}/stop", headers={"X-CSRF-Token": csrf(client)})

    events = client.get(f"/api/v1/sessions/{session_id}/events")
    event_types = {event["event_type"] for event in events.json()}

    assert events.status_code == 200
    assert {"session_started", "session_stopped"}.issubset(event_types)

    db = SessionLocal()
    try:
        all_event_types = {row.event_type for row in db.query(SessionEvent).all()}
        assert {"account_login_requested", "account_online", "games_selected", "session_started", "session_stopped"}.issubset(all_event_types)
    finally:
        db.close()
