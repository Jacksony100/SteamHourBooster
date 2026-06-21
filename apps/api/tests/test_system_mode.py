def test_system_mode_is_honest_about_demo_runtime(client):
    response = client.get("/api/v1/system/mode")

    assert response.status_code == 200
    payload = response.json()
    assert payload["environment"] == "test"
    assert payload["steam_test_mode"] is True
    assert payload["steam_integration_mode"] == "demo"
    assert payload["real_steam_enabled"] is False
    assert payload["official_steam_configured"] is False
    assert payload["password_login_allowed"] is True
    assert payload["demo_mode"] is True
