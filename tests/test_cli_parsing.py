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
    ],
    ids=["inclusive between", "step between", "options all around", "count after", "count before"],
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
