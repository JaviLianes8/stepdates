"""The command line reads the same on every supported Python, with or without a stdout."""

from __future__ import annotations

import itertools
import sys

import pytest

from stepdates._cli import main


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    try:
        code = main(argv)
    except SystemExit as stop:
        code = int(stop.code or 0)
    out, err = capsys.readouterr()
    return code, out, err


@pytest.mark.parametrize(
    ("argv", "lines"),
    [
        (
            ["2026-01-01", "--inclusive", "2026-01-03"],
            ["2026-01-01", "2026-01-02", "2026-01-03"],
        ),
        (["2026-01-01", "-s", "week", "2026-01-20"], ["2026-01-01", "2026-01-08", "2026-01-15"]),
        (
            ["--inclusive", "2026-01-01", "-s", "2 days", "2026-01-05", "-f", "%d"],
            ["01", "03", "05"],
        ),
        (["2026-01-01", "-n", "2"], ["2026-01-01", "2026-01-02"]),
        (["-n", "2", "2026-01-01"], ["2026-01-01", "2026-01-02"]),
        (["--inclusive", "--", "2026-01-01", "2026-01-02"], ["2026-01-01", "2026-01-02"]),
        (["-s", "-1 day", "2026-01-03", "--", "2026-01-01"], ["2026-01-03", "2026-01-02"]),
    ],
    ids=[
        "inclusive between",
        "step between",
        "options all around",
        "count after",
        "count before",
        "options before double dash",
        "stop after double dash",
    ],
)
def test_stop_may_come_after_an_option(
    argv: list[str], lines: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = _run(argv, capsys)
    assert (code, err) == (0, "")
    assert out.splitlines() == lines


def test_extra_positionals_after_an_option_are_still_refused(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["2026-01-01", "--inclusive", "2026-01-03", "x", "y"], capsys)
    assert (code, out) == (2, "")
    assert err.endswith("stepdates: error: unrecognized arguments: x y\n")


UNKNOWN = "stepdates: error: unrecognized arguments: "
BAD_START = "stepdates: error: argument start: not an ISO 8601 date or datetime: "
BAD_STOP = "stepdates: error: argument stop: not an ISO 8601 date or datetime: "


@pytest.mark.parametrize(
    ("argv", "last"),
    [
        (["2026-01-01", "--bogus", "2026-01-03"], UNKNOWN + "--bogus"),
        (["2026-01-01", "-x", "2026-01-03", "--inclusive"], UNKNOWN + "-x"),
        (
            ["--x1", "2026-01-01", "--x2", "--x3", "2026-01-03", "--x4"],
            UNKNOWN + "--x1 --x2 --x3 and 1 more",
        ),
        (["2026-01-01", "--bogus", "2026-01-03", "x"], UNKNOWN + "--bogus x"),
        (["2026-01-01", "--bogus", "2026-01-03", "-n", "2"], UNKNOWN + "--bogus"),
        (["2026-01-01", "--bogus", "--", "2026-01-03"], UNKNOWN + "--bogus"),
        (["2026-01-01", "--bogus", "2026-01-03", "--", "x"], UNKNOWN + "--bogus x"),
        (["2026-01-01", "--bogus", "--"], UNKNOWN + "--bogus"),
        (["2026-01-01", "--bogus", "x"], BAD_STOP + "'x'"),
        (["2026-01-01", "--bogus", "-5"], BAD_STOP + "'-5'"),
        (["2026-01-01", "--bogus", ""], BAD_STOP + "''"),
        (["2026-01-01", "-x", ""], BAD_STOP + "''"),
        (["2026-01-01", "--bogus", "--", "--"], BAD_STOP + "'--'"),
        (["--", "2026-01-01", "2026-01-03", "--inclusive"], UNKNOWN + "--inclusive"),
        (["--", "--bogus"], BAD_START + "'--bogus'"),
        (["2026-01-01", "2026-01-03", "--", "-x", "--"], UNKNOWN + "-x --"),
    ],
    ids=[
        "typo before stop",
        "short unknown before stop",
        "unknown options all around",
        "extra positional after stop",
        "count after stop",
        "double dash before stop",
        "double dash after stop",
        "double dash alone",
        "bad stop",
        "negative number stop",
        "empty stop",
        "empty stop after a short unknown",
        "double dash as stop",
        "an option after double dash",
        "an option as start",
        "dash-led extras after double dash",
    ],
)
def test_unknown_options_and_double_dash_read_the_same_on_every_python(
    argv: list[str], last: str, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = _run(argv, capsys)
    assert (code, out) == (2, "")
    assert err.splitlines()[-1] == last


COUNT = "stepdates: error: argument -n/--count: "


@pytest.mark.parametrize(
    ("argv", "code", "out", "last"),
    [
        (
            ["2026-01-01", "--count=--"],
            2,
            "",
            COUNT + "not a whole number of at most 18 digits: '--'",
        ),
        (["2026-01-01", "--step=--"], 2, "", "stepdates: error: invalid step '--': use a unit"),
        (["2026-01-01", "-n", "1", "--format=--"], 0, "--\n", None),
        (["-f--", "-n", "1", "2026-01-01"], 0, "--\n", None),
        (["-n", "--", "2", "2026-01-01"], 2, "", COUNT + "expected one argument"),
        (["2026-01-01", "-1x"], 2, "", BAD_STOP + "'-1x'"),
        (
            ["-n", "-1x", "2026-01-01"],
            2,
            "",
            COUNT + "not a whole number of at most 18 digits: '-1x'",
        ),
        (["2026-01-01", "-n", "1", "-f", "-1x"], 0, "-1x\n", None),
        (["2026-01-01", "--", "-s", "week"], 2, "", BAD_STOP + "'-s'"),
    ],
    ids=[
        "count of double dash",
        "step of double dash",
        "format of double dash",
        "short format of double dash",
        "option before double dash",
        "number-like stop",
        "number-like count",
        "number-like format",
        "step flag after double dash",
    ],
)
def test_option_values_read_the_same_on_every_python(
    argv: list[str], code: int, out: str, last: str | None, capsys: pytest.CaptureFixture[str]
) -> None:
    got = _run(argv, capsys)
    assert got[:2] == (code, out)
    assert got[2].splitlines()[-1].startswith(last) if last else got[2] == ""


TOKENS = ["2026-01-01", "--", "-x", "-5", "-1x", "-n", "-s", "-f", "x", "--count=--"]


def test_a_rewritten_argument_never_shows_in_output(capsys: pytest.CaptureFixture[str]) -> None:
    for argv in itertools.product(TOKENS, repeat=3):
        _, out, err = _run(list(argv), capsys)
        assert "\0" not in out + err and "\\x00" not in out + err, argv


@pytest.mark.parametrize(
    "argv",
    [["--help"], ["--version"], ["-h"], ["2026-01-01", "-n", "1", "--help"], ["--bogus"], []],
)
def test_without_a_stdout_every_run_is_a_one_line_error(
    argv: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    code, _, err = _run(argv, capsys)
    assert code == 2
    assert err == "stepdates: error: there is no standard output to write to\n"
