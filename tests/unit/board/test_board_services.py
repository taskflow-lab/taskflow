from app.modules.board import services
from app.modules.issues.services import change_status
from app.modules.projects.services import add_member


def column(board, status):
    return next(col for col in board if col["status"] == status)


def keys(col):
    return [issue.key for issue in col["issues"]]


def test_board_has_four_columns_in_order(app, project):
    board = services.get_board(project)

    assert [col["status"] for col in board] == ["todo", "in_progress", "in_review", "done"]
    assert [col["label"] for col in board] == ["To Do", "In Progress", "In Review", "Done"]


def test_empty_project_has_empty_columns(app, project):
    assert all(col["issues"] == [] for col in services.get_board(project))


def test_issues_go_in_the_right_column(app, user, project, make_issue):
    first = make_issue(title="First")
    second = make_issue(title="Second")
    change_status(second, "in_review", user)

    board = services.get_board(project)

    assert keys(column(board, "todo")) == [first.key]
    assert keys(column(board, "in_review")) == [second.key]


def test_cards_sorted_by_issue_number(app, project, make_issue):
    for title in ["A", "B", "C"]:
        make_issue(title=title)

    assert keys(column(services.get_board(project), "todo")) == ["WEB-1", "WEB-2", "WEB-3"]


def test_search_filters_by_title_or_key(app, project, make_issue):
    make_issue(title="Fix login")
    make_issue(title="Write docs")

    assert keys(column(services.get_board(project, search="LOGIN"), "todo")) == ["WEB-1"]
    assert keys(column(services.get_board(project, search="web-2"), "todo")) == ["WEB-2"]


def test_assignee_filter(app, user, other_user, project, make_issue):
    add_member(project, user, other_user.email)
    make_issue(title="Mine", assignee_id=user.id)
    make_issue(title="Bob's", assignee_id=other_user.id)

    board = services.get_board(project, assignee_id=other_user.id)
    assert keys(column(board, "todo")) == ["WEB-2"]


def test_board_only_shows_this_projects_issues(app, project, make_project, make_issue):
    other = make_project(name="Mobile", key="MOB")
    make_issue(title="Web issue")
    make_issue(title="Mobile issue", target_project=other)

    assert keys(column(services.get_board(project), "todo")) == ["WEB-1"]
