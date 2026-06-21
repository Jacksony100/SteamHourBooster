from types import SimpleNamespace

import app.steam_accounts.service as account_service
from app.sessions.manager import _real_sessions_enabled
from app.sessions.runtime import MemoryRuntimeStore

from .conftest import csrf, register


def _real_settings(**over):
    base = dict(
        environment="development",
        steam_integration_mode="official",
        steam_official_linking_enabled=True,
        steam_real_sessions_enabled=True,
        steam_api_key="",
    )
    base.update(over)
    return SimpleNamespace(**base)


def test_real_sessions_enabled_truth_table():
    assert _real_sessions_enabled(_real_settings()) is True
    assert _real_sessions_enabled(_real_settings(steam_real_sessions_enabled=False)) is False
    assert _real_sessions_enabled(_real_settings(steam_official_linking_enabled=False)) is False
    assert _real_sessions_enabled(_real_settings(steam_integration_mode="demo")) is False


def test_create_account_real_mode_requires_credentials(client, monkeypatch):
    monkeypatch.setattr(account_service, "get_settings", lambda: _real_settings())
    register(client)
    headers = {"X-CSRF-Token": csrf(client)}

    missing = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Real", "username": "loginname", "ownership_attested": True},
        headers=headers,
    )
    assert missing.status_code == 400
    assert "require the account login and password" in missing.json()["detail"]

    ok = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Real", "username": "loginname", "password": "supersecret", "ownership_attested": True},
        headers=headers,
    )
    assert ok.status_code == 200
    # Raw credentials must never appear in the response.
    assert "supersecret" not in ok.text


def test_runtime_stop_flag_roundtrip():
    store = MemoryRuntimeStore()
    assert store.is_stop_requested(99) is False
    store.request_stop(99)
    assert store.is_stop_requested(99) is True
    store.clear_stop(99)
    assert store.is_stop_requested(99) is False


def test_runtime_acquire_is_exclusive_per_account():
    store = MemoryRuntimeStore()
    assert store.acquire(5) is True
    assert store.acquire(5) is False  # already held — second worker is blocked
    store.release(5)
    assert store.acquire(5) is True


def test_system_mode_reports_real_steam_enabled(client, monkeypatch):
    import app.system.routes as system_routes

    monkeypatch.setattr(system_routes, "get_settings", lambda: _real_settings(steam_test_mode=False, billing_provider="mock"))
    resp = client.get("/api/v1/system/mode")
    assert resp.status_code == 200
    body = resp.json()
    assert body["real_steam_enabled"] is True
    assert body["demo_mode"] is False
