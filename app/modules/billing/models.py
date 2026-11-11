from datetime import datetime, timezone

from app.extensions import db
from app.utils import iso_utc

def utcnow():
    return datetime.now(timezone.utc)


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    plan = db.Column(db.String(20), nullable=False, default="free")
    status = db.Column(db.String(20), nullable=False, default="active")
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", backref=db.backref("subscription", uselist=False))

    def to_dict(self):
        return {
            "plan": self.plan,
            "status": self.status,
            "updated_at": iso_utc(self.updated_at),
        }


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="USD")
    status = db.Column(db.String(20), nullable=False, default="succeeded")
    is_mock = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plan": self.plan,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "mock": self.is_mock,
            "created_at": self.created_at.isoformat(),
        }
