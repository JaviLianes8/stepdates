"""The command line reads the same on every supported Python, with or without a stdout."""

from __future__ import annotations

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
