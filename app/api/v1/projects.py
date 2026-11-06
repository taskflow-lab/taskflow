from flask import g, jsonify

from app.api.v1 import api_login_required, api_v1_bp, get_json_body
from app.modules.projects import services


def get_accessible_project(key):
    project = services.get_project_by_key(key)
    if not services.user_can_access(g.api_user, project):
        raise PermissionError("You do not have access to this project")
    return project


@api_v1_bp.get("/projects")
@api_login_required
def list_projects():
    projects = services.list_projects_for_user(g.api_user)
    return jsonify({"projects": [p.to_dict() for p in projects]}), 200


@api_v1_bp.post("/projects")
@api_login_required
def create_project():
    data = get_json_body()
    project = services.create_project(
        owner=g.api_user,
        name=data.get("name", ""),
        key=data.get("key", ""),
        description=data.get("description", ""),
    )
    return jsonify({"project": project.to_dict()}), 201


@api_v1_bp.get("/projects/<key>")
@api_login_required
def get_project(key):
    project = get_accessible_project(key)
    return jsonify({"project": project.to_dict()}), 200


@api_v1_bp.patch("/projects/<key>")
@api_login_required
def update_project(key):
    project = get_accessible_project(key)
    data = get_json_body()
    project = services.update_project(
        project,
        name=data.get("name"),
        description=data.get("description"),
    )
    return jsonify({"project": project.to_dict()}), 200


@api_v1_bp.post("/projects/<key>/archive")
@api_login_required
def archive_project(key):
    project = get_accessible_project(key)
    project = services.archive_project(project, g.api_user)
    return jsonify({"project": project.to_dict()}), 200
