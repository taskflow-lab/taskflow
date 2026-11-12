import copy
from pathlib import Path

import pytest
from flask import g

from app import create_app
from app.extensions import db as _db
from app.modules.auth import services as auth_services
from app.modules.billing import services as billing_services
from app.modules.issues import services as issue_services
from app.modules.projects import services as project_services

TESTS_DIR = Path(__file__).parent
TEST_TYPES = {"unit", "integration", "contract", "api", "smoke", "health", "regression", "ui"}
MODULES = {"auth", "projects", "issues", "sprints", "board", "search", "notifications", "billing", "health"}
DEFAULT_PASSWORD = "password123"


def pytest_collection_modifyitems(config, items):
    """Mark every test by its folder: tests/<type>/<module>/test_x.py -> @type + @module."""
    for item in items:
        parts = Path(item.fspath).relative_to(TESTS_DIR).parts
        if parts and parts[0] in TEST_TYPES:
            item.add_marker(getattr(pytest.mark, parts[0]))
        if len(parts) > 2 and parts[1] in MODULES:
            item.add_marker(getattr(pytest.mark, parts[1]))


# ---------- App & database ----------

@pytest.fixture
def app():
    app = create_app("testing")
    # Config dicts are shared between apps; give each test its own copy so changes don't leak.
    app.config["PLAN_LIMITS"] = copy.deepcopy(app.config["PLAN_LIMITS"])

    @app.before_request
    def _fresh_login_per_request():
        # The test keeps one app context open, so Flask shares `g` between requests.
        # Flask-Login caches the user in `g`; clear it so each request uses its own login cookie.
        g.pop("_login_user", None)

    with app.app_context():
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def client(app):
    return app.test_client()


# ---------- Users ----------

@pytest.fixture
def make_user(app):
    counter = {"n": 0}

    def _make_user(name=None, email=None, password=DEFAULT_PASSWORD, role="member"):
        counter["n"] += 1
        n = counter["n"]
        return auth_services.register_user(
            email=email or f"user{n}@test.com",
            name=name or f"Test User {n}",
            password=password,
            role=role,
        )

    return _make_user


@pytest.fixture
def user(make_user):
    return make_user(name="Alice Owner", email="alice@test.com")


@pytest.fixture
def other_user(make_user):
    return make_user(name="Bob Outsider", email="bob@test.com")


@pytest.fixture
def admin_user(make_user):
    return make_user(name="Ada Admin", email="admin@test.com", role="admin")


# ---------- Logged-in clients ----------

def login_client(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True
    return client


@pytest.fixture
def logged_in_client(client, user):
    return login_client(client, user)


@pytest.fixture
def auth_headers(user):
    return {"Authorization": f"Bearer {auth_services.generate_api_token(user)}"}


@pytest.fixture
def headers_for(app):
    def _headers_for(some_user):
        return {"Authorization": f"Bearer {auth_services.generate_api_token(some_user)}"}

    return _headers_for


# ---------- Projects & issues ----------

@pytest.fixture
def make_project(app, user):
    counter = {"n": 0}

    def _make_project(owner=None, name=None, key=None, description="", members=()):
        counter["n"] += 1
        owner = owner or user
        project = project_services.create_project(
            owner=owner,
            name=name or f"Project {counter['n']}",
            key=key or f"PR{counter['n']}",
            description=description,
        )
        for member in members:
            project_services.add_member(project, owner, member.email)
        return project

    return _make_project


@pytest.fixture
def project(make_project):
    return make_project(name="Website", key="WEB")


@pytest.fixture
def make_issue(app, user, project):
    def _make_issue(title="Sample issue", target_project=None, reporter=None, **fields):
        return issue_services.create_issue(
            project=target_project or project,
            reporter=reporter or user,
            title=title,
            **fields,
        )

    return _make_issue


@pytest.fixture
def issue(make_issue):
    return make_issue(title="Fix login button", issue_type="bug", priority="high")


# ---------- Billing ----------

@pytest.fixture
def set_plan(app):
    def _set_plan(some_user, plan_code):
        subscription = billing_services.get_subscription(some_user)
        if subscription.plan != plan_code:
            billing_services.change_plan(some_user, plan_code)
        return billing_services.get_subscription(some_user)

    return _set_plan
