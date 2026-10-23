"""Short, safe quoting of caller input inside error messages."""

from __future__ import annotations

import ast
import re
import warnings
from collections.abc import Sequence
from gettext import gettext

LIMIT = 80
MESSAGE_LIMIT = 500
SHOWN = 3

# The one argparse message that echoes a refused argument raw (unrecognized arguments are
# listed by the tool itself); every other one uses repr(), which _REPR finds.
_AMBIGUOUS = "ambiguous option: %(option)s could match %(matches)s"
_REPR = re.compile(r"""'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*\"""")


def quote(value: str) -> str:
    """``repr`` of ``value`` in at most ``LIMIT`` characters between its quotes.

    A value that does not fit is cut between two of its characters, never inside an escape
    such as ``\\t``, and followed by its length.
    """
    shown = value[:LIMIT]
    text = repr(shown)
    while len(text) > LIMIT + 2:  # escapes make the repr longer than the value
        shown = shown[:-1]
        text = repr(shown)
    return text if len(shown) == len(value) else f"{text}... ({len(value)} characters)"


def listing(values: Sequence[str]) -> str:
    """The first ``SHOWN`` of ``values`` as argparse lists them, a long or odd one quoted."""
    names = [v if len(v) <= LIMIT and v.isprintable() else quote(v) for v in values[:SHOWN]]
    rest = len(values) - SHOWN
    return " ".join(names) + (f" and {rest} more" if rest > 0 else "")


def bound(message: str) -> str:
    """``message`` with control characters escaped, cut to ``MESSAGE_LIMIT`` characters."""
    pieces: list[str] = []
    size = 0
    for char in message:
        piece = char if char.isprintable() else repr(char)[1:-1]
        size += len(piece)
        if size > MESSAGE_LIMIT:
            return "".join(pieces) + f"... ({len(message)} characters)"
        pieces.append(piece)
    return "".join(pieces)


def scrub(message: str) -> str:
    """An argparse error ``message`` with every argument it echoes held to :func:`quote`.

    One pass over the message, so the time is linear in its length whatever the arguments.
    """
    head, _, rest = gettext(_AMBIGUOUS).partition("%(option)s")
    tail = rest.partition("%(matches)s")[0]
    if head and tail and message.startswith(head) and tail in message:
        option, _, matches = message[len(head) :].rpartition(tail)
        if len(option) > LIMIT:
            message = f"{head}{quote(option)}{tail}{matches}"
    return bound(_REPR.sub(_short, message))


def _short(match: re.Match[str]) -> str:
    text = match.group()
    if len(text) <= LIMIT + 2:
        return text
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            value = ast.literal_eval(text)
    except (SyntaxError, ValueError, MemoryError, RecursionError):
        value = text
    return quote(value if isinstance(value, str) else text)
