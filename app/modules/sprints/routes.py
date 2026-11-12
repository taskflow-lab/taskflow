from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.modules.issues.services import get_issue_by_key
from app.modules.projects.routes import get_project_or_abort
from app.modules.projects.services import user_can_access
from app.modules.sprints import services

bp = Blueprint("sprints", __name__)


def get_sprint_or_abort(sprint_id):
    try:
        sprint = services.get_sprint(sprint_id)
    except LookupError:
        abort(404)
    if not user_can_access(current_user, sprint.project):
        abort(403)
    return sprint


def back_to_backlog(project):
    return redirect(url_for("sprints.view_backlog", key=project.key))


def run(action, success_message=None):
    """Run a service call; flash its error instead of crashing the page."""
    try:
        result = action()
    except (ValueError, LookupError) as error:
        flash(str(error.args[0] if error.args else error), "danger")
        return None
    if success_message:
        flash(success_message(result) if callable(success_message) else success_message, "success")
    return result


@bp.get("/projects/<key>/backlog")
@login_required
def view_backlog(key):
    project = get_project_or_abort(key)
    sprints = services.list_open_sprints(project)
    return render_template(
        "sprints/backlog.html",
        project=project,
        sprints=sprints,
        backlog=services.get_backlog(project),
        has_active=any(s.status == "active" for s in sprints),
        days_left=services.days_left,
        allowed_weeks=services.ALLOWED_WEEKS,
        default_weeks=services.DEFAULT_WEEKS,
    )


@bp.post("/projects/<key>/sprints")
@login_required
def create_sprint(key):
    project = get_project_or_abort(key)
    run(
        lambda: services.create_sprint(project, request.form.get("name"), request.form.get("goal")),
        lambda sprint: f"{sprint.name} created. Add issues from the backlog, then start it.",
    )
    return back_to_backlog(project)


@bp.post("/projects/<key>/backlog/add")
@login_required
def add_to_sprint(key):
    project = get_project_or_abort(key)
    sprint = get_sprint_or_abort(request.form.get("sprint_id", type=int) or 0)
    if sprint.project_id != project.id:
        abort(404)

    def action():
        issue = get_issue_by_key(request.form.get("issue_key", ""))
        services.add_issue(sprint, issue)
        return issue

    run(action, lambda issue: f"{issue.key} added to {sprint.name}.")
    return back_to_backlog(project)


@bp.post("/sprints/<int:sprint_id>/issues/<issue_key>/remove")
@login_required
def remove_from_sprint(sprint_id, issue_key):
    sprint = get_sprint_or_abort(sprint_id)
    run(
        lambda: services.remove_issue(sprint, get_issue_by_key(issue_key)),
        f"{issue_key.upper()} moved back to the backlog.",
    )
    return back_to_backlog(sprint.project)


@bp.post("/sprints/<int:sprint_id>/start")
@login_required
def start_sprint(sprint_id):
    sprint = get_sprint_or_abort(sprint_id)
    started = run(
        lambda: services.start_sprint(sprint, request.form.get("weeks", services.DEFAULT_WEEKS)),
        lambda s: f"{s.name} started. It ends on {s.end_date.strftime('%b %d')}.",
    )
    if started:
        return redirect(url_for("board.view_board", key=sprint.project.key))
    return back_to_backlog(sprint.project)


@bp.post("/sprints/<int:sprint_id>/complete")
@login_required
def complete_sprint(sprint_id):
    sprint = get_sprint_or_abort(sprint_id)
    run(
        lambda: services.complete_sprint(sprint),
        lambda r: f"{sprint.name} completed: {r['done']} done, {r['unfinished']} moved back to the backlog.",
    )
    return back_to_backlog(sprint.project)
