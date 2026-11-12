from datetime import datetime, timezone

from app.extensions import db

SPRINT_STATUSES = ("planned", "active", "completed")


def utcnow():
    return datetime.now(timezone.utc)


# Which issues are in which sprint. A separate table (instead of a sprint_id column on issues)
# means existing databases need no migration: db.create_all() simply adds the new tables.
sprint_issues = db.Table(
    "sprint_issues",
    db.Column("sprint_id", db.Integer, db.ForeignKey("sprints.id"), primary_key=True),
    db.Column("issue_id", db.Integer, db.ForeignKey("issues.id"), primary_key=True),
)


class Sprint(db.Model):
    __tablename__ = "sprints"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    goal = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="planned", index=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    project = db.relationship("Project", backref=db.backref("sprints", lazy="dynamic"))
    issues = db.relationship("Issue", secondary=sprint_issues, order_by="Issue.number")

    @property
    def is_open(self):
        return self.status != "completed"

    def __repr__(self):
        return f"<Sprint {self.name} ({self.status})>"
