import re

from playwright.sync_api import expect

from tests.ui.pages.auth_pages import LoginPage, RegisterPage


# ---------- sign up ----------

def test_sign_up_logs_you_in(page, new_user):
    RegisterPage(page).open().register(**new_user)

    expect(page).to_have_url(re.compile(r"/projects/$"))
    expect(page.get_by_test_id("flash-success")).to_contain_text("Your account is ready")
    expect(page.get_by_test_id("user-menu-button")).to_have_text("UT")  # initials of "UI Tester"


def test_sign_up_with_empty_form_shows_errors(page):
    register = RegisterPage(page).open().register(name="", email="", password="")

    expect(register.error_for("name")).to_be_visible()
    expect(register.error_for("email")).to_be_visible()
    expect(page).to_have_url(re.compile(r"/auth/register$"))


def test_sign_up_with_different_passwords(page, new_user):
    register = RegisterPage(page).open().register(**new_user, confirm="something-else")

    expect(register.error_for("confirm")).to_have_text("Passwords must match")


def test_sign_up_with_short_password(page, new_user):
    register = RegisterPage(page).open().register(new_user["name"], new_user["email"], "short")

    expect(register.error_for("password")).to_contain_text("at least 8")


def test_sign_up_with_an_email_that_already_exists(page, registered_user):
    register = RegisterPage(page).open().register(**registered_user)

    expect(register.error_for("email")).to_have_text("An account with this email already exists")


# ---------- log in / log out ----------

def test_login_with_valid_credentials(page, registered_user):
    LoginPage(page).open().login(registered_user["email"], registered_user["password"])

    expect(page).to_have_url(re.compile(r"/projects/$"))
    expect(page.get_by_test_id("flash-success")).to_contain_text("Welcome back, UI Tester")


def test_login_with_wrong_password_shows_error(page, registered_user):
    login = LoginPage(page).open().login(registered_user["email"], "wrong-password")

    expect(page).to_have_url(re.compile(r"/auth/login"))
    expect(login.flash).to_contain_text("Invalid email or password")


def test_protected_page_redirects_to_login_and_back(page, registered_user):
    page.goto("/projects/new")
    expect(page).to_have_url(re.compile(r"/auth/login\?next="))

    LoginPage(page).login(registered_user["email"], registered_user["password"])

    expect(page).to_have_url(re.compile(r"/projects/new$"))


def test_logout(logged_in_page):
    LoginPage(logged_in_page).logout()

    expect(logged_in_page).to_have_url(re.compile(r"/auth/login"))
    expect(logged_in_page.get_by_test_id("flash-info")).to_contain_text("logged out")
