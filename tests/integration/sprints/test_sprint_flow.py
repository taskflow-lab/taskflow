"""A full sprint through the web pages: plan -> start -> work on the board -> complete."""
import pytest

from app.extensions import db
from app.modules.sprints.models import Sprint


@pytest.fixture
def three_issues(make_issue):
    return [make_issue(title=title) for title in ["Login page", "Signup page", "Docs"]]


def page(client, url):
    return client.get(url).get_data(as_text=True)


def plan_sprint(client, issue_keys, name="Sprint A", goal="Ship auth"):
    client.post("/projects/WEB/sprints", data={"name": name, "goal": goal})
    sprint = Sprint.query.filter_by(name=name).one()
    for key in issue_keys:
        client.post("/projects/WEB/backlog/add", data={"sprint_id": sprint.id, "issue_key": key})
    return sprint


def test_full_sprint_cycle(logged_in_client, three_issues):
    client = logged_in_client
    sprint = plan_sprint(client, ["WEB-1", "WEB-2"])

    response = client.post(f"/sprints/{sprint.id}/start", data={"weeks": "1"})
    assert response.status_code == 302
    assert response.location.endswith("/projects/WEB/board")

    board = page(client, "/projects/WEB/board")
    assert "Sprint A" in board and "Goal: Ship auth" in board
    assert 'data-issue-key="WEB-1"' in board and 'data-issue-key="WEB-2"' in board
    assert 'data-issue-key="WEB-3"' not in board  # still in the backlog

    client.post("/api/v1/issues/WEB-1/transition", json={"status": "done"})
    client.post(f"/sprints/{sprint.id}/complete")

    backlog = page(client, "/projects/WEB/backlog")
    assert "Sprint A completed: 1 done, 1 moved back to the backlog." in backlog
    assert 'data-testid="backlog-issue-WEB-2"' in backlog
    assert 'data-testid="backlog-issue-WEB-3"' in backlog
    assert 'data-testid="backlog-issue-WEB-1"' not in backlog

    assert "No active sprint" in page(client, "/projects/WEB/board")


def test_board_without_sprint_shows_everything(logged_in_client, three_issues):
    board = page(logged_in_client, "/projects/WEB/board")
    assert "No active sprint" in board
    assert all(f'data-issue-key="WEB-{n}"' in board for n in (1, 2, 3))


def test_errors_are_shown_not_crashing(logged_in_client, three_issues):
    client = logged_in_client
    sprint = plan_sprint(client, [])

    response = client.post(f"/sprints/{sprint.id}/start", data={"weeks": "2"}, follow_redirects=True)

    assert response.status_code == 200
    assert "Add at least one issue" in response.get_data(as_text=True)
    assert db.session.get(Sprint, sprint.id).status == "planned"


def test_remove_from_sprint_via_web(logged_in_client, three_issues):
    sprint = plan_sprint(logged_in_client, ["WEB-1"])

    logged_in_client.post(f"/sprints/{sprint.id}/issues/WEB-1/remove")

    assert 'data-testid="backlog-issue-WEB-1"' in page(logged_in_client, "/projects/WEB/backlog")


def test_outsider_cannot_see_or_change_sprints(app, logged_in_client, three_issues, other_user):
    from tests.conftest import login_client

    sprint = plan_sprint(logged_in_client, ["WEB-1"])
    outsider = login_client(app.test_client(), other_user)

    assert outsider.get("/projects/WEB/backlog").status_code == 403
    assert outsider.post(f"/sprints/{sprint.id}/start", data={"weeks": "2"}).status_code == 403
    assert outsider.post(f"/sprints/{sprint.id}/complete").status_code == 403
    assert outsider.post(f"/sprints/{sprint.id}/issues/WEB-1/remove").status_code == 403


def test_unknown_sprint_is_404(logged_in_client, project):
    assert logged_in_client.post("/sprints/999/start").status_code == 404


def test_cannot_add_issue_to_sprint_of_another_project(logged_in_client, three_issues, make_project):
    make_project(name="Mobile", key="MOB")
    logged_in_client.post("/projects/MOB/sprints", data={"name": "Mobile sprint"})
    mobile_sprint = Sprint.query.filter_by(name="Mobile sprint").one()

    response = logged_in_client.post(
        "/projects/WEB/backlog/add", data={"sprint_id": mobile_sprint.id, "issue_key": "WEB-1"}
    )

    assert response.status_code == 404
    assert mobile_sprint.issues == []
