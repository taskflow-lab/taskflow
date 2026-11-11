"""Billing + Projects working together, through the real web pages and API."""


def create_project_via_web(client, name, key):
    return client.post("/projects/new", data={"name": name, "key": key, "description": ""})


def test_free_plan_limit_redirects_to_billing_page(logged_in_client, make_project):
    for _ in range(3):
        make_project()

    response = create_project_via_web(logged_in_client, "Fourth", "FOUR")

    assert response.status_code == 302
    assert response.location.endswith("/billing/")
    page = logged_in_client.get(response.location).get_data(as_text=True)
    assert "allows 3 active projects" in page


def test_upgrade_unlocks_project_creation(logged_in_client, make_project):
    for _ in range(3):
        make_project()

    logged_in_client.post("/billing/change", data={"plan": "standard"})
    response = create_project_via_web(logged_in_client, "Fourth", "FOUR")

    assert response.status_code == 302
    assert response.location.endswith("/projects/FOUR")


def test_archiving_frees_a_slot(client, auth_headers, make_project):
    projects = [make_project() for _ in range(3)]

    client.post(f"/api/v1/projects/{projects[0].key}/archive", headers=auth_headers)
    response = client.post("/api/v1/projects", json={"name": "Fourth", "key": "FOUR"}, headers=auth_headers)

    assert response.status_code == 201


def test_usage_page_reflects_projects_created_via_api(client, auth_headers, logged_in_client):
    for key in ["AAA", "BBB"]:
        client.post("/api/v1/projects", json={"name": key, "key": key}, headers=auth_headers)

    usage = client.get("/api/v1/billing/usage", headers=auth_headers).json["usage"]
    page = logged_in_client.get("/billing/").get_data(as_text=True)

    assert usage["projects_used"] == 2
    assert "2 / 3" in " ".join(page.split())


def test_limits_are_per_user(client, make_project, other_user, headers_for):
    for _ in range(3):
        make_project()

    response = client.post(
        "/api/v1/projects", json={"name": "Bob's", "key": "BOB"}, headers=headers_for(other_user)
    )
    assert response.status_code == 201


def test_being_a_member_does_not_use_your_quota(client, user, other_user, make_project, headers_for):
    for i in range(3):
        make_project(owner=other_user, name=f"Bob {i}", key=f"BOB{i}", members=[user])

    response = client.post(
        "/api/v1/projects", json={"name": "Mine", "key": "MINE"}, headers=headers_for(user)
    )
    assert response.status_code == 201
