from datetime import date

import pytest

from app.modules.issues.services import change_status
from app.modules.projects.services import archive_project
from app.modules.sprints import services

TODAY = date(2026, 11, 11)


@pytest.fixture
def make_sprint(app, project):
    def _make_sprint(name=None, goal="", issues=(), target_project=None):
        sprint = services.create_sprint(target_project or project, name, goal)
        for issue in issues:
            services.add_issue(sprint, issue)
        return sprint

    return _make_sprint


@pytest.fixture
def started_sprint(make_sprint, make_issue):
    sprint = make_sprint(issues=[make_issue(title="First"), make_issue(title="Second")])
    return services.start_sprint(sprint, weeks=2, today=TODAY)


# ---------- create ----------

def test_create_sprint_defaults(app, project):
    sprint = services.create_sprint(project)

    assert sprint.name == "WEB Sprint 1"
    assert sprint.status == "planned"
    assert sprint.goal == ""
    assert sprint.issues == []


def test_default_names_count_up(app, project):
    services.create_sprint(project)
    assert services.create_sprint(project).name == "WEB Sprint 2"


def test_create_sprint_with_name_and_goal(app, project):
    sprint = services.create_sprint(project, "  Launch week ", "  Ship the board ")
    assert sprint.name == "Launch week"
    assert sprint.goal == "Ship the board"


def test_create_sprint_name_too_long(app, project):
    with pytest.raises(ValueError, match="100 characters"):
        services.create_sprint(project, "x" * 101)


def test_cannot_plan_sprint_in_archived_project(app, user, project):
    archive_project(project, user)
    with pytest.raises(ValueError, match="archived"):
        services.create_sprint(project)


# ---------- add / remove issues ----------

def test_add_issue(app, make_sprint, issue):
    sprint = make_sprint()
    services.add_issue(sprint, issue)
    assert sprint.issues == [issue]


def test_adding_twice_does_not_duplicate(app, make_sprint, issue):
    sprint = make_sprint(issues=[issue])
    services.add_issue(sprint, issue)
    assert sprint.issues == [issue]


def test_adding_to_another_sprint_moves_the_issue(app, make_sprint, issue):
    first = make_sprint(issues=[issue])
    second = make_sprint()

    services.add_issue(second, issue)

    assert first.issues == []
    assert second.issues == [issue]


def test_cannot_add_issue_from_another_project(app, make_sprint, make_issue, make_project):
    other_issue = make_issue(target_project=make_project(name="Mobile", key="MOB"))
    with pytest.raises(ValueError, match="different project"):
        services.add_issue(make_sprint(), other_issue)


def test_cannot_add_done_issue(app, user, make_sprint, issue):
    change_status(issue, "done", user)
    with pytest.raises(ValueError, match="already done"):
        services.add_issue(make_sprint(), issue)


def test_remove_issue_returns_it_to_backlog(app, project, make_sprint, issue):
    sprint = make_sprint(issues=[issue])
    services.remove_issue(sprint, issue)

    assert sprint.issues == []
    assert services.get_backlog(project) == [issue]


def test_remove_issue_not_in_sprint(app, make_sprint, issue):
    with pytest.raises(LookupError, match="is not in"):
        services.remove_issue(make_sprint(), issue)


# ---------- start ----------

def test_start_sprint_sets_dates(app, started_sprint):
    assert started_sprint.status == "active"
    assert started_sprint.start_date == TODAY
    assert started_sprint.end_date == date(2026, 11, 25)


@pytest.mark.parametrize("weeks, end", [(1, date(2026, 11, 18)), ("4", date(2026, 12, 9))])
def test_sprint_length(app, make_sprint, issue, weeks, end):
    sprint = services.start_sprint(make_sprint(issues=[issue]), weeks=weeks, today=TODAY)
    assert sprint.end_date == end


