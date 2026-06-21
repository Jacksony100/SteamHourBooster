from .conftest import login, make_admin, register


def test_admin_guard_redirects_regular_user(client):
    register(client)
    login(client)

    response = client.get("/admin", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_admin_guard_allows_admin(app, client):
    register(client)
    make_admin(app)
    login(client)

    response = client.get("/admin")

    assert response.status_code == 200
    assert "Админ-панель".encode("utf-8") in response.data
