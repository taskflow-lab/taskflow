def test_plans_are_public(client):
    response = client.get("/api/v1/billing/plans")

    assert response.status_code == 200
    assert [p["code"] for p in response.json["plans"]] == ["free", "standard", "premium"]


def test_new_user_subscription_is_free(client, auth_headers):
    response = client.get("/api/v1/billing/subscription", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["subscription"]["plan"] == "free"


def test_upgrade_returns_mock_payment(client, auth_headers):
    response = client.post("/api/v1/billing/subscription", json={"plan": "premium"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json["subscription"]["plan"] == "premium"
    assert response.json["payment"]["amount"] == 15
    assert response.json["payment"]["mock"] is True


def test_unknown_plan_returns_400(client, auth_headers):
    response = client.post("/api/v1/billing/subscription", json={"plan": "gold"}, headers=auth_headers)
    assert response.status_code == 400


def test_downgrade_blocked_when_over_limit(client, auth_headers, user, set_plan, make_project):
    set_plan(user, "standard")
    for _ in range(4):
        make_project()

    response = client.post("/api/v1/billing/subscription", json={"plan": "free"}, headers=auth_headers)

    assert response.status_code == 402
    assert "Archive some projects" in response.json["error"]["message"]


def test_usage_counts_projects(client, auth_headers, project):
    response = client.get("/api/v1/billing/usage", headers=auth_headers)
    assert response.json["usage"]["projects_used"] == 1
    assert response.json["usage"]["projects_remaining"] == 2


def test_subscription_requires_auth(client):
    assert client.get("/api/v1/billing/subscription").status_code == 401
