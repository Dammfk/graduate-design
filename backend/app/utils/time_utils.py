from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


DISPLAY_TIMEZONE = ZoneInfo("Asia/Shanghai")


def get_display_time(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(DISPLAY_TIMEZONE)


def to_display_iso(value: datetime | None) -> str | None:
    display_value = get_display_time(value)
    return display_value.isoformat() if display_value else None


def get_display_now() -> datetime:
    return datetime.now(DISPLAY_TIMEZONE)
