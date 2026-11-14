from tests.ui.pages.base_page import BasePage


class ProjectsPage(BasePage):
    path = "/projects/"

    def project_link(self, key):
        return self.test_id(f"project-link-{key}")


class CreateProjectPage(BasePage):
    path = "/projects/new"

    @property
    def name(self):
        return self.test_id("project-name")

    @property
    def key(self):
        return self.test_id("project-key")

    @property
    def key_error(self):
        return self.test_id("project-key-error")

    def create(self, name, key=None, description=""):
        self.name.fill(name)
        if key is not None:
            self.key.fill(key)
        self.test_id("project-description").fill(description)
        self.test_id("project-submit").click()
        return ProjectSummaryPage(self.page)


class ProjectSummaryPage(BasePage):
    path = "/projects/{key}"

    @property
    def title(self):
        return self.test_id("project-title")

    @property
    def active_sprint(self):
        return self.test_id("summary-active-sprint")


class PlansPage(BasePage):
    path = "/billing/"

    @property
    def current_plan(self):
        return self.test_id("current-plan")

    def switch_to(self, plan):
        self.accept_next_confirm()
        self.test_id(f"choose-{plan}").click()
        return self
