from datetime import datetime, timedelta, timezone

import pytest

from app.utils import iso_utc


@pytest.mark.parametrize(
    "value, expected",
    [
        (datetime(2026, 11, 10, 15, 59, 54), "2026-11-10T15:59:54Z"),
        (datetime(2026, 11, 10, 15, 59, 54, tzinfo=timezone.utc), "2026-11-10T15:59:54Z"),
        (datetime(2026, 11, 10, 21, 29, 54, tzinfo=timezone(timedelta(hours=5, minutes=30))), "2026-11-10T15:59:54Z"),
        (None, None),
    ],
)
def test_iso_utc(value, expected):
    assert iso_utc(value) == expected
