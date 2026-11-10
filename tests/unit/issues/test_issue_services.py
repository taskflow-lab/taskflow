from datetime import date

import pytest

from app.modules.issues import services
from app.modules.notifications.models import Notification
from app.modules.projects.services import add_member, archive_project


# ---------- create_issue ----------

def test_create_issue_defaults(app, user, project):
    issue = services.create_issue(project, user, "  Fix header  ")

    assert issue.key == "WEB-1"
    assert issue.title == "Fix header"
    assert issue.status == "todo"
    assert issue.issue_type == "task"
    assert issue.priority == "medium"
    assert issue.reporter == user
    assert issue.assignee is None


def test_issue_numbers_increase_per_project(app, make_issue, make_project, user):
    other = make_project(name="Mobile", key="MOB")

    assert make_issue().key == "WEB-1"
    assert make_issue().key == "WEB-2"
    assert make_issue(target_project=other).key == "MOB-1"


@pytest.mark.parametrize(
    "fields, message",
    [
        ({"title": ""}, "Title is required"),
        ({"title": "x" * 201}, "200 characters"),
        ({"issue_type": "epic"}, "Type must be one of"),
        ({"priority": "urgent"}, "Priority must be one of"),
        ({"due_date": "31/12/2026"}, "YYYY-MM-DD"),
        ({"assignee_id": "abc"}, "user id"),
    ],
)
def test_create_issue_rejects_invalid_input(app, user, project, fields, message):
    data = {"title": "Valid title", **fields}
    with pytest.raises(ValueError, match=message):
        services.create_issue(project, user, **data)


def test_create_issue_parses_due_date(app, make_issue):
    issue = make_issue(due_date="2026-12-31")
    assert issue.due_date == date(2026, 12, 31)


def test_assignee_must_be_project_member(app, make_issue, other_user):
    with pytest.raises(ValueError, match="member of the project"):
        make_issue(assignee_id=other_user.id)


def test_cannot_create_issue_in_archived_project(app, user, project, make_issue):
    archive_project(project, user)
    with pytest.raises(ValueError, match="archived project"):
        make_issue()


# ---------- notifications ----------

def test_assigning_someone_else_notifies_them(app, user, other_user, project, make_issue):
    add_member(project, user, other_user.email)
    issue = make_issue(assignee_id=other_user.id)

    notification = Notification.query.filter_by(user_id=other_user.id).one()
    assert issue.key in notification.message
    assert notification.link == f"/issues/{issue.key}"


def test_assigning_yourself_sends_no_notification(app, user, make_issue):
    make_issue(assignee_id=user.id)
    assert Notification.query.count() == 0


def test_status_change_notifies_reporter_but_not_actor(app, user, other_user, project, make_issue):
    add_member(project, user, other_user.email)
    issue = make_issue()

    services.change_status(issue, "in_progress", other_user)

    assert Notification.query.filter_by(user_id=user.id).count() == 1
    assert Notification.query.filter_by(user_id=other_user.id).count() == 0


def test_comment_notifies_reporter(app, user, other_user, project, make_issue):
    add_member(project, user, other_user.email)
    issue = make_issue()

    services.add_comment(issue, other_user, "Looks good")

    assert "commented on WEB-1" in Notification.query.filter_by(user_id=user.id).one().message


# ---------- status ----------

def test_change_status(app, issue, user):
    services.change_status(issue, "done", user)
    assert issue.status == "done"
    assert issue.status_label == "Done"


def test_change_status_rejects_unknown_status(app, issue, user):
    with pytest.raises(ValueError, match="Status must be one of"):
        services.change_status(issue, "closed", user)


def test_change_to_same_status_does_nothing(app, issue, user, other_user, project):
    add_member(project, user, other_user.email)
    services.change_status(issue, "todo", other_user)
    assert Notification.query.count() == 0


# ---------- update ----------

def test_update_issue_fields(app, issue, user):
    services.update_issue(issue, user, title="New title", priority="lowest", type="story", due_date="2027-01-15")

    assert issue.title == "New title"
    assert issue.priority == "lowest"
    assert issue.issue_type == "story"
    assert issue.due_date == date(2027, 1, 15)


def test_update_issue_can_unassign(app, user, make_issue):
    issue = make_issue(assignee_id=user.id)
    services.update_issue(issue, user, assignee_id=None)
    assert issue.assignee_id is None


# ---------- comments ----------

def test_add_comment(app, issue, user):
    comment = services.add_comment(issue, user, "  On it  ")
    assert comment.body == "On it"
    assert issue.comments == [comment]


@pytest.mark.parametrize("body", ["", "   ", None])
def test_empty_comment_rejected(app, issue, user, body):
    with pytest.raises(ValueError, match="cannot be empty"):
        services.add_comment(issue, user, body)


# ---------- lookup & listing ----------

@pytest.mark.parametrize("key", ["WEB-1", "web-1", " WEB-1 "])
def test_get_issue_by_key(app, issue, key):
    assert services.get_issue_by_key(key) == issue


@pytest.mark.parametrize("key", ["WEB-99", "NOPE-1", "WEB", "garbage", ""])
def test_get_issue_by_key_not_found(app, issue, key):
    with pytest.raises(LookupError):
        services.get_issue_by_key(key)


def test_list_issues_filters(app, user, make_issue):
    bug = make_issue(title="Bug", priority="high", assignee_id=user.id)
    make_issue(title="Task", priority="low")
    services.change_status(bug, "in_progress", user)

    assert services.list_issues(bug.project, status="in_progress") == [bug]
    assert services.list_issues(bug.project, priority="high") == [bug]
    assert services.list_issues(bug.project, assignee_id=user.id) == [bug]
    assert len(services.list_issues(bug.project)) == 2


def test_list_issues_rejects_bad_filter(app, project):
    with pytest.raises(ValueError):
        services.list_issues(project, status="closed")


def test_count_by_status_includes_empty_columns(app, user, make_issue):
    issue = make_issue()
    make_issue()
    services.change_status(issue, "done", user)

    assert services.count_by_status(issue.project) == [
        ("todo", "To Do", 1),
        ("in_progress", "In Progress", 0),
        ("in_review", "In Review", 0),
        ("done", "Done", 1),
    ]


def test_to_dict_shape(app, issue):
    data = issue.to_dict()
    assert data["key"] == "WEB-1"
    assert data["type"] == "bug"
    assert data["assignee"] is None
    assert data["comment_count"] == 0
