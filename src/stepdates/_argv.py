"""Command line arguments put in a shape that every supported Python's argparse reads alike."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


class Escaped(str):
    """An argument after ``--``: START or STOP whatever it looks like, kept as ``original``."""

    original: str

    def __new__(cls, original: str) -> Escaped:
        # No leading dash, so argparse never takes it for an option; it never reaches output.
        self = super().__new__(cls, "\0" + original)
        self.original = original
        return self


def plain(arg: str) -> str:
    """``arg`` as the caller wrote it."""
    return arg.original if isinstance(arg, Escaped) else arg


def prepare(argv: Sequence[str]) -> list[str]:
    """``argv`` with each dash-led step glued to its flag and the first ``--`` resolved.

    argparse reads a step such as "-P1M" as an option, so it is glued to its flag. After the
    first ``--`` every argument is START or STOP, as Python 3.12 and later read it; each is
    wrapped so that 3.10 and 3.11, which read ``--`` otherwise, see a plain positional too.
    """
    prepared: list[str] = []
    rest = iter(argv)
    for arg in rest:
        if arg in ("-s", "--step"):
            value = next(rest, None)
            prepared.append(arg if value is None else f"--step={value}")
        elif arg == "--":
            prepared.extend(Escaped(after) for after in rest)
        else:
            prepared.append(arg)
    return prepared


def late_stop(extras: list[str]) -> tuple[str | None, list[str]]:
    """STOP as Python 3.12 and later find it among ``extras``, and the extras that remain.

    When an unknown option comes before STOP, 3.10 and 3.11 fill STOP with nothing and leave
    the real one among the extras; later versions take the first positional, and so does this.
    """
    # A parser with no options decides, so a dash-led argument such as "-5" is read the way
    # this Python's argparse read the rest of the command line.
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument("value", nargs="?")
    for at, arg in enumerate(extras):
        if probe.parse_known_args([arg])[0].value is not None:
            return arg, extras[:at] + extras[at + 1 :]
    return None, extras
