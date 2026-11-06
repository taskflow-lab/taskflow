from flask import current_app
from sqlalchemy import or_

from app.modules.issues.models import Issue
from app.modules.issues.services import ISSUE_KEY_RE
from app.modules.projects.models import Project
from app.modules.projects.services import list_projects_for_user

MAX_RESULTS = 100


def search_issues(user, query="", status=None, priority=None, project_key=None):
    query = (query or "").strip()
    if status and status not in current_app.config["ISSUE_STATUSES"]:
        raise ValueError(f"Unknown status '{status}'")
    if priority and priority not in current_app.config["ISSUE_PRIORITIES"]:
        raise ValueError(f"Unknown priority '{priority}'")

    project_ids = [p.id for p in list_projects_for_user(user)]
    if not project_ids:
        return []

    q = Issue.query.join(Project).filter(Issue.project_id.in_(project_ids))

    if project_key:
        q = q.filter(Project.key == project_key.upper())
    if status:
        q = q.filter(Issue.status == status)
    if priority:
        q = q.filter(Issue.priority == priority)

    if query:
        key_match = ISSUE_KEY_RE.match(query)
        if key_match:
            q = q.filter(Project.key == key_match.group(1).upper(), Issue.number == int(key_match.group(2)))
        else:
            pattern = f"%{query}%"
            q = q.filter(or_(Issue.title.ilike(pattern), Issue.description.ilike(pattern)))

    return q.order_by(Issue.updated_at.desc(), Issue.id.desc()).limit(MAX_RESULTS).all()
