from flask import Blueprint, current_app, flash, render_template, request
from flask_login import current_user, login_required

from app.modules.issues.models import STATUS_LABELS
from app.modules.projects.services import list_projects_for_user
from app.modules.search import services

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.get("/")
@login_required
def search():
    params = {
        "query": request.args.get("q", "").strip(),
        "status": request.args.get("status") or None,
        "priority": request.args.get("priority") or None,
        "project_key": request.args.get("project") or None,
    }
    has_filters = any(params.values())
    results = []
    if has_filters:
        try:
            results = services.search_issues(current_user, **params)
        except ValueError as error:
            flash(str(error), "danger")

    return render_template(
        "search/results.html",
        params=params,
        results=results,
        has_filters=has_filters,
        projects=list_projects_for_user(current_user),
        status_labels=STATUS_LABELS,
        priorities=current_app.config["ISSUE_PRIORITIES"],
    )
