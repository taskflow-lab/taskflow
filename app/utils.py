from datetime import timezone


def iso_utc(value):
    """Format a datetime for the API as UTC with a 'Z', e.g. 2026-11-10T15:59:54.159279Z.

    SQLite drops timezone info when it stores datetimes, so values read back are "naive".
    We always store UTC, so a naive value is treated as UTC.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
