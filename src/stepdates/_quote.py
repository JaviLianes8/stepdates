"""Short, safe quoting of caller input inside error messages."""

from __future__ import annotations

LIMIT = 80


def quote(value: object) -> str:
    """``repr`` of ``value``, cut to ``LIMIT`` characters so a huge input stays out of messages."""
    if isinstance(value, str) and len(value) > LIMIT:
        return f"{value[:LIMIT]!r}... ({len(value)} characters)"
    text = repr(value)
    return text if len(text) <= LIMIT else f"{text[:LIMIT]}... ({type(value).__name__})"
