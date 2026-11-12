from datetime import date, datetime, timedelta, timezone

from app.extensions import db
from app.modules.issues.models import Issue
from app.modules.sprints.models import Sprint, sprint_issues

MAX_NAME_LENGTH = 100
ALLOWED_WEEKS = (1, 2, 3, 4)
DEFAULT_WEEKS = 2


# ---------- lookups ----------

def get_sprint(sprint_id):
    sprint = db.session.get(Sprint, sprint_id)
    if sprint is None:
        raise LookupError("Sprint not found")
    return sprint


def get_active_sprint(project):
    return Sprint.query.filter_by(project_id=project.id, status="active").first()


def list_open_sprints(project):
    """Active sprint first, then planned sprints in the order they were created."""
    sprints = Sprint.query.filter(Sprint.project_id == project.id, Sprint.status != "completed").all()
    return sorted(sprints, key=lambda s: (s.status != "active", s.id))


def open_sprint_for_issue(issue):
    return (
        Sprint.query.join(sprint_issues)
        .filter(sprint_issues.c.issue_id == issue.id, Sprint.status != "completed")
        .first()
    )


def get_backlog(project):
    """Unfinished issues that are not in a planned or active sprint."""
    in_open_sprint = (
        db.session.query(sprint_issues.c.issue_id)
        .join(Sprint, Sprint.id == sprint_issues.c.sprint_id)
        .filter(Sprint.project_id == project.id, Sprint.status != "completed")
    )
    return (
        Issue.query.filter(
            Issue.project_id == project.id,
            Issue.status != "done",
            Issue.id.not_in(in_open_sprint),
        )
        .order_by(Issue.number)
        .all()
    )


def days_left(sprint, today=None):
    if sprint.status != "active" or sprint.end_date is None:
        return None
    today = today or date.today()
    return max((sprint.end_date - today).days, 0)


# ---------- changes ----------

def create_sprint(project, name=None, goal=""):
    if project.is_archived:
        raise ValueError("Cannot plan sprints in an archived project")

    name = (name or "").strip() or f"{project.key} Sprint {project.sprints.count() + 1}"
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Sprint name must be {MAX_NAME_LENGTH} characters or fewer")

    sprint = Sprint(project_id=project.id, name=name, goal=(goal or "").strip())
    db.session.add(sprint)
    db.session.commit()
    return sprint


def _ensure_open(sprint):
    if sprint.status == "completed":
        raise ValueError("A completed sprint cannot be changed")


def add_issue(sprint, issue):
    """Put an issue in the sprint. If it is in another open sprint, it moves."""
    _ensure_open(sprint)
    if issue.project_id != sprint.project_id:
        raise ValueError("The issue belongs to a different project")
    if issue.status == "done":
        raise ValueError(f"{issue.key} is already done")

    current = open_sprint_for_issue(issue)
    if current is sprint:
        return sprint
    if current is not None:
        current.issues.remove(issue)

    sprint.issues.append(issue)
    db.session.commit()
    return sprint


def remove_issue(sprint, issue):
    """Send an issue back to the backlog."""
    _ensure_open(sprint)
    if issue not in sprint.issues:
        raise LookupError(f"{issue.key} is not in {sprint.name}")
    sprint.issues.remove(issue)
    db.session.commit()
    return sprint


def start_sprint(sprint, weeks=DEFAULT_WEEKS, today=None):
    if sprint.status != "planned":
        raise ValueError("Only a planned sprint can be started")

    active = get_active_sprint(sprint.project)
    if active is not None:
        raise ValueError(f"Complete {active.name} before starting another sprint")
    if not sprint.issues:
        raise ValueError("Add at least one issue before starting the sprint")

    try:
        weeks = int(weeks)
    except (TypeError, ValueError):
        raise ValueError("Sprint length must be a number of weeks") from None
    if weeks not in ALLOWED_WEEKS:
        raise ValueError("Sprint length must be 1 to 4 weeks")

    today = today or date.today()
    sprint.status = "active"
    sprint.start_date = today
    sprint.end_date = today + timedelta(weeks=weeks)
    db.session.commit()
    return sprint


def complete_sprint(sprint):
    """Close the sprint. Unfinished issues automatically return to the backlog."""
    if sprint.status != "active":
        raise ValueError("Only the active sprint can be completed")

    done = sum(1 for issue in sprint.issues if issue.status == "done")
    unfinished = len(sprint.issues) - done

    sprint.status = "completed"
    sprint.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return {"done": done, "unfinished": unfinished}
