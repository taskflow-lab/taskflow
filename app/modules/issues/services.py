import re
from datetime import date

from flask import current_app
from sqlalchemy import func

from app.extensions import db
from app.modules.auth.models import User
from app.modules.issues.models import STATUS_LABELS, Comment, Issue
from app.modules.notifications import services as notifications
from app.modules.projects.models import Project
from app.modules.projects.services import user_can_access

ISSUE_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9]{1,9})-(\d+)$")


def _check_choice(value, option_name, label):
    options = current_app.config[option_name]
    if value not in options:
        raise ValueError(f"{label} must be one of: {', '.join(options)}")
    return value


def _parse_due_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValueError("Due date must be in YYYY-MM-DD format") from None


def _resolve_assignee(project, assignee_id):
    if assignee_id in (None, "", 0):
        return None
    try:
        assignee_id = int(assignee_id)
    except (TypeError, ValueError):
        raise ValueError("Assignee must be a user id") from None
    user = db.session.get(User, assignee_id)
    if user is None or not user_can_access(user, project):
        raise ValueError("Assignee must be a member of the project")
    return user


def _validate_title(title):
    title = (title or "").strip()
    if not title:
        raise ValueError("Title is required")
    if len(title) > 200:
        raise ValueError("Title must be 200 characters or fewer")
    return title


def _notify_people(issue, actor, message):
    recipients = {issue.reporter_id, issue.assignee_id} - {None, actor.id}
    for user_id in recipients:
        notifications.notify(user_id, message, link=f"/issues/{issue.key}")


def get_issue_by_key(issue_key):
    match = ISSUE_KEY_RE.match((issue_key or "").strip())
    if not match:
        raise LookupError(f"Issue '{issue_key}' not found")
    project_key, number = match.group(1).upper(), int(match.group(2))
    issue = (
        Issue.query.join(Project)
        .filter(Project.key == project_key, Issue.number == number)
        .first()
    )
    if issue is None:
        raise LookupError(f"Issue '{issue_key}' not found")
    return issue


def list_issues(project, status=None, priority=None, assignee_id=None):
    query = Issue.query.filter_by(project_id=project.id)
    if status:
        query = query.filter_by(status=_check_choice(status, "ISSUE_STATUSES", "Status"))
    if priority:
        query = query.filter_by(priority=_check_choice(priority, "ISSUE_PRIORITIES", "Priority"))
    if assignee_id:
        query = query.filter_by(assignee_id=assignee_id)
    return query.order_by(Issue.created_at.desc(), Issue.id.desc()).all()


def count_by_status(project):
    rows = dict(
        db.session.query(Issue.status, func.count(Issue.id))
        .filter(Issue.project_id == project.id)
        .group_by(Issue.status)
        .all()
    )
    return [(status, STATUS_LABELS[status], rows.get(status, 0)) for status in current_app.config["ISSUE_STATUSES"]]


def create_issue(project, reporter, title, description="", issue_type="task",
                 priority="medium", assignee_id=None, due_date=None):
    if project.is_archived:
        raise ValueError("Cannot add issues to an archived project")

    title = _validate_title(title)
    _check_choice(issue_type, "ISSUE_TYPES", "Type")
    _check_choice(priority, "ISSUE_PRIORITIES", "Priority")
    assignee = _resolve_assignee(project, assignee_id)

    project.issue_counter += 1
    issue = Issue(
        project_id=project.id,
        number=project.issue_counter,
        title=title,
        description=(description or "").strip(),
        issue_type=issue_type,
        priority=priority,
        reporter_id=reporter.id,
        assignee_id=assignee.id if assignee else None,
        due_date=_parse_due_date(due_date),
    )
    db.session.add(issue)
    db.session.flush()

    if assignee and assignee.id != reporter.id:
        notifications.notify(
            assignee.id, f"{reporter.name} assigned you {issue.key}: {issue.title}", link=f"/issues/{issue.key}"
        )
    db.session.commit()
    return issue


def update_issue(issue, actor, **changes):
    previous_assignee = issue.assignee_id

    if "title" in changes:
        issue.title = _validate_title(changes["title"])
    if "description" in changes:
        issue.description = (changes["description"] or "").strip()
    if "priority" in changes:
        issue.priority = _check_choice(changes["priority"], "ISSUE_PRIORITIES", "Priority")
    if "type" in changes:
        issue.issue_type = _check_choice(changes["type"], "ISSUE_TYPES", "Type")
    if "due_date" in changes:
        issue.due_date = _parse_due_date(changes["due_date"])
    if "assignee_id" in changes:
        assignee = _resolve_assignee(issue.project, changes["assignee_id"])
        issue.assignee_id = assignee.id if assignee else None

    if issue.assignee_id and issue.assignee_id != previous_assignee and issue.assignee_id != actor.id:
        notifications.notify(
            issue.assignee_id, f"{actor.name} assigned you {issue.key}: {issue.title}", link=f"/issues/{issue.key}"
        )
    db.session.commit()
    return issue


def change_status(issue, new_status, actor):
    _check_choice(new_status, "ISSUE_STATUSES", "Status")
    if issue.status == new_status:
        return issue
    issue.status = new_status
    _notify_people(issue, actor, f"{actor.name} moved {issue.key} to {issue.status_label}")
    db.session.commit()
    return issue


def add_comment(issue, author, body):
    body = (body or "").strip()
    if not body:
        raise ValueError("Comment cannot be empty")
    comment = Comment(issue_id=issue.id, author_id=author.id, body=body)
    db.session.add(comment)
    _notify_people(issue, author, f"{author.name} commented on {issue.key}")
    db.session.commit()
    return comment
