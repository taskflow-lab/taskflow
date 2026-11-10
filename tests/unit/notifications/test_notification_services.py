import pytest

from app.extensions import db
from app.modules.notifications import services


@pytest.fixture
def notify(app, user):
    def _notify(message="Something happened", target=None, link=None):
        notification = services.notify((target or user).id, message, link=link)
        db.session.commit()
        return notification

    return _notify


def test_notify_creates_unread_notification(app, user, notify):
    notification = notify("You were assigned WEB-1", link="/issues/WEB-1")

    assert notification.is_read is False
    assert notification.link == "/issues/WEB-1"
    assert services.unread_count(user) == 1


def test_notify_truncates_long_messages(app, notify):
    notification = notify("x" * 500)
    assert len(notification.message) == 300


def test_unread_count_only_counts_own_notifications(app, user, other_user, notify):
    notify(target=user)
    notify(target=other_user)
    notify(target=other_user)

    assert services.unread_count(user) == 1
    assert services.unread_count(other_user) == 2


def test_list_newest_first(app, user, notify):
    notify("first")
    notify("second")
    notify("third")

    messages = [n.message for n in services.list_for_user(user)]
    assert messages == ["third", "second", "first"]


def test_list_respects_limit(app, user, notify):
    for i in range(5):
        notify(f"message {i}")
    assert len(services.list_for_user(user, limit=3)) == 3


def test_list_unread_only(app, user, notify):
    read = notify("read me")
    notify("still unread")
    services.mark_read(user, read.id)

    assert [n.message for n in services.list_for_user(user, unread_only=True)] == ["still unread"]


def test_mark_read(app, user, notify):
    notification = notify()
    services.mark_read(user, notification.id)

    assert notification.is_read is True
    assert services.unread_count(user) == 0


def test_cannot_mark_someone_elses_notification(app, user, other_user, notify):
    notification = notify(target=other_user)

    with pytest.raises(LookupError):
        services.mark_read(user, notification.id)
    assert notification.is_read is False


def test_mark_read_unknown_id(app, user):
    with pytest.raises(LookupError):
        services.mark_read(user, 9999)


def test_mark_all_read_returns_count_and_only_touches_own(app, user, other_user, notify):
    notify(target=user)
    notify(target=user)
    notify(target=other_user)

    assert services.mark_all_read(user) == 2
    assert services.unread_count(user) == 0
    assert services.unread_count(other_user) == 1
