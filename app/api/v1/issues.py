from flask import g, jsonify, request

from app.api.v1 import api_login_required, api_v1_bp, get_json_body
from app.api.v1.projects import get_accessible_project
from app.modules.issues import services
from app.modules.projects.services import user_can_access


def get_accessible_issue(issue_key):
    issue = services.get_issue_by_key(issue_key)
    if not user_can_access(g.api_user, issue.project):
        raise PermissionError("You do not have access to this issue")
    return issue


@api_v1_bp.get("/projects/<key>/issues")
@api_login_required
def list_issues(key):
    project = get_accessible_project(key)
    issues = services.list_issues(
        project,
        status=request.args.get("status"),
        priority=request.args.get("priority"),
        assignee_id=request.args.get("assignee_id", type=int),
    )
    return jsonify({"issues": [i.to_dict() for i in issues]}), 200


@api_v1_bp.post("/projects/<key>/issues")
@api_login_required
def create_issue(key):
    project = get_accessible_project(key)
    data = get_json_body()
    issue = services.create_issue(
        project=project,
        reporter=g.api_user,
        title=data.get("title", ""),
        description=data.get("description", ""),
        issue_type=data.get("type", "task"),
        priority=data.get("priority", "medium"),
        assignee_id=data.get("assignee_id"),
        due_date=data.get("due_date"),
    )
    return jsonify({"issue": issue.to_dict()}), 201


@api_v1_bp.get("/issues/<issue_key>")
@api_login_required
def get_issue(issue_key):
    issue = get_accessible_issue(issue_key)
    return jsonify({"issue": issue.to_dict()}), 200


@api_v1_bp.patch("/issues/<issue_key>")
@api_login_required
def update_issue(issue_key):
    issue = get_accessible_issue(issue_key)
    data = get_json_body()
    allowed = {"title", "description", "priority", "type", "assignee_id", "due_date"}
    changes = {k: v for k, v in data.items() if k in allowed}
    issue = services.update_issue(issue, g.api_user, **changes)
    return jsonify({"issue": issue.to_dict()}), 200


@api_v1_bp.post("/issues/<issue_key>/transition")
@api_login_required
def transition_issue(issue_key):
    issue = get_accessible_issue(issue_key)
    data = get_json_body()
    issue = services.change_status(issue, data.get("status", ""), g.api_user)
    return jsonify({"issue": issue.to_dict()}), 200


@api_v1_bp.get("/issues/<issue_key>/comments")
@api_login_required
def list_comments(issue_key):
    issue = get_accessible_issue(issue_key)
    return jsonify({"comments": [c.to_dict() for c in issue.comments]}), 200


@api_v1_bp.post("/issues/<issue_key>/comments")
@api_login_required
def add_comment(issue_key):
    issue = get_accessible_issue(issue_key)
    data = get_json_body()
    comment = services.add_comment(issue, g.api_user, data.get("body", ""))
    return jsonify({"comment": comment.to_dict()}), 201
