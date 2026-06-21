from .conftest import csrf, register


def test_cancel_trial_keeps_access_until_period_end(client):
    register(client)
    headers = {"X-CSRF-Token": csrf(client)}

    sub = client.get("/api/v1/billing/subscription").json()
    assert sub["active"] is True
    assert sub["cancel_at_period_end"] is False

    cancel = client.post("/api/v1/billing/cancel", json={}, headers=headers)
    assert cancel.status_code == 200
    body = cancel.json()
    # Trial has an expiry, so access rides out the period.
    assert body["active"] is True
    assert body["cancel_at_period_end"] is True
    assert body["canceled_at"] is not None

    reactivate = client.post("/api/v1/billing/reactivate", json={}, headers=headers)
    assert reactivate.status_code == 200
    assert reactivate.json()["cancel_at_period_end"] is False


def test_cancel_requires_csrf(client):
    register(client)
    resp = client.post("/api/v1/billing/cancel", json={})
    assert resp.status_code == 403
