"""Command line arguments put in a shape that every supported Python's argparse reads alike."""

from __future__ import annotations

import argparse
import re
from collections.abc import Sequence
from typing import Any

# Python 3.14 reads any argument that starts like a negative number as a positional; earlier
# versions only whole numbers and decimals. The newest rule is applied on every version.
_NUMBER = re.compile(r"-\.?\d")


class Escaped(str):
    """An argument argparse must read as a positional, kept as the caller wrote it."""

    original: str

    def __new__(cls, original: str) -> Escaped:
        # No leading dash, so argparse never takes it for an option; it never reaches output.
        self = super().__new__(cls, "\0" + original)
        self.original = original
        return self


class Mark(str):
    """Stands for the first ``--``: an unknown option to argparse, dropped from the extras."""

    def __new__(cls) -> Mark:
        return super().__new__(cls, "--\0")  # not "--", which 3.10 and 3.11 treat apart


class Value(argparse.Action):
    """Stores an option's value; Python 3.10 and 3.11 hand ``[]`` for a value of ``--``."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        if values == []:  # they drop "--" from "--step=--"; read it as later versions do
            try:
                values = self.type("--") if callable(self.type) else "--"
            except argparse.ArgumentTypeError as error:
                raise argparse.ArgumentError(self, str(error)) from None
        setattr(namespace, self.dest, values)


def plain(arg: str) -> str:
    """``arg`` as the caller wrote it."""
    return arg.original if isinstance(arg, Escaped) else arg


def prepare(argv: Sequence[str]) -> list[str]:
    """``argv`` rewritten so that every supported Python reads it as 3.14 does.

    A step such as "-P1M" is glued to its flag, which argparse would otherwise take for an
    option. After the first ``--`` every argument is START or STOP: each is wrapped, and the
    ``--`` itself becomes a :class:`Mark`, so that 3.10 and 3.11, which read ``--`` otherwise,
    agree. An argument that starts like a negative number is wrapped as well.
    """
    prepared: list[str] = []
    rest = iter(argv)
    for arg in rest:
        if arg in ("-s", "--step"):
            value = next(rest, None)
            prepared.append(arg if value is None else f"--step={value}")
        elif arg == "--":
            prepared.append(Mark())
            prepared.extend(Escaped(after) for after in rest)
        else:
            prepared.append(Escaped(arg) if _NUMBER.match(arg) else arg)
    return prepared


def settle(args: argparse.Namespace, extras: list[str]) -> list[str]:
    """Undo :func:`prepare` on the parsed ``args``: unwrap each wrapped option value, and
    return the extras without the mark.
    """
    for name, value in vars(args).items():
        if isinstance(value, Escaped):
            setattr(args, name, value.original)
    return [arg for arg in extras if not isinstance(arg, Mark)]


def late_stop(extras: list[str]) -> tuple[str | None, list[str]]:
    """STOP as Python 3.12 and later find it among ``extras``, and the extras that remain.

    When an unknown option comes before STOP, 3.10 and 3.11 fill STOP with nothing and leave
    the real one among the extras; later versions take the first positional, and so does this.
    """
    # A parser with no options decides, so an argument is read the way argparse read the rest.
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument("value", nargs="?")
    for at, arg in enumerate(extras):
        if probe.parse_known_args([arg])[0].value is not None:
            return arg, extras[:at] + extras[at + 1 :]
    return None, extras
