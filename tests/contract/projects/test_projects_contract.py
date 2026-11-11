from tests.contract import schemas


def test_create_project_contract(client, auth_headers, assert_matches):
    response = client.post("/api/v1/projects", json={"name": "Mobile", "key": "MOB"}, headers=auth_headers)
    assert response.status_code == 201
    assert_matches(response.json, schemas.wrap("project", schemas.PROJECT))


def test_list_projects_contract(client, auth_headers, project, assert_matches):
    response = client.get("/api/v1/projects", headers=auth_headers)
    assert_matches(response.json, schemas.wrap_list("projects", schemas.PROJECT))


def test_project_errors_contract(client, auth_headers, other_user, project, headers_for, assert_matches):
    for response in [
        client.get("/api/v1/projects/NOPE", headers=auth_headers),                    # 404
        client.get("/api/v1/projects/WEB", headers=headers_for(other_user)),          # 403
        client.post("/api/v1/projects", json={"key": "1"}, headers=auth_headers),     # 400
        client.get("/api/v1/projects"),                                               # 401
    ]:
        assert_matches(response.json, schemas.ERROR)
