import pytest

from app import create_app, db


@pytest.fixture()
def client():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test",
        }
    )
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()


def register(client, username="jone", password="supersecret"):
    return client.post(
        "/register", data={"username": username, "password": password}, follow_redirects=True
    )


def login(client, username="jone", password="supersecret"):
    return client.post(
        "/login", data={"username": username, "password": password}, follow_redirects=True
    )


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["database"] == "up"


def test_dashboard_requires_login(client):
    res = client.get("/")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_register_and_login(client):
    assert b"Account created" in register(client).data
    res = login(client)
    assert b"Welcome, jone" in res.data


def test_wrong_password_rejected(client):
    register(client)
    res = login(client, password="wrongpass")
    assert b"Invalid username or password" in res.data


def test_duplicate_username_rejected(client):
    register(client)
    res = register(client)
    assert b"already taken" in res.data


def test_short_password_rejected(client):
    res = register(client, password="short")
    assert b"8+ characters" in res.data


def test_logout(client):
    register(client)
    login(client)
    res = client.get("/logout", follow_redirects=True)
    assert b"logged out" in res.data
    assert client.get("/").status_code == 302
