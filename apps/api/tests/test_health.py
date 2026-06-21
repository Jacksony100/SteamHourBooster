def test_health_and_readiness(client):
    live = client.get("/healthz")
    ready = client.get("/readyz")

    assert live.status_code == 200
    assert live.json()["status"] == "live"
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert ready.json()["checks"]["database"] is True
