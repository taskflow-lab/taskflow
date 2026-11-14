import re

from playwright.sync_api import expect

from tests.ui.pages.issue_pages import CreateIssuePage, IssuePage, SearchPage


def test_create_issue(logged_in_page, project_key):
    issue = CreateIssuePage(logged_in_page).open(key=project_key).create(
        "Fix login button", issue_type="bug", priority="high", description="Safari only"
    )

    expect(logged_in_page).to_have_url(re.compile(rf"/issues/{project_key}-1$"))
    expect(issue.key).to_have_text(f"{project_key}-1")
    expect(issue.title).to_contain_text("Fix login button")
    expect(issue.status).to_have_text("To Do")
    expect(issue.flash).to_contain_text(f"Issue {project_key}-1 created")


def test_issue_numbers_go_up(make_issue, project_key):
    assert make_issue("First") == f"{project_key}-1"
    assert make_issue("Second") == f"{project_key}-2"


def test_issue_without_title_shows_error(logged_in_page, project_key):
    form = CreateIssuePage(logged_in_page).open(key=project_key)
    form.create("")

    expect(form.title_error).to_be_visible()
    expect(logged_in_page).to_have_url(re.compile(r"/issues/new$"))


def test_change_status_and_add_comment(logged_in_page, make_issue):
    issue_key = make_issue("Write release notes")
    issue = IssuePage(logged_in_page).open(issue_key=issue_key)

    issue.change_status("in_progress")
    expect(issue.status).to_have_text("In Progress")

    issue.add_comment("Started on the draft")
    expect(issue.comments).to_have_count(1)
    expect(issue.comments.first).to_contain_text("Started on the draft")


def test_search_finds_issue_from_the_top_bar(logged_in_page, make_issue):
    issue_key = make_issue("Payment page times out")

    IssuePage(logged_in_page).search("times out")

    results = SearchPage(logged_in_page)
    expect(logged_in_page).to_have_url(re.compile(r"/search/\?q="))
    expect(results.result(issue_key)).to_be_visible()
    expect(results.count).to_have_text("1 result")
