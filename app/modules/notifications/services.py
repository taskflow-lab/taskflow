from app.extensions import db
from app.modules.notifications.models import Notification


def notify(user_id, message, link=None):
    """Queue a notification. The caller's transaction commits it."""
    notification = Notification(user_id=user_id, message=message[:300], link=link)
    db.session.add(notification)
    return notification


def unread_count(user):
    return Notification.query.filter_by(user_id=user.id, is_read=False).count()


def list_for_user(user, unread_only=False, limit=50):
    query = Notification.query.filter_by(user_id=user.id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()


def mark_read(user, notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=user.id).first()
    if notification is None:
        raise LookupError("Notification not found")
    notification.is_read = True
    db.session.commit()
    return notification


def mark_all_read(user):
    updated = Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return updated
