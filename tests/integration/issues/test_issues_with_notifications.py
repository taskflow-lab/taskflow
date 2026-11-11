"""Issues + Notifications + Board + Search working together."""
import pytest

from app.modules.notifications.models import Notification
from app.modules.projects.services import add_member
from tests.conftest import login_client


@pytest.fixture
def team(app, user, other_user, project):
    """Alice owns WEB, Bob is a member. Returns a logged-in web client for each."""
    add_member(project, user, other_user.email)
    alice = login_client(app.test_client(), user)
    bob = login_client(app.test_client(), other_user)
    return alice, bob


def unread_badge(client):
    html = client.get("/projects/").get_data(as_text=True)
    marker = 'data-testid="nav-unread-count">'
    if marker not in html:
        return 0
    return int(html.split(marker)[1].split("<")[0])


def test_assigning_an_issue_shows_in_assignees_bell(team, other_user):
    alice, bob = team
    alice.post(
        "/projects/WEB/issues/new",
        data={"title": "Fix header", "issue_type": "bug", "priority": "high", "assignee_id": other_user.id},
    )

    assert unread_badge(bob) == 1
    assert unread_badge(alice) == 0
    assert "assigned you WEB-1" in bob.get("/notifications/").get_data(as_text=True)


def test_status_change_by_assignee_notifies_reporter(team, auth_headers, headers_for, other_user, client):
    alice, _ = team
    client.post("/api/v1/projects/WEB/issues", json={"title": "Login bug"}, headers=auth_headers)

    client.post("/api/v1/issues/WEB-1/transition", json={"status": "in_review"}, headers=headers_for(other_user))

    assert unread_badge(alice) == 1
    assert "moved WEB-1 to In Review" in alice.get("/notifications/").get_data(as_text=True)


def test_opening_notification_marks_read_and_goes_to_issue(team, other_user):
    alice, bob = team
    alice.post(
        "/projects/WEB/issues/new",
        data={"title": "Fix header", "issue_type": "task", "priority": "medium", "assignee_id": other_user.id},
    )
    notification = Notification.query.filter_by(user_id=other_user.id).one()

    response = bob.post(f"/notifications/{notification.id}/open")

    assert response.status_code == 302
    assert response.location.endswith("/issues/WEB-1")
    assert unread_badge(bob) == 0


def test_board_drag_and_drop_flow(team, client, auth_headers):
    """What board.js does when a card is dropped: call the transition API, then the board re-renders."""
    alice, _ = team
    client.post("/api/v1/projects/WEB/issues", json={"title": "Move me"}, headers=auth_headers)

    alice.post("/api/v1/issues/WEB-1/transition", json={"status": "done"})
    board = alice.get("/projects/WEB/board").get_data(as_text=True)

    done_column = board.split('data-testid="column-done"')[1].split("</section>")[0]
    assert 'data-issue-key="WEB-1"' in done_column


def test_new_issue_is_immediately_searchable(team, client, auth_headers):
    alice, bob = team
    client.post("/api/v1/projects/WEB/issues", json={"title": "Payment page timeout"}, headers=auth_headers)

    assert "WEB-1" in bob.get("/search/?q=timeout").get_data(as_text=True)


def test_removed_member_loses_access_everywhere(team, user, other_user, project, headers_for, client):
    from app.modules.projects.services import remove_member

    remove_member(project, user, other_user.id)
    _, bob = team

    assert bob.get("/projects/WEB").status_code == 403
    assert bob.get("/projects/WEB/board").status_code == 403
    assert client.get("/api/v1/projects/WEB", headers=headers_for(other_user)).status_code == 403
