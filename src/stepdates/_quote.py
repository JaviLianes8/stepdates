"""Short, safe quoting of caller input inside error messages."""

from __future__ import annotations

LIMIT = 80


def quote(value: str) -> str:
    """``repr`` of ``value``, cut to ``LIMIT`` characters so a huge input stays out of messages."""
    text = repr(value[:LIMIT])
    if len(text) > LIMIT:  # escapes such as \t or \U0001f600 make the repr longer
        text = text[:LIMIT] + "..."
    elif len(value) > LIMIT:
        text += "..."
    return text if len(value) <= LIMIT else f"{text} ({len(value)} characters)"
