import pytest


def test_create_issue(client, auth_headers, project, user):
    response = client.post(
        "/api/v1/projects/WEB/issues",
        json={"title": "Login crash", "type": "bug", "priority": "highest", "assignee_id": user.id},
        headers=auth_headers,
    )

    assert response.status_code == 201
    issue = response.json["issue"]
    assert issue["key"] == "WEB-1"
    assert issue["status"] == "todo"
    assert issue["assignee"]["id"] == user.id


@pytest.mark.parametrize(
    "payload",
    [{"title": ""}, {"title": "x", "type": "epic"}, {"title": "x", "priority": "urgent"}],
)
def test_create_issue_invalid_returns_400(client, auth_headers, project, payload):
    response = client.post("/api/v1/projects/WEB/issues", json=payload, headers=auth_headers)
    assert response.status_code == 400


def test_get_issue(client, auth_headers, issue):
    response = client.get("/api/v1/issues/WEB-1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["issue"]["title"] == "Fix login button"


def test_unknown_issue_returns_404(client, auth_headers, project):
    assert client.get("/api/v1/issues/WEB-99", headers=auth_headers).status_code == 404


def test_outsider_cannot_read_issue(client, issue, other_user, headers_for):
    assert client.get("/api/v1/issues/WEB-1", headers=headers_for(other_user)).status_code == 403


def test_list_issues_with_status_filter(client, auth_headers, make_issue, user):
    from app.modules.issues.services import change_status

    first = make_issue(title="First")
    make_issue(title="Second")
    change_status(first, "done", user)

    response = client.get("/api/v1/projects/WEB/issues?status=done", headers=auth_headers)

    assert response.status_code == 200
    assert [i["key"] for i in response.json["issues"]] == ["WEB-1"]


def test_transition_issue(client, auth_headers, issue):
    response = client.post("/api/v1/issues/WEB-1/transition", json={"status": "in_review"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json["issue"]["status"] == "in_review"


def test_transition_to_invalid_status(client, auth_headers, issue):
    response = client.post("/api/v1/issues/WEB-1/transition", json={"status": "closed"}, headers=auth_headers)
    assert response.status_code == 400


def test_patch_ignores_unknown_fields(client, auth_headers, issue):
    response = client.patch(
        "/api/v1/issues/WEB-1",
        json={"priority": "low", "status": "done", "reporter_id": 999},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json["issue"]["priority"] == "low"
    assert response.json["issue"]["status"] == "todo"


def test_add_and_list_comments(client, auth_headers, issue):
    created = client.post("/api/v1/issues/WEB-1/comments", json={"body": "On it"}, headers=auth_headers)
    assert created.status_code == 201

    listed = client.get("/api/v1/issues/WEB-1/comments", headers=auth_headers)
    assert [c["body"] for c in listed.json["comments"]] == ["On it"]


def test_empty_comment_returns_400(client, auth_headers, issue):
    response = client.post("/api/v1/issues/WEB-1/comments", json={"body": "  "}, headers=auth_headers)
    assert response.status_code == 400
