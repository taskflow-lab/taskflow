from tests.contract import schemas


def test_register_contract(client, assert_matches):
    response = client.post(
        "/api/v1/auth/register", json={"email": "c@test.com", "name": "C", "password": "password123"}
    )
    assert response.status_code == 201
    assert_matches(response.json, schemas.AUTH_RESPONSE)


def test_token_contract(client, user, assert_matches):
    response = client.post("/api/v1/auth/token", json={"email": user.email, "password": "password123"})
    assert_matches(response.json, schemas.AUTH_RESPONSE)


def test_me_contract(client, auth_headers, assert_matches):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert_matches(response.json, schemas.wrap("user", schemas.USER))
