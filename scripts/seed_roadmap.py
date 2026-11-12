"""Create a "TaskFlow Platform" project with the real work done so far, so you can track it on your own board.

Usage (from the repo root, with the venv active):
    python scripts/seed_roadmap.py you@example.com

The email must belong to an account you already registered in the app.
Safe to run twice: it stops if the TF project already exists. Nothing else is changed or deleted.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.modules.auth.services import get_user_by_email  # noqa: E402
from app.modules.issues import services as issues  # noqa: E402
from app.modules.projects import services as projects  # noqa: E402

PROJECT_KEY = "TF"
PROJECT_NAME = "TaskFlow Platform"
PROJECT_DESCRIPTION = (
    "Building TaskFlow the way a company would: the app (Dev), the test framework (SDET) "
    "and the CI/CD pipeline (DevOps)."
)

# (title, type, priority, status, description)
WORK = [
    # ---------- Developer ----------
    ("[Dev] App foundation: app factory, config, extensions", "task", "high", "done",
     "create_app(), development/testing/production configs, SQLAlchemy, Flask-Login, CSRF."),
    ("[Dev] Auth: sign up, log in, log out, API tokens", "story", "high", "done",
     "Hashed passwords, unique lowercase emails, safe ?next= redirects, 24h Bearer tokens."),
    ("[Dev] Projects: create, members, archive", "story", "high", "done",
     "Unique keys, owner is always a member, archived projects don't count toward the plan limit."),
    ("[Dev] Issues: create, edit, status, comments", "story", "highest", "done",
     "Keys like TF-1, types, priorities, 4 statuses, assignee must be a member."),
    ("[Dev] Kanban board with drag and drop", "story", "medium", "done",
     "Dropping a card calls the transition API; the card jumps back if the API fails."),
    ("[Dev] Search across projects", "story", "medium", "done",
     "Text in title/description or exact issue key, only in projects you can access."),
    ("[Dev] Notifications and unread bell", "story", "medium", "done",
     "On assign, status change and comment; never notify the person who made the change."),
    ("[Dev] Billing plans with mock payments", "story", "high", "done",
     "Free 3 / Standard 10 / Premium unlimited projects. Limit hit returns HTTP 402."),
    ("[Dev] Health and readiness endpoints", "task", "low", "done",
     "/health (app up) and /ready (database reachable, 503 if not)."),
    ("[Dev] REST API v1", "story", "high", "done",
     "JSON endpoints for auth, projects, issues, billing, with one consistent error format."),

    # ---------- SDET ----------
    ("[SDET] Test framework: pytest config, fixtures, markers", "task", "highest", "done",
     "conftest.py fixtures, fresh in-memory DB per test, auto-marking tests by folder."),
    ("[SDET] Smoke tests", "task", "medium", "done", "Is the app alive: starts, login page, projects page."),
    ("[SDET] Unit tests for all 8 modules", "task", "high", "done",
     "141 tests on services.py using parametrize, pytest.raises and monkeypatch."),
    ("[SDET] API tests", "task", "high", "done",
     "39 tests: status codes 400/401/402/403/404, security checks, full login flow."),
    ("[SDET] Integration tests", "task", "high", "in_review",
     "Billing + projects, issues + notifications + board + search, multi-user flows. PR #3."),
    ("[SDET] Contract tests with JSON schema", "task", "high", "in_review",
     "Lock the API response shapes. Found the timestamp bug. PR #3."),

    # ---------- Bugs ----------
    ("[Bug] Plan limit changes leak between tests", "bug", "medium", "done",
     "app.config['PLAN_LIMITS'] was the same dict for every app. Fixed with a deepcopy in the app fixture."),
    ("[Bug] Logged-in user cached across requests in tests", "bug", "high", "in_review",
     "Tests share one app context, so Flask-Login's user in g leaked: Bob was served as Alice. "
     "Fixed in conftest.py. PR #3."),
    ("[Bug] API timestamps have no timezone", "bug", "highest", "done",
     "created_at/updated_at returned like 2026-11-11T09:12:33 (not valid ISO-8601). "
     "Found by contract tests, fixed with iso_utc() in PR #4."),
    ("[Bug] Payment.created_at missed in the timestamp fix", "bug", "high", "done",
     "Found while verifying PR #4: test_upgrade_contract still failed. One-line follow-up fix."),
    ("[Bug] Empty placeholder workflows fail on every push", "bug", "low", "done",
     "push.yml and nightly-regression.yml were empty, so GitHub reported a failed run. Removed in PR #5."),

    # ---------- DevOps ----------
    ("[DevOps] CI pipeline on every PR", "task", "highest", "done",
     "pr.yml: pull_request, push to main, merge_group, manual runs. Pip cache, 15 min timeout."),
    ("[DevOps] HTML and Allure reports in CI", "task", "medium", "done",
     "pytest-html and single-file Allure report uploaded as artifacts, even when tests fail."),
    ("[DevOps] PR template and CODEOWNERS", "task", "medium", "done",
     "Every PR describes its change and affected modules; owners per folder."),
    ("[DevOps] Protect main with a ruleset", "task", "highest", "done",
     "PR required, CI must pass, branch up to date, no force pushes, squash only."),
    ("[DevOps] Move repo to the taskflow-lab organization", "task", "medium", "done",
     "Free private repos don't enforce rulesets, so the repo moved to an org and went public."),

    # ---------- Next ----------
    ("[SDET] Playwright UI tests with page objects", "story", "high", "todo",
     "Login, create project, create issue, drag a card on the board, using data-testid."),
    ("[SDET] Regression suite and nightly run", "story", "medium", "todo",
     "Full suite on a schedule, with failures triaged every morning."),
    ("[DevOps] Parallel jobs, caching and matrix builds", "task", "medium", "todo",
     "Split unit/API/UI into parallel jobs; pytest-xdist; test on several Python versions."),
    ("[DevOps] Publish Allure history to GitHub Pages", "task", "low", "todo",
     "So the Trend panel shows pass/fail history across runs."),
    ("[DevOps] Dockerize TaskFlow", "story", "medium", "todo", "Dockerfile, gunicorn, health check."),
    ("[DevOps] Deploy to staging with smoke and health checks", "story", "medium", "todo",
     "Continuous Delivery: build, deploy, verify, roll back on failure."),
    ("[DevOps] Smart test selection from a dependency map", "story", "highest", "todo",
     "Change billing -> run billing unit, projects integration and billing contract tests only."),
    ("[DevOps] AI-based test selection", "story", "highest", "todo",
     "Send the diff and test list to an LLM, run the ranked tests, keep smoke tests and a nightly full run."),
    ("[DevOps] Merge queue with merge_group", "task", "low", "todo",
     "Retest PRs together with the latest main before merging."),
    ("[Dev] Viewer role should be read-only", "story", "low", "todo",
     "Gap found while reviewing requirements: viewers currently behave like members."),
]

COMMENTS = {
    "[Bug] API timestamps have no timezone":
        "Verified: after the follow-up payment fix, all contract tests pass on PR #3.",
    "[Bug] Payment.created_at missed in the timestamp fix":
        "Lesson: run grep -rn '_at.isoformat()' app/modules before pushing a fix like this.",
}


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/seed_roadmap.py you@example.com")

    app = create_app()
    with app.app_context():
        user = get_user_by_email(sys.argv[1])
        if user is None:
            sys.exit(f"No account for {sys.argv[1]}. Sign up in the app first, then run this again.")

        try:
            projects.get_project_by_key(PROJECT_KEY)
            sys.exit(f"Project {PROJECT_KEY} already exists. Nothing changed.")
        except LookupError:
            pass

        try:
            project = projects.create_project(user, PROJECT_NAME, PROJECT_KEY, PROJECT_DESCRIPTION)
        except PermissionError as error:
            sys.exit(f"{error}\nArchive a project or switch plan on the Plans page, then run this again.")

        for title, kind, priority, status, description in WORK:
            issue = issues.create_issue(
                project, user, title, description=description,
                issue_type=kind, priority=priority, assignee_id=user.id,
            )
            if status != "todo":
                issues.change_status(issue, status, user)
            if title in COMMENTS:
                issues.add_comment(issue, user, COMMENTS[title])

        counts = {status: count for status, _, count in issues.count_by_status(project)}
        print(f"Created {PROJECT_KEY} '{PROJECT_NAME}' with {len(WORK)} issues: {counts}")
        print(f"Open http://127.0.0.1:5000/projects/{PROJECT_KEY}/board")


if __name__ == "__main__":
    main()
