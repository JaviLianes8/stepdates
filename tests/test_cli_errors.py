"""The tool's error messages: argparse's own, bounded, escaped and quick to build."""

from __future__ import annotations

import contextlib
import io
import time

import pytest

from stepdates._cli import _parser, main
from stepdates._quote import bound


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    try:
        code = main(argv)
    except SystemExit as stop:
        code = int(stop.code or 0)
    return code, capsys.readouterr().err


def _error_line(argv: list[str], capsys: pytest.CaptureFixture[str]) -> str:
    code, err = _run(argv, capsys)
    usage, _, error = err.partition("stepdates: error: ")
    assert code == 2
    assert usage.startswith("usage: stepdates ")
    assert error.endswith("\n")
    assert "\n" not in error[:-1]
    return "stepdates: error: " + error[:-1]


@pytest.mark.parametrize(
    ("argv", "line"),
    [
        (["2026-01-01", "2026-01-03", "y" * 80], "unrecognized arguments: " + "y" * 80),
        (
            ["2026-01-01", "2026-01-03", "y" * 81],
            "unrecognized arguments: " + repr("y" * 80) + "... (81 characters)",
        ),
        (
            ["2026-01-01", "-n", "1", "--bogus=" + "y" * 100],
            "unrecognized arguments: " + repr("--bogus=" + "y" * 72) + "... (108 characters)",
        ),
        (
            ["2026-01-01", "-n", "1", "--inclusive=" + "y" * 100],
            "argument --inclusive: ignored explicit argument "
            + repr("y" * 80)
            + "... (100 characters)",
        ),
        (
            ["2026-01-01", "-n", "1", "--s=" + "y" * 100],
            "ambiguous option: "
            + repr("--s=" + "y" * 76)
            + "... (104 characters) could match --step, --skip-invalid",
        ),
        (
            ["2026-01-01", "-n", "1", "--s=" + "y" * 76],
            "ambiguous option: --s=" + "y" * 76 + " could match --step, --skip-invalid",
        ),
        (
            ["2026-01-01", "2026-01-03", "a", "b", "c", "d", "e"],
            "unrecognized arguments: a b c and 2 more",
        ),
        (["2026-01-01", "2026-01-03", "a", "b", "c"], "unrecognized arguments: a b c"),
        (["2026-01-01", "2026-01-03", "a\tb", "c"], "unrecognized arguments: 'a\\tb' c"),
    ],
    ids=[
        "80 whole",
        "81 quoted",
        "unknown option",
        "explicit argument",
        "ambiguous",
        "ambiguous 80",
        "many",
        "three",
        "odd",
    ],
)
def test_the_whole_error_line(
    argv: list[str], line: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _error_line(argv, capsys) == "stepdates: error: " + line


def test_a_dash_h_tail_is_quoted_as_older_pythons_report_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Python 3.10 and 3.11 refuse "-hTAIL" with this message; later ones print the help.
    tail = "ghp_SECRET-" + "q" * 200
    with pytest.raises(SystemExit):
        _parser().error(f"argument -h/--help: ignored explicit argument {tail!r}")
    line = capsys.readouterr().err.splitlines()[-1]
    assert line == (
        "stepdates: error: argument -h/--help: ignored explicit argument "
        + repr(tail[:80])
        + "... (211 characters)"
    )


def test_a_dash_h_tail_is_never_echoed(capsys: pytest.CaptureFixture[str]) -> None:
    code, err = _run(["2026-01-01", "-n", "1", "-hghp_SECRET-" + "q" * 300], capsys)
    assert code in (0, 2)  # 0 where argparse prints the help instead
    assert "q" * 81 not in err
    assert len(err) < 1000


@pytest.mark.parametrize(
    "odd",
    ["a\nb", "a\rb", "a\x07b", "a\x85b", "a\u2028b", "\nstepdates: error: forged"],
)
@pytest.mark.parametrize("shape", ["unrecognized", "ambiguous", "explicit"])
def test_no_argument_starts_a_new_line(
    odd: str, shape: str, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = {
        "unrecognized": ["2026-01-01", "2026-01-03", odd],
        "ambiguous": ["2026-01-01", "-n", "1", "--s=" + odd],
        "explicit": ["2026-01-01", "-n", "1", "--inclusive=" + odd],
    }[shape]
    line = _error_line(argv, capsys)
    assert repr(odd)[1:-1] in line
    assert all(char.isprintable() for char in line)


def _seconds(argv: list[str]) -> float:
    best = float("inf")
    for _ in range(3):  # the best of three ignores a scheduler hiccup
        began = time.perf_counter()
        with pytest.raises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            main(argv)
        best = min(best, time.perf_counter() - began)
    return best


def _many(count: int, shape: str) -> list[str]:
    long = [f"{i:08d}".ljust(81, "z") for i in range(count)]
    if shape == "unrecognized":
        return ["2026-01-01", "2026-02-01", *long]
    return ["2026-01-01", "-n", "1", "--s=" + "z" * 50 * count, *long]


@pytest.mark.parametrize("shape", ["unrecognized", "ambiguous"])
def test_many_long_arguments_take_linear_time(shape: str) -> None:
    small, large = _seconds(_many(1000, shape)), _seconds(_many(4000, shape))
    # Four times the input may take at most about four times as long (plus a floor for noise).
    assert large < 10 * small + 0.05, (shape, small, large)


@pytest.mark.parametrize("shape", ["unrecognized", "ambiguous"])
def test_many_long_arguments_give_a_short_message(
    shape: str, capsys: pytest.CaptureFixture[str]
) -> None:
    code, err = _run(_many(4000, shape), capsys)
    assert code == 2
    assert len(err) < 1000


def test_bound_cuts_whole_escapes_at_the_message_limit() -> None:
    assert bound("a" * 500) == "a" * 500
    assert bound("a" * 501) == "a" * 500 + "... (501 characters)"
    assert bound("\x00" * 130) == "\\x00" * 125 + "... (130 characters)"
    assert bound("a\x00" * 101) == "a\\x00" * 100 + "... (202 characters)"
