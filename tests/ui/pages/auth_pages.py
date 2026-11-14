from tests.ui.pages.base_page import BasePage


class RegisterPage(BasePage):
    path = "/auth/register"

    def register(self, name, email, password, confirm=None):
        self.test_id("register-name").fill(name)
        self.test_id("register-email").fill(email)
        self.test_id("register-password").fill(password)
        self.test_id("register-confirm").fill(password if confirm is None else confirm)
        self.test_id("register-submit").click()
        return self

    def error_for(self, field):
        """field is one of: name, email, password, confirm."""
        return self.test_id(f"register-{field}-error")


class LoginPage(BasePage):
    path = "/auth/login"

    def login(self, email, password):
        self.test_id("login-email").fill(email)
        self.test_id("login-password").fill(password)
        self.test_id("login-submit").click()
        return self
