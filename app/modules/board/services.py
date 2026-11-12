from flask import current_app

from app.modules.issues import services as issue_services
from app.modules.issues.models import STATUS_LABELS


def get_board(project, search=None, assignee_id=None, sprint=None):
    issues = issue_services.list_issues(project, assignee_id=assignee_id)

    if sprint is not None:
        sprint_issue_ids = {issue.id for issue in sprint.issues}
        issues = [i for i in issues if i.id in sprint_issue_ids]

    if search:
        term = search.strip().lower()
        issues = [i for i in issues if term in i.title.lower() or term in i.key.lower()]

    columns = []
    for status in current_app.config["ISSUE_STATUSES"]:
        column_issues = [i for i in issues if i.status == status]
        column_issues.sort(key=lambda i: i.number)
        columns.append({"status": status, "label": STATUS_LABELS[status], "issues": column_issues})
    return columns
