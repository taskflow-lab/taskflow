from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.modules.notifications import services

bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@bp.get("/")
@login_required
def list_notifications():
    unread_only = request.args.get("filter") == "unread"
    return render_template(
        "notifications/list.html",
        notifications=services.list_for_user(current_user, unread_only=unread_only),
        unread_only=unread_only,
    )


@bp.post("/<int:notification_id>/open")
@login_required
def open_notification(notification_id):
    try:
        notification = services.mark_read(current_user, notification_id)
    except LookupError:
        abort(404)
    return redirect(notification.link or url_for("notifications.list_notifications"))


@bp.post("/read-all")
@login_required
def mark_all_read():
    count = services.mark_all_read(current_user)
    flash(f"Marked {count} notification{'s' if count != 1 else ''} as read.", "info")
    return redirect(url_for("notifications.list_notifications"))
