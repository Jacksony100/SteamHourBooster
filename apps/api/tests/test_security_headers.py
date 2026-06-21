from .conftest import csrf, register


def test_security_headers_present_on_responses(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert "Content-Security-Policy" in resp.headers
    assert "Permissions-Policy" in resp.headers


def test_request_id_header_is_emitted(client):
    resp = client.get("/health")
    assert resp.headers.get("X-Request-ID")


def test_request_id_is_echoed_when_supplied(client):
    resp = client.get("/health", headers={"X-Request-ID": "test-correlation-id"})
    assert resp.headers.get("X-Request-ID") == "test-correlation-id"


def test_csrf_still_enforced_on_mutations(client):
    register(client)
    # Missing CSRF header on a state-changing request must be rejected.
    resp = client.post(
        "/api/v1/steam-accounts",
        json={"label": "X", "display_name": "demo", "ownership_attested": True},
    )
    assert resp.status_code == 403

    ok = client.post(
        "/api/v1/steam-accounts",
        json={"label": "X", "display_name": "demo", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )
    assert ok.status_code == 200
