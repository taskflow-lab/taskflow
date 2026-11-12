from flask import Blueprint, render_template, request
from flask_login import login_required

from app.modules.board import services
from app.modules.projects.routes import get_project_or_abort
from app.modules.sprints import services as sprint_services

bp = Blueprint("board", __name__)


@bp.get("/projects/<key>/board")
@login_required
def view_board(key):
    project = get_project_or_abort(key)
    search = request.args.get("q", "").strip()
    assignee_id = request.args.get("assignee_id", type=int) or None
    sprint = sprint_services.get_active_sprint(project)
    columns = services.get_board(project, search=search or None, assignee_id=assignee_id, sprint=sprint)
    return render_template(
        "board/board.html",
        project=project,
        columns=columns,
        search=search,
        assignee_id=assignee_id,
        sprint=sprint,
        days_left=sprint_services.days_left(sprint) if sprint else None,
    )
