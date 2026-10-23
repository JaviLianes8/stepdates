"""Short, safe quoting of caller input inside error messages."""

from __future__ import annotations

from collections.abc import Sequence

LIMIT = 80


def quote(value: str) -> str:
    """``repr`` of ``value``, cut to ``LIMIT`` characters so a huge input stays out of messages."""
    text = repr(value[:LIMIT])
    if len(text) > LIMIT + 2:  # escapes such as \t or \U0001f600 make the repr longer
        text = text[: LIMIT + 1] + "..."
    elif len(value) > LIMIT:
        text += "..."
    return text if len(value) <= LIMIT else f"{text} ({len(value)} characters)"


def scrub(message: str, args: Sequence[str]) -> str:
    """``message`` with each long argument in ``args`` quoted and control characters escaped.

    argparse writes the arguments it refuses into its messages whole; this bounds them as
    :func:`quote` bounds the library's own messages.
    """
    parts = {part for arg in args for part in (arg, arg.partition("=")[2]) if len(part) > LIMIT}
    for part in sorted(parts, key=len, reverse=True):
        message = message.replace(repr(part), quote(part)).replace(part, quote(part))
    return "".join(c if c.isprintable() else repr(c)[1:-1] for c in message)
