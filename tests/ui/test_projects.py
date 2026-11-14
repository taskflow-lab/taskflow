import re

from playwright.sync_api import expect

from tests.ui.conftest import unique
from tests.ui.pages.project_pages import CreateProjectPage, PlansPage, ProjectsPage


def test_project_key_is_suggested_from_the_name(logged_in_page):
    form = CreateProjectPage(logged_in_page).open()

    form.name.type("Mobile Banking App")

    expect(form.key).to_have_value("MBA")


def test_create_project(logged_in_page):
    key = unique("P")

    summary = CreateProjectPage(logged_in_page).open().create("Website Relaunch", key=key)

    expect(logged_in_page).to_have_url(re.compile(rf"/projects/{key}$"))
    expect(summary.title).to_have_text("Website Relaunch")
    expect(summary.flash).to_contain_text("Project Website Relaunch created")
    expect(ProjectsPage(logged_in_page).open().project_link(key)).to_have_text("Website Relaunch")


def test_duplicate_project_key_shows_error(logged_in_page, project_key):
    form = CreateProjectPage(logged_in_page).open()
    form.create("Another project", key=project_key)

    expect(form.key_error).to_contain_text("already taken")


def test_free_plan_allows_three_projects_then_asks_to_upgrade(logged_in_page):
    for _ in range(3):
        CreateProjectPage(logged_in_page).open().create("Project", key=unique("P"))

    CreateProjectPage(logged_in_page).open().create("One too many", key=unique("P"))

    plans = PlansPage(logged_in_page)
    expect(logged_in_page).to_have_url(re.compile(r"/billing/$"))
    expect(plans.flash).to_contain_text("allows 3 active projects")

    plans.switch_to("standard")
    expect(plans.current_plan).to_have_text("Standard")

    key = unique("P")
    CreateProjectPage(logged_in_page).open().create("Now it works", key=key)
    expect(logged_in_page).to_have_url(re.compile(rf"/projects/{key}$"))
