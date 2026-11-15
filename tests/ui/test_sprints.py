import re

import pytest
from playwright.sync_api import expect

from tests.ui.pages.project_pages import ProjectSummaryPage
from tests.ui.pages.sprint_pages import BacklogPage, BoardPage


@pytest.fixture
def three_issues(make_issue):
    return [make_issue(title) for title in ["Login page", "Signup page", "Docs"]]


def test_plan_start_and_complete_a_sprint(logged_in_page, project_key, three_issues):
    login_page, signup_page, docs = three_issues

    backlog = BacklogPage(logged_in_page).open(key=project_key)
    backlog.create_sprint("Auth sprint", goal="Ship sign-up")
    expect(backlog.sprint_status).to_have_text("planned")

    backlog.add_to_sprint(login_page)
    backlog.add_to_sprint(signup_page)
    expect(backlog.sprint_issue(login_page)).to_be_visible()
    expect(backlog.sprint_issue(signup_page)).to_be_visible()
    expect(backlog.backlog_issue(docs)).to_be_visible()

    board = backlog.start_sprint(weeks=1)
    expect(logged_in_page).to_have_url(re.compile(rf"/projects/{project_key}/board$"))
    expect(board.title).to_have_text("Auth sprint")
    expect(board.sprint_banner).to_contain_text("7 days left")
    expect(board.sprint_banner).to_contain_text("Goal: Ship sign-up")
    expect(board.card(login_page)).to_be_visible()
    expect(board.card(docs)).to_have_count(0)

    expect(ProjectSummaryPage(logged_in_page).open(key=project_key).active_sprint).to_contain_text("Auth sprint")

    backlog = BoardPage(logged_in_page).open(key=project_key).complete_sprint()
    expect(backlog.flash).to_contain_text("Auth sprint completed: 0 done, 2 moved back to the backlog")
    expect(backlog.backlog_issue(login_page)).to_be_visible()
    expect(BoardPage(logged_in_page).open(key=project_key).no_sprint_banner).to_be_visible()


def test_cannot_start_an_empty_sprint(logged_in_page, project_key):
    backlog = BacklogPage(logged_in_page).open(key=project_key)
    backlog.create_sprint("Empty sprint")

    expect(backlog.start_button).to_be_disabled()


def test_remove_issue_from_sprint(logged_in_page, project_key, three_issues):
    issue_key = three_issues[0]
    backlog = BacklogPage(logged_in_page).open(key=project_key)
    backlog.create_sprint()
    backlog.add_to_sprint(issue_key)
    expect(backlog.sprint_issue(issue_key)).to_be_visible()

    backlog.remove_from_sprint(issue_key)

    expect(backlog.sprint_issue(issue_key)).to_have_count(0)
    expect(backlog.backlog_issue(issue_key)).to_be_visible()
