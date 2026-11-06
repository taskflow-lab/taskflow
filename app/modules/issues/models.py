from datetime import datetime, timezone

from app.extensions import db

STATUS_LABELS = {
    "todo": "To Do",
    "in_progress": "In Progress",
    "in_review": "In Review",
    "done": "Done",
}


def utcnow():
    return datetime.now(timezone.utc)


class Issue(db.Model):
    __tablename__ = "issues"
    __table_args__ = (db.UniqueConstraint("project_id", "number", name="uq_issue_project_number"),)

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    issue_type = db.Column(db.String(20), nullable=False, default="task")
    priority = db.Column(db.String(20), nullable=False, default="medium")
    status = db.Column(db.String(20), nullable=False, default="todo", index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    project = db.relationship("Project", backref=db.backref("issues", lazy="dynamic"))
    reporter = db.relationship("User", foreign_keys=[reporter_id])
    assignee = db.relationship("User", foreign_keys=[assignee_id])
    comments = db.relationship(
        "Comment", backref="issue", order_by="Comment.created_at", cascade="all, delete-orphan"
    )

    @property
    def key(self):
        return f"{self.project.key}-{self.number}"

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "project_key": self.project.key,
            "title": self.title,
            "description": self.description,
            "type": self.issue_type,
            "priority": self.priority,
            "status": self.status,
            "reporter": {"id": self.reporter.id, "name": self.reporter.name},
            "assignee": {"id": self.assignee.id, "name": self.assignee.name} if self.assignee else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "comment_count": len(self.comments),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Issue {self.key}>"


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    author = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "author": {"id": self.author.id, "name": self.author.name},
            "body": self.body,
            "created_at": self.created_at.isoformat(),
        }
