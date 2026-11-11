from tests.contract import schemas


def test_create_issue_contract(client, auth_headers, project, user, assert_matches):
    response = client.post(
        "/api/v1/projects/WEB/issues",
        json={"title": "Contract check", "assignee_id": user.id, "due_date": "2026-12-31"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert_matches(response.json, schemas.wrap("issue", schemas.ISSUE))


def test_unassigned_issue_contract(client, auth_headers, issue, assert_matches):
    response = client.get("/api/v1/issues/WEB-1", headers=auth_headers)
    assert_matches(response.json, schemas.wrap("issue", schemas.ISSUE))


def test_list_issues_contract(client, auth_headers, make_issue, assert_matches):
    make_issue(title="One")
    make_issue(title="Two")
    response = client.get("/api/v1/projects/WEB/issues", headers=auth_headers)
    assert_matches(response.json, schemas.wrap_list("issues", schemas.ISSUE))


def test_comment_contract(client, auth_headers, issue, assert_matches):
    created = client.post("/api/v1/issues/WEB-1/comments", json={"body": "Hi"}, headers=auth_headers)
    assert_matches(created.json, schemas.wrap("comment", schemas.COMMENT))

    listed = client.get("/api/v1/issues/WEB-1/comments", headers=auth_headers)
    assert_matches(listed.json, schemas.wrap_list("comments", schemas.COMMENT))


def test_issue_error_contract(client, auth_headers, project, assert_matches):
    response = client.get("/api/v1/issues/WEB-404", headers=auth_headers)
    assert response.status_code == 404
    assert_matches(response.json, schemas.ERROR)
