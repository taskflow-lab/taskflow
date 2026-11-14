"""Fixtures for browser tests. Everything, including test data, is created through the UI.

How UI tests run:
1. `live_server` starts the real TaskFlow app in a background thread, on a free port,
   with its own database file and CSRF protection ON (like production).
2. pytest-playwright gives every test a fresh browser `page` (no shared cookies).
3. Each test signs up its own new user through the sign-up form, so tests never share data.
"""
import threading
import uuid

import pytest
from werkzeug.serving import make_server

from app import create_app
from tests.ui.pages.auth_pages import RegisterPage
from tests.ui.pages.issue_pages import CreateIssuePage
from tests.ui.pages.project_pages import CreateProjectPage

PASSWORD = "password123"


def unique(prefix=""):
    """Random suffix, so every test uses different emails and project keys."""
    return prefix + uuid.uuid4().hex[:6].upper()


# ---------- the app under test ----------

@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("ui-db") / "taskflow-ui.db"
    app = create_app(
        "testing",
        overrides={
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
            "WTF_CSRF_ENABLED": True,
        },
    )
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def base_url(live_server):
    """pytest-playwright uses this, so page.goto("/projects/") works with relative URLs."""
    return live_server


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1400, "height": 900}}


# ---------- test data, created through the UI ----------

@pytest.fixture
def new_user():
    """Details for a user who does not exist yet."""
    return {"name": "UI Tester", "email": f"ui-{unique().lower()}@test.com", "password": PASSWORD}


@pytest.fixture
def logged_in_page(page, new_user):
    """Sign up through the form. The app logs new users in straight away."""
    RegisterPage(page).open().register(**new_user)
    page.wait_for_url("**/projects/")
    return page


@pytest.fixture
def registered_user(page, new_user):
    """A user who has an account but is logged out (for login tests)."""
    register = RegisterPage(page).open().register(**new_user)
    page.wait_for_url("**/projects/")
    register.logout()
    page.wait_for_url("**/auth/login")
    return new_user


@pytest.fixture
def project_key(logged_in_page):
    """Create a project through the 'Create project' form and return its key."""
    key = unique("UI")
    CreateProjectPage(logged_in_page).open().create("UI Project", key=key)
    logged_in_page.wait_for_url(f"**/projects/{key}")
    return key


@pytest.fixture
def make_issue(logged_in_page, project_key):
    """Create issues through the 'Create issue' form. Returns the new issue key, e.g. UI3F9A2C-1."""

    def _make_issue(title, **fields):
        issue = CreateIssuePage(logged_in_page).open(key=project_key).create(title, **fields)
        logged_in_page.wait_for_url("**/issues/*")
        return issue.key.inner_text()

    return _make_issue
