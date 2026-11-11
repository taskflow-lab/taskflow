from datetime import datetime, timezone

from app.extensions import db
from app.utils import iso_utc


def utcnow():
    return datetime.now(timezone.utc)


project_members = db.Table(
    "project_members",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    issue_counter = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    owner = db.relationship("User", foreign_keys=[owner_id])
    members = db.relationship("User", secondary=project_members, lazy="select", order_by="User.name")

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "owner": {"id": self.owner.id, "name": self.owner.name},
            "members": [{"id": m.id, "name": m.name, "email": m.email} for m in self.members],
            "is_archived": self.is_archived,
            "created_at": iso_utc(self.created_at),
        }

    def __repr__(self):
        return f"<Project {self.key}>"
