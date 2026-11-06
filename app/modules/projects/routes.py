from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length

from app.modules.billing.services import PlanLimitError
from app.modules.projects import services

bp = Blueprint("projects", __name__, url_prefix="/projects")


class ProjectForm(FlaskForm):
    name = StringField("Project name", validators=[DataRequired(), Length(max=120)])
    key = StringField("Key", validators=[DataRequired(), Length(min=2, max=10)])
    description = TextAreaField("Description")


def get_project_or_abort(key):
    try:
        project = services.get_project_by_key(key)
    except LookupError:
        abort(404)
    if not services.user_can_access(current_user, project):
        abort(403)
    return project


@bp.get("/")
@login_required
def list_projects():
    projects = services.list_projects_for_user(current_user)
    return render_template("projects/list.html", projects=projects)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        try:
            project = services.create_project(
                current_user, form.name.data, form.key.data, form.description.data
            )
        except PlanLimitError as error:
            flash(str(error), "warning")
            return redirect(url_for("billing.plans"))
        except ValueError as error:
            form.key.errors.append(str(error))
        else:
            flash(f"Project {project.name} created.", "success")
            return redirect(url_for("projects.project_detail", key=project.key))
    return render_template("projects/create.html", form=form)


@bp.get("/<key>")
@login_required
def project_detail(key):
    from app.modules.issues import services as issue_services

    project = get_project_or_abort(key)
    return render_template(
        "projects/detail.html",
        project=project,
        status_counts=issue_services.count_by_status(project),
        recent_issues=issue_services.list_issues(project)[:5],
        can_manage=services.user_can_manage(current_user, project),
    )


@bp.post("/<key>/members")
@login_required
def add_member(key):
    project = get_project_or_abort(key)
    try:
        user = services.add_member(project, current_user, request.form.get("email"))
    except (ValueError, LookupError, PermissionError) as error:
        flash(str(error.args[0] if error.args else error), "danger")
    else:
        flash(f"{user.name} added to {project.name}.", "success")
    return redirect(url_for("projects.project_detail", key=project.key))


@bp.post("/<key>/archive")
@login_required
def archive_project(key):
    project = get_project_or_abort(key)
    try:
        services.archive_project(project, current_user)
    except PermissionError as error:
        flash(str(error), "danger")
        return redirect(url_for("projects.project_detail", key=project.key))
    flash(f"Project {project.name} archived.", "info")
    return redirect(url_for("projects.list_projects"))
