"""Utilities for normalizing genre values."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List


def normalize_genre_value(value: object) -> str:
    """Normalize a genre string to slash-separated values."""
    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    text = re.sub(r"\s*,\s*", "/", text)
    text = re.sub(r"\s*/\s*", "/", text)
    text = re.sub(r"/{2,}", "/", text)
    return text.strip(" /")


def normalize_genre_row(row: Dict[str, object]) -> bool:
    """Normalize the Genre field on a CSV row in place.

    Returns True when the value changed.
    """
    if "Genre" not in row:
        return False

    original = row.get("Genre", "")
    normalized = normalize_genre_value(original)
    if str(original).strip() != normalized:
        row["Genre"] = normalized
        return True
    return False


def audit_genre_separators(rows: Iterable[Dict[str, object]]) -> List[str]:
    """Return artist names whose genre values still use comma separators."""
    offenders: List[str] = []
    for row in rows:
        genre = str(row.get("Genre", "") or "").strip()
        if genre and "," in genre:
            offenders.append(str(row.get("Artist", "") or "").strip() or "<unknown>")
    return offenders