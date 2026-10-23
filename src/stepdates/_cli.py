"""Command line tool: print a date range, one value per line."""

from __future__ import annotations

import argparse
import errno
import os
import re
import sys
from collections.abc import Sequence
from datetime import date, datetime
from typing import NoReturn

from stepdates import __version__
from stepdates._quote import quote, scrub
from stepdates._range import date_range
from stepdates._step import MAX_DIGITS

_COUNT = re.compile(rf"[+-]?[0-9]{{1,{MAX_DIGITS}}}")


def _when(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"not an ISO 8601 date or datetime: {quote(text)}"
        ) from None


def _count(text: str) -> int:
    if not _COUNT.fullmatch(text):
        raise argparse.ArgumentTypeError(
            f"not a whole number of at most {MAX_DIGITS} digits: {quote(text)}"
        )
    return int(text)


def _join_negative_steps(argv: Sequence[str]) -> list[str]:
    # argparse reads "-P1M" as an option; glue a dash-led step value to its flag.
    joined: list[str] = []
    rest = iter(argv)
    for arg in rest:
        if arg in ("-s", "--step"):
            value = next(rest, None)
            joined.append(arg if value is None else f"--step={value}")
        else:
            joined.append(arg)
    return joined


class _Parser(argparse.ArgumentParser):
    args: Sequence[str] = ()

    def error(self, message: str) -> NoReturn:
        super().error(scrub(message, self.args))


def _parser() -> _Parser:
    parser = _Parser(
        prog="stepdates",
        description="Print dates from START by a calendar step, one per line.",
        epilog='Example: stepdates 2026-01-31 --count 3 --step "1 month"',
    )
    parser.add_argument("start", type=_when, help="first value, YYYY-MM-DD or a datetime")
    parser.add_argument("stop", type=_when, nargs="?", help="end value (excluded by default)")
    parser.add_argument("-n", "--count", type=_count, help="how many values, instead of STOP")
    parser.add_argument(
        "-s", "--step", default="day", help='"day", "2 weeks", "-1 month", "P3M" (default: day)'
    )
    parser.add_argument("--inclusive", action="store_true", help="include STOP when reached")
    parser.add_argument(
        "--skip-invalid", action="store_true", help="drop days a month lacks instead of clamping"
    )
    parser.add_argument(
        "--end-of-month", action="store_true", help="keep a month-end START on month ends"
    )
    parser.add_argument("-f", "--format", help="strftime format (default: ISO 8601)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _output_encoding() -> tuple[str, str]:
    stdout = sys.stdout
    return getattr(stdout, "encoding", None) or "utf-8", getattr(stdout, "errors", None) or "strict"


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for ``stepdates`` and ``python -m stepdates``; returns the exit code."""
    parser = _parser()
    parser.args = _join_negative_steps(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(parser.args)
    if args.format:
        try:  # UnicodeEncodeError is a ValueError: the output must be able to hold the text
            sample = args.start.strftime(args.format)
            sample.encode(*_output_encoding())
        except ValueError as error:
            parser.error(f"invalid --format {quote(args.format)}: {error}")
    try:
        values = date_range(
            args.start,
            args.stop,
            step=args.step,
            count=args.count,
            inclusive=args.inclusive,
            invalid="skip" if args.skip_invalid else "clamp",
            end_of_month=args.end_of_month,
        )
    except (TypeError, ValueError) as error:
        parser.error(str(error))
    try:
        for value in values:
            text = value.strftime(args.format) if args.format else value.isoformat()
            sys.stdout.write(text + "\n")
        sys.stdout.flush()
    except UnicodeEncodeError as error:
        # A value the --format check could not foresee, such as a later zone name.
        print(f"stepdates: error: the output cannot hold {quote(text)}: {error}", file=sys.stderr)
        return 2
    except OverflowError as error:
        sys.stdout.flush()
        print(f"stepdates: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        # The reader went away (``| head``). Windows reports EINVAL rather than EPIPE.
        if not isinstance(error, BrokenPipeError) and error.errno != errno.EINVAL:
            raise
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
        return 0
    return 0
