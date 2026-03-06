"""Anchor extraction helpers for code-state-aware memory features.

This module is intentionally parser-only and has no database side effects.
"""

from __future__ import annotations

import re
from typing import TypedDict


class AnchorResult(TypedDict):
    """Structured anchor extracted from free text."""

    anchor_type: str
    anchor_value: str


_WINDOWS_PATH_RE = re.compile(
    r"(?:(?:[A-Za-z]:[\\/]|\.{1,2}[\\/])"
    r"(?:[A-Za-z0-9._-]+[\\/])+"
    r"[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+)"
)

_POSIX_PREFIXED_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9._-])(?:(?:/|\./|\.\./)"
    r"(?:[A-Za-z0-9._-]+/)+"
    r"[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+)"
)

_POSIX_RELATIVE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9._/-])(?:"
    r"(?:[A-Za-z0-9_-]+/)+"
    r"[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+)"
)

_COMMIT_HASH_RE = re.compile(
    r"\b(?:(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,12}"
    r"|(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{40})\b",
    re.IGNORECASE,
)

_TOOL_RE = re.compile(
    r"(?i)(?<![\w-])("
    r"pytest|uvicorn|docker(?:-compose)?|git|pip3?|poetry|tox|nox|"
    r"ruff|mypy|black|flake8|pre-commit|npm|pnpm|yarn|node|python3?|"
    r"uv|cargo|kubectl|helm|terraform|ansible"
    r")(?![\w-])"
)

_TOOL_CANONICAL = {
    "pip3": "pip",
    "python3": "python",
}


def _clean_path(value: str) -> str:
    cleaned = value.strip()
    cleaned = cleaned.strip("`'\"")
    cleaned = cleaned.lstrip("([{<")
    cleaned = cleaned.rstrip(")]}>.,;:")
    return cleaned


def _extract_paths(text: str) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    for regex in (_WINDOWS_PATH_RE, _POSIX_PREFIXED_PATH_RE, _POSIX_RELATIVE_PATH_RE):
        for match in regex.finditer(text):
            value = _clean_path(match.group(0))
            if not value:
                continue
            if value.startswith(("http://", "https://")):
                continue
            matches.append((match.start(), value))
    return matches


def _extract_commits(text: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(0).lower()) for m in _COMMIT_HASH_RE.finditer(text)]


def _extract_tools(text: str) -> list[tuple[int, str]]:
    tools: list[tuple[int, str]] = []
    for match in _TOOL_RE.finditer(text):
        raw = match.group(1).lower()
        tools.append((match.start(), _TOOL_CANONICAL.get(raw, raw)))
    return tools


def extract_anchors(text: str) -> list[AnchorResult]:
    """Extract stable, deduplicated anchors from free text.

    Returns:
        List of anchors in first-occurrence order. Each anchor has:
        - ``anchor_type``: ``path`` | ``commit`` | ``tool``
        - ``anchor_value``: normalized anchor value
    """

    if not text:
        return []

    raw_matches: list[tuple[int, str, str]] = []
    raw_matches.extend((pos, "path", value) for pos, value in _extract_paths(text))
    raw_matches.extend((pos, "commit", value) for pos, value in _extract_commits(text))
    raw_matches.extend((pos, "tool", value) for pos, value in _extract_tools(text))

    raw_matches.sort(key=lambda item: (item[0], item[1], item[2]))

    anchors: list[AnchorResult] = []
    seen: set[tuple[str, str]] = set()
    for _, anchor_type, anchor_value in raw_matches:
        key = (anchor_type, anchor_value)
        if key in seen:
            continue
        seen.add(key)
        anchors.append({"anchor_type": anchor_type, "anchor_value": anchor_value})

    return anchors


__all__ = ["AnchorResult", "extract_anchors"]
