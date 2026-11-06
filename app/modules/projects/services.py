import re

from sqlalchemy import or_

from app.extensions import db
from app.modules.auth.models import User
from app.modules.billing import services as billing_services
from app.modules.projects.models import Project, project_members

KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")


def validate_project(name, key):
    if not name:
        raise ValueError("Project name is required")
    if len(name) > 120:
        raise ValueError("Project name must be 120 characters or fewer")
    if not KEY_RE.match(key):
        raise ValueError("Project key must be 2-10 characters: letters and numbers, starting with a letter")


def count_active_owned_projects(user):
    return Project.query.filter_by(owner_id=user.id, is_archived=False).count()


def list_projects_for_user(user, include_archived=False):
    query = Project.query.outerjoin(project_members).filter(
        or_(Project.owner_id == user.id, project_members.c.user_id == user.id)
    )
    if not include_archived:
        query = query.filter(Project.is_archived.is_(False))
    return query.distinct().order_by(Project.name).all()


def create_project(owner, name, key, description=""):
    name = (name or "").strip()
    key = (key or "").strip().upper()
    validate_project(name, key)

    if Project.query.filter_by(key=key).first():
        raise ValueError(f"Project key '{key}' is already taken")

    billing_services.check_project_limit(owner, count_active_owned_projects(owner))

    project = Project(name=name, key=key, description=(description or "").strip(), owner_id=owner.id)
    project.members.append(owner)
    db.session.add(project)
    db.session.commit()
    return project


def get_project_by_key(key):
    project = Project.query.filter_by(key=(key or "").upper()).first()
    if project is None:
        raise LookupError(f"Project '{key}' not found")
    return project


def user_can_access(user, project):
    if user is None:
        return False
    return user.is_admin or project.owner_id == user.id or user in project.members


def user_can_manage(user, project):
    return user.is_admin or project.owner_id == user.id


def update_project(project, name=None, description=None):
    if name is not None:
        name = name.strip()
        validate_project(name, project.key)
        project.name = name
    if description is not None:
        project.description = description.strip()
    db.session.commit()
    return project


def archive_project(project, user):
    if not user_can_manage(user, project):
        raise PermissionError("Only the project owner can archive this project")
    project.is_archived = True
    db.session.commit()
    return project


def add_member(project, actor, email):
    if not user_can_manage(actor, project):
        raise PermissionError("Only the project owner can add members")
    user = User.query.filter_by(email=(email or "").strip().lower()).first()
    if user is None:
        raise LookupError(f"No user with email '{email}'")
    if user in project.members:
        raise ValueError(f"{user.name} is already a member")
    project.members.append(user)
    db.session.commit()
    return user


def remove_member(project, actor, user_id):
    if not user_can_manage(actor, project):
        raise PermissionError("Only the project owner can remove members")
    if user_id == project.owner_id:
        raise ValueError("The project owner cannot be removed")
    user = db.session.get(User, user_id)
    if user is None or user not in project.members:
        raise LookupError("Member not found")
    project.members.remove(user)
    db.session.commit()
    return user
