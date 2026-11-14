from tests.ui.pages.base_page import BasePage


class CreateIssuePage(BasePage):
    path = "/projects/{key}/issues/new"

    @property
    def title_error(self):
        return self.test_id("issue-title-error")

    def create(self, title, issue_type="task", priority="medium", description=""):
        self.test_id("issue-title").fill(title)
        self.test_id("issue-type").select_option(issue_type)
        self.test_id("issue-priority").select_option(priority)
        self.test_id("issue-description").fill(description)
        self.test_id("issue-submit").click()
        return IssuePage(self.page)


class IssuePage(BasePage):
    path = "/issues/{issue_key}"

    @property
    def key(self):
        return self.test_id("issue-key")

    @property
    def title(self):
        return self.test_id("issue-title")

    @property
    def status(self):
        return self.test_id("issue-status")

    @property
    def comments(self):
        return self.test_id("comment")

    def change_status(self, status):
        self.test_id("status-select").select_option(status)
        self.test_id("status-submit").click()
        return self

    def add_comment(self, text):
        self.test_id("comment-body").fill(text)
        self.test_id("comment-submit").click()
        return self


class SearchPage(BasePage):
    path = "/search/"

    def result(self, issue_key):
        return self.test_id(f"search-row-{issue_key}")

    @property
    def count(self):
        return self.test_id("search-count")
