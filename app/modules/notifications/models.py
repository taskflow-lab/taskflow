from datetime import datetime, timezone

from app.extensions import db

from app.utils import iso_utc
def utcnow():
    return datetime.now(timezone.utc)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.String(300), nullable=False)
    link = db.Column(db.String(300), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "link": self.link,
            "is_read": self.is_read,
            "created_at": iso_utc(self.created_at),
        }
