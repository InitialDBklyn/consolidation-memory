"""Shared utility helpers used across consolidation-memory modules.

Centralizes common patterns that were previously duplicated:
- JSON list parsing (tags column, source_episodes)
- ISO datetime parsing with naive-UTC normalization
"""

from __future__ import annotations

import json
from datetime import datetime, timezone


def parse_json_list(raw: str | list | None, default: list | None = None) -> list:
    """Parse a value that may be a JSON string, a list, or None.

    Used for the ``tags`` and ``source_episodes`` columns which are stored
    as JSON arrays in SQLite but may already be deserialized by the time
    they reach Python code.

    Args:
        raw: A JSON-encoded string (e.g. ``'["a","b"]'``), an already-parsed
            list, or ``None``.
        default: Value to return when *raw* is ``None`` or cannot be parsed.
            Defaults to an empty list.

    Returns:
        The parsed list, or *default* on failure / None input.
    """
    if default is None:
        default = []
    if raw is None:
        return default
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        return default
    except (json.JSONDecodeError, ValueError, TypeError):
        return default


def parse_datetime(s: str) -> datetime:
    """Parse an ISO 8601 datetime string, normalizing naive datetimes to UTC.

    SQLite stores datetimes as text and they may lack timezone info.
    This helper ensures a consistent timezone-aware result.

    Args:
        s: An ISO 8601 datetime string (e.g. ``"2025-01-15T10:30:00"``
           or ``"2025-01-15T10:30:00+00:00"``).

    Returns:
        A timezone-aware ``datetime`` in UTC.

    Raises:
        ValueError: If *s* is not a valid ISO datetime.
    """
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
