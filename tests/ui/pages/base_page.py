class BasePage:
    """Shared behaviour for every page object.

    A page object knows HOW to use a page (which field, which button).
    Tests only say WHAT to do: RegisterPage(page).open().register(...).
    If the HTML changes, only the page object needs updating, not every test.
    """

    path = "/"

    def __init__(self, page):
        self.page = page

    def open(self, **params):
        self.page.goto(self.path.format(**params))
        return self

    def test_id(self, value):
        return self.page.get_by_test_id(value)

    # ---------- things that are on every page ----------

    @property
    def flash(self):
        return self.test_id("flash-messages")

    @property
    def user_menu(self):
        return self.test_id("user-menu-button")

    def logout(self):
        self.user_menu.click()
        self.test_id("logout-button").click()

    def search(self, text):
        box = self.test_id("nav-search-input")
        box.fill(text)
        box.press("Enter")

    def accept_next_confirm(self):
        """Buttons with data-confirm open a browser confirm(). Playwright cancels those by default."""
        self.page.once("dialog", lambda dialog: dialog.accept())