@pytest.mark.parametrize("weeks", [0, 5, "two", None])
def test_invalid_sprint_length(app, make_sprint, issue, weeks):
    with pytest.raises(ValueError, match="weeks"):
        services.start_sprint(make_sprint(issues=[issue]), weeks=weeks)


def test_cannot_start_empty_sprint(app, make_sprint):
    with pytest.raises(ValueError, match="at least one issue"):
        services.start_sprint(make_sprint())


def test_only_one_active_sprint_per_project(app, started_sprint, make_sprint, make_issue):
    next_sprint = make_sprint(issues=[make_issue(title="Later")])
    with pytest.raises(ValueError, match=f"Complete {started_sprint.name}"):
        services.start_sprint(next_sprint)


def test_active_sprints_in_different_projects_are_fine(app, started_sprint, make_sprint, make_issue, make_project):
    mobile = make_project(name="Mobile", key="MOB")
    other = make_sprint(target_project=mobile, issues=[make_issue(target_project=mobile)])

    assert services.start_sprint(other).status == "active"


def test_cannot_start_active_sprint_again(app, started_sprint):
    with pytest.raises(ValueError, match="Only a planned sprint"):
        services.start_sprint(started_sprint)


@pytest.mark.parametrize("today, left", [(TODAY, 14), (date(2026, 11, 24), 1), (date(2026, 12, 1), 0)])
def test_days_left(app, started_sprint, today, left):
    assert services.days_left(started_sprint, today=today) == left


def test_days_left_for_planned_sprint_is_none(app, make_sprint):
    assert services.days_left(make_sprint()) is None


# ---------- complete ----------

def test_complete_sprint_counts_and_returns_unfinished_to_backlog(app, user, project, started_sprint):
    first, second = started_sprint.issues
    change_status(first, "done", user)

    result = services.complete_sprint(started_sprint)

    assert result == {"done": 1, "unfinished": 1}
    assert started_sprint.status == "completed"
    assert started_sprint.completed_at is not None
    assert services.get_backlog(project) == [second]


def test_completed_sprint_keeps_its_history(app, started_sprint):
    issues = list(started_sprint.issues)
    services.complete_sprint(started_sprint)
    assert started_sprint.issues == issues


def test_cannot_complete_planned_sprint(app, make_sprint):
    with pytest.raises(ValueError, match="Only the active sprint"):
        services.complete_sprint(make_sprint())


def test_completed_sprint_cannot_be_changed(app, started_sprint, make_issue):
    services.complete_sprint(started_sprint)

    with pytest.raises(ValueError, match="completed sprint cannot be changed"):
        services.add_issue(started_sprint, make_issue(title="Too late"))
    with pytest.raises(ValueError, match="completed sprint cannot be changed"):
        services.remove_issue(started_sprint, started_sprint.issues[0])


def test_after_completing_a_new_sprint_can_start(app, started_sprint, make_sprint, make_issue):
    services.complete_sprint(started_sprint)
    next_sprint = make_sprint(issues=[make_issue(title="Next")])

    assert services.start_sprint(next_sprint).status == "active"


# ---------- backlog & lookups ----------

def test_backlog_excludes_done_and_planned_issues(app, user, project, make_sprint, make_issue):
    in_sprint = make_issue(title="Planned")
    done = make_issue(title="Finished")
    waiting = make_issue(title="Waiting")
    make_sprint(issues=[in_sprint])
    change_status(done, "done", user)

    assert services.get_backlog(project) == [waiting]


def test_list_open_sprints_puts_active_first(app, make_sprint, started_sprint):
    planned = make_sprint(name="Later")
    assert services.list_open_sprints(started_sprint.project) == [started_sprint, planned]


def test_list_open_sprints_hides_completed(app, started_sprint):
    services.complete_sprint(started_sprint)
    assert services.list_open_sprints(started_sprint.project) == []


def test_get_sprint_unknown(app):
    with pytest.raises(LookupError):
        services.get_sprint(999)
