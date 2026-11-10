import pytest


def test_register_returns_user_and_token(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "jane@test.com", "name": "Jane", "password": "password123"},
    )

    assert response.status_code == 201
    body = response.json
    assert body["user"]["email"] == "jane@test.com"
    assert body["token"]
    assert "password_hash" not in body["user"]


def test_register_duplicate_email_returns_400(client, user):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": user.email, "name": "Copy", "password": "password123"},
    )
    assert response.status_code == 400
    assert "already exists" in response.json["error"]["message"]


def test_login_returns_token_that_works(client, user):
    response = client.post("/api/v1/auth/token", json={"email": "alice@test.com", "password": "password123"})
    assert response.status_code == 200

    token = response.json["token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json["user"]["email"] == "alice@test.com"


def test_login_wrong_password_returns_401(client, user):
    response = client.post("/api/v1/auth/token", json={"email": "alice@test.com", "password": "nope"})
    assert response.status_code == 401
    assert response.json["error"]["message"] == "Invalid email or password"


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer not-a-real-token"}, {"Authorization": "Token abc"}],
)
def test_me_requires_valid_token(client, headers):
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json["error"]["message"] == "Authentication required"


@pytest.mark.parametrize("body", ["not json", "[1, 2]"])
def test_non_object_body_returns_400(client, body):
    response = client.post("/api/v1/auth/token", data=body, content_type="application/json")
    assert response.status_code == 400
    assert "JSON object" in response.json["error"]["message"]
