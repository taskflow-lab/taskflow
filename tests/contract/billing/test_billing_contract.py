from tests.contract import schemas


def test_plans_contract(client, assert_matches):
    assert_matches(client.get("/api/v1/billing/plans").json, schemas.wrap_list("plans", schemas.PLAN))


def test_subscription_contract(client, auth_headers, assert_matches):
    response = client.get("/api/v1/billing/subscription", headers=auth_headers)
    assert_matches(response.json, schemas.wrap("subscription", schemas.SUBSCRIPTION))


def test_upgrade_contract(client, auth_headers, assert_matches):
    response = client.post("/api/v1/billing/subscription", json={"plan": "standard"}, headers=auth_headers)
    assert_matches(response.json["subscription"], schemas.SUBSCRIPTION)
    assert_matches(response.json["payment"], schemas.PAYMENT)


def test_usage_contract(client, auth_headers, assert_matches):
    response = client.get("/api/v1/billing/usage", headers=auth_headers)
    assert_matches(response.json, schemas.wrap("usage", schemas.USAGE))


def test_plan_limit_error_contract(client, auth_headers, make_project, assert_matches):
    for _ in range(3):
        make_project()
    response = client.post("/api/v1/projects", json={"name": "Four", "key": "FOUR"}, headers=auth_headers)
    assert response.status_code == 402
    assert_matches(response.json, schemas.ERROR)
