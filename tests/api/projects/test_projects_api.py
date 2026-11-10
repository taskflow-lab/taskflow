def test_create_and_get_project(client, auth_headers):
    created = client.post(
        "/api/v1/projects",
        json={"name": "Mobile App", "key": "mob", "description": "iOS and Android"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    assert created.json["project"]["key"] == "MOB"

    fetched = client.get("/api/v1/projects/MOB", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json["project"]["name"] == "Mobile App"


def test_list_projects_only_shows_mine(client, auth_headers, project, make_project, other_user):
    make_project(owner=other_user, name="Secret", key="SEC")

    response = client.get("/api/v1/projects", headers=auth_headers)

    assert response.status_code == 200
    assert [p["key"] for p in response.json["projects"]] == ["WEB"]


def test_create_project_validation_error(client, auth_headers):
    response = client.post("/api/v1/projects", json={"name": "Bad", "key": "1"}, headers=auth_headers)
    assert response.status_code == 400


def test_duplicate_key_returns_400(client, auth_headers, project):
    response = client.post("/api/v1/projects", json={"name": "Again", "key": "WEB"}, headers=auth_headers)
    assert response.status_code == 400
    assert "already taken" in response.json["error"]["message"]


def test_fourth_project_on_free_plan_returns_402(client, auth_headers, make_project):
    for _ in range(3):
        make_project()

    response = client.post("/api/v1/projects", json={"name": "Fourth", "key": "FOUR"}, headers=auth_headers)

    assert response.status_code == 402
    assert "Upgrade" in response.json["error"]["message"]


def test_unknown_project_returns_404(client, auth_headers):
    response = client.get("/api/v1/projects/NOPE", headers=auth_headers)
    assert response.status_code == 404


def test_other_users_project_returns_403(client, project, other_user, headers_for):
    response = client.get("/api/v1/projects/WEB", headers=headers_for(other_user))
    assert response.status_code == 403


def test_update_project(client, auth_headers, project):
    response = client.patch("/api/v1/projects/WEB", json={"name": "Website v2"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json["project"]["name"] == "Website v2"


def test_member_cannot_archive(client, user, other_user, project, headers_for):
    from app.modules.projects.services import add_member

    add_member(project, user, other_user.email)
    response = client.post("/api/v1/projects/WEB/archive", headers=headers_for(other_user))
    assert response.status_code == 403


def test_projects_require_auth(client):
    assert client.get("/api/v1/projects").status_code == 401
