from tests.ui.pages.base_page import BasePage


class BacklogPage(BasePage):
    path = "/projects/{key}/backlog"

    def create_sprint(self, name="", goal=""):
        self.test_id("sprint-name").fill(name)
        self.test_id("sprint-goal").fill(goal)
        self.test_id("create-sprint").click()
        return self

    def add_to_sprint(self, issue_key):
        """Add a backlog issue to the sprint selected in its dropdown (the first open sprint)."""
        self.test_id(f"add-{issue_key}").click()
        return self

    def remove_from_sprint(self, issue_key):
        self.test_id(f"remove-{issue_key}").click()
        return self

    def start_sprint(self, weeks=2):
        self.test_id("sprint-weeks").select_option(str(weeks))
        self.start_button.click()
        return BoardPage(self.page)

    @property
    def start_button(self):
        return self.test_id("start-sprint")

    @property
    def sprint_status(self):
        return self.test_id("sprint-status")

    def sprint_issue(self, issue_key):
        return self.test_id(f"sprint-issue-{issue_key}")

    def backlog_issue(self, issue_key):
        return self.test_id(f"backlog-issue-{issue_key}")


class BoardPage(BasePage):
    path = "/projects/{key}/board"

    @property
    def title(self):
        return self.test_id("board-title")

    @property
    def sprint_banner(self):
        return self.test_id("sprint-banner")

    @property
    def no_sprint_banner(self):
        return self.test_id("no-sprint-banner")

    @property
    def toast(self):
        return self.test_id("toast")

    def card(self, issue_key):
        return self.test_id(f"card-{issue_key}")

    def column(self, status):
        return self.test_id(f"column-{status}")

    def card_in_column(self, issue_key, status):
        return self.column(status).get_by_test_id(f"card-{issue_key}")

    def column_count(self, status):
        return self.test_id(f"column-count-{status}")

    def drag(self, issue_key, to_status):
        self.card(issue_key).drag_to(self.column(to_status))
        return self

    def filter(self, text):
        self.test_id("board-search").fill(text)
        self.test_id("board-search").press("Enter")
        return self

    def complete_sprint(self):
        self.accept_next_confirm()
        self.test_id("board-complete-sprint").click()
        return BacklogPage(self.page)
