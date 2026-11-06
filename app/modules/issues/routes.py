from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.modules.issues import services
from app.modules.issues.models import STATUS_LABELS
from app.modules.projects.routes import get_project_or_abort
from app.modules.projects.services import user_can_access

bp = Blueprint("issues", __name__)


class IssueForm(FlaskForm):
    title = StringField("Summary", validators=[DataRequired(), Length(max=200)])
    issue_type = SelectField("Type")
    priority = SelectField("Priority")
    assignee_id = SelectField("Assignee", coerce=int)
    due_date = DateField("Due date", validators=[Optional()])
    description = TextAreaField("Description")


def build_issue_form(project, issue=None):
    form = IssueForm(obj=issue)
    form.issue_type.choices = [(t, t.capitalize()) for t in current_app.config["ISSUE_TYPES"]]
    form.priority.choices = [(p, p.capitalize()) for p in current_app.config["ISSUE_PRIORITIES"]]
    form.assignee_id.choices = [(0, "Unassigned")] + [(m.id, m.name) for m in project.members]
    if request.method == "GET" and issue is None:
        form.priority.data = "medium"
        form.assignee_id.data = 0
    if request.method == "GET" and issue is not None and issue.assignee_id is None:
        form.assignee_id.data = 0
    return form


def get_issue_or_abort(issue_key):
    try:
        issue = services.get_issue_by_key(issue_key)
    except LookupError:
        abort(404)
    if not user_can_access(current_user, issue.project):
        abort(403)
    return issue


@bp.get("/projects/<key>/issues")
@login_required
def list_issues(key):
    project = get_project_or_abort(key)
    filters = {
        "status": request.args.get("status") or None,
        "priority": request.args.get("priority") or None,
        "assignee_id": request.args.get("assignee_id", type=int) or None,
    }
    try:
        issues = services.list_issues(project, **filters)
    except ValueError as error:
        flash(str(error), "danger")
        issues = services.list_issues(project)
    return render_template(
        "issues/list.html",
        project=project,
        issues=issues,
        filters=filters,
        status_labels=STATUS_LABELS,
        priorities=current_app.config["ISSUE_PRIORITIES"],
    )


@bp.route("/projects/<key>/issues/new", methods=["GET", "POST"])
@login_required
def create_issue(key):
    project = get_project_or_abort(key)
    form = build_issue_form(project)
    if form.validate_on_submit():
        try:
            issue = services.create_issue(
                project=project,
                reporter=current_user,
                title=form.title.data,
                description=form.description.data,
                issue_type=form.issue_type.data,
                priority=form.priority.data,
                assignee_id=form.assignee_id.data or None,
                due_date=form.due_date.data,
            )
        except ValueError as error:
            form.title.errors.append(str(error))
        else:
            flash(f"Issue {issue.key} created.", "success")
            return redirect(url_for("issues.issue_detail", issue_key=issue.key))
    return render_template("issues/create.html", project=project, form=form)


@bp.get("/issues/<issue_key>")
@login_required
def issue_detail(issue_key):
    issue = get_issue_or_abort(issue_key)
    form = build_issue_form(issue.project, issue)
    return render_template(
        "issues/detail.html",
        project=issue.project,
        issue=issue,
        form=form,
        status_labels=STATUS_LABELS,
    )


@bp.post("/issues/<issue_key>/edit")
@login_required
def edit_issue(issue_key):
    issue = get_issue_or_abort(issue_key)
    form = build_issue_form(issue.project, issue)
    if form.validate_on_submit():
        try:
            services.update_issue(
                issue,
                current_user,
                title=form.title.data,
                description=form.description.data,
                type=form.issue_type.data,
                priority=form.priority.data,
                assignee_id=form.assignee_id.data or None,
                due_date=form.due_date.data,
            )
        except ValueError as error:
            flash(str(error), "danger")
        else:
            flash("Issue updated.", "success")
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
    return redirect(url_for("issues.issue_detail", issue_key=issue.key))


@bp.post("/issues/<issue_key>/status")
@login_required
def change_status(issue_key):
    issue = get_issue_or_abort(issue_key)
    try:
        services.change_status(issue, request.form.get("status", ""), current_user)
    except ValueError as error:
        flash(str(error), "danger")
    else:
        flash(f"{issue.key} moved to {issue.status_label}.", "success")
    return redirect(url_for("issues.issue_detail", issue_key=issue.key))


@bp.post("/issues/<issue_key>/comments")
@login_required
def add_comment(issue_key):
    issue = get_issue_or_abort(issue_key)
    try:
        services.add_comment(issue, current_user, request.form.get("body", ""))
    except ValueError as error:
        flash(str(error), "danger")
    return redirect(url_for("issues.issue_detail", issue_key=issue.key) + "#comments")
