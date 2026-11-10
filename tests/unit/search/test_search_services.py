import pytest

from app.modules.issues.services import change_status
from app.modules.search import services


@pytest.fixture
def issues(app, user, make_issue, make_project):
    mobile = make_project(name="Mobile", key="MOB")
    return {
        "login": make_issue(title="Login button broken", description="Safari only", priority="high"),
        "export": make_issue(title="Export to CSV", priority="low"),
        "crash": make_issue(title="App crash on start", target_project=mobile, priority="high"),
    }


def keys(results):
    return sorted(issue.key for issue in results)


def test_search_by_title(app, user, issues):
    assert keys(services.search_issues(user, "login")) == ["WEB-1"]


def test_search_is_case_insensitive(app, user, issues):
    assert keys(services.search_issues(user, "EXPORT")) == ["WEB-2"]


def test_search_matches_description(app, user, issues):
    assert keys(services.search_issues(user, "safari")) == ["WEB-1"]


@pytest.mark.parametrize("query", ["WEB-2", "web-2", " WEB-2 "])
def test_search_by_issue_key(app, user, issues, query):
    assert keys(services.search_issues(user, query)) == ["WEB-2"]


def test_search_across_projects(app, user, issues):
    assert keys(services.search_issues(user, priority="high")) == ["MOB-1", "WEB-1"]


def test_filter_by_project(app, user, issues):
    assert keys(services.search_issues(user, project_key="mob")) == ["MOB-1"]


def test_filter_by_status(app, user, issues):
    change_status(issues["export"], "done", user)
    assert keys(services.search_issues(user, status="done")) == ["WEB-2"]


def test_filters_combine(app, user, issues):
    assert keys(services.search_issues(user, "crash", priority="high", project_key="WEB")) == []


def test_no_match_returns_empty(app, user, issues):
    assert services.search_issues(user, "nothing like this") == []


def test_cannot_see_other_peoples_issues(app, other_user, issues):
    assert services.search_issues(other_user, "login") == []


def test_user_without_projects_gets_empty_list(app, make_user):
    assert services.search_issues(make_user(), "anything") == []


@pytest.mark.parametrize("filters", [{"status": "closed"}, {"priority": "urgent"}])
def test_invalid_filters_raise(app, user, filters):
    with pytest.raises(ValueError, match="Unknown"):
        services.search_issues(user, **filters)


def test_results_are_capped(app, user, make_issue, monkeypatch):
    monkeypatch.setattr(services, "MAX_RESULTS", 2)
    for i in range(4):
        make_issue(title=f"Issue {i}")
    assert len(services.search_issues(user, "issue")) == 2
