"""The command line tool."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from stepdates import __version__
from stepdates._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    try:
        code = main(argv)
    except SystemExit as stop:
        code = int(stop.code or 0)
    out, err = capsys.readouterr()
    return code, out, err


def test_prints_one_iso_date_per_line(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["2026-01-30", "2026-02-02"], capsys) == (
        0,
        "2026-01-30\n2026-01-31\n2026-02-01\n",
        "",
    )


def test_count_step_and_clamping(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["2026-01-31", "--count", "3", "--step", "1 month"], capsys)
    assert (code, out.split()) == (0, ["2026-01-31", "2026-02-28", "2026-03-31"])


def test_short_options(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["2026-01-31", "-n", "2", "-s", "P1M", "-f", "%d/%m/%Y"], capsys)
    assert (code, out.split()) == (0, ["31/01/2026", "28/02/2026"])


def test_skip_invalid(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["2026-01-31", "-n", "3", "-s", "month", "--skip-invalid"], capsys)
    assert (code, out.split()) == (0, ["2026-01-31", "2026-03-31", "2026-05-31"])


def test_end_of_month(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["2026-04-30", "-n", "2", "-s", "month", "--end-of-month"], capsys)
    assert (code, out.split()) == (0, ["2026-04-30", "2026-05-31"])


def test_inclusive_and_backwards(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["2026-01-03", "2026-01-01", "-s", "-1 day", "--inclusive"], capsys)
    assert (code, out.split()) == (0, ["2026-01-03", "2026-01-02", "2026-01-01"])


def test_datetimes(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["2026-03-28T09:00:00+01:00", "-n", "2"], capsys)
    assert (code, out.split()) == (0, ["2026-03-28T09:00:00+01:00", "2026-03-29T09:00:00+01:00"])


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["2026-13-01", "-n", "1"], "not an ISO 8601 date"),
        (["2026-01-01", "-n", "x"], "not a whole number"),
        (["2026-01-01"], "exactly one of stop or count"),
        (["2026-01-01", "2026-02-01", "-n", "2"], "exactly one of stop or count"),
        (["2026-01-01", "-n", "2", "-s", "fortnight"], "invalid step"),
        (["2026-01-01", "-n", "-1"], "must not be negative"),
        (["2026-01-01", "2026-01-02T00:00"], "both be dates or both be datetimes"),
        (["2026-01-30", "-n", "2", "-s", "month", "--end-of-month"], "last day of its month"),
        (["2026-01-01", "-n", "2", "--inclusive"], "inclusive"),
        (["2026-01-01", "-n", "2", "-f", "%"], "invalid --format"),
        (["2026-01-01", "-n", "\u0662"], "not a whole number"),
        (["2026-01-01", "-n", "2", "-s"], "expected one argument"),
    ],
)
def test_bad_input_exits_two(
    argv: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = _run(argv, capsys)
    assert (code, out) == (2, "")
    assert message in err
    assert err.startswith("usage: stepdates")


def test_overflow_exits_one_after_the_values_that_fit(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(["9999-12-30", "-n", "3"], capsys)
    assert (code, out) == (1, "9999-12-30\n9999-12-31\n")
    assert err == "stepdates: the range leaves the supported years 1 to 9999 after 2 values\n"


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["--version"], capsys) == (0, f"stepdates {__version__}\n", "")


class _ClosedPipe(io.StringIO):
    def write(self, text: str) -> int:
        raise BrokenPipeError

    def fileno(self) -> int:
        return sys.__stdout__.fileno() if sys.__stdout__ else 1


def test_a_closed_pipe_stops_quietly(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(sys, "stdout", _ClosedPipe())
    monkeypatch.setattr(os, "dup2", lambda a, b: calls.append((a, b)))
    assert main(["2026-01-01", "-n", "5"]) == 0
    assert len(calls) == 1


def test_python_dash_m_runs_the_tool(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "stepdates", "2024-02-29", "-n", "2", "-s", "year"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert (result.returncode, result.stdout.split()) == (0, ["2024-02-29", "2025-02-28"])


def test_a_dash_led_step_needs_no_equals_sign(capsys: pytest.CaptureFixture[str]) -> None:
    for flag in ("-s", "--step"):
        code, out, _ = _run(["2026-03-31", "-n", "2", flag, "-P1M"], capsys)
        assert (code, out.split()) == (0, ["2026-03-31", "2026-02-28"])
    code, out, _ = _run(["2026-03-31", "-n", "2", "--step=-1 month"], capsys)
    assert (code, out.split()) == (0, ["2026-03-31", "2026-02-28"])


def test_a_plain_date_stays_a_date(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["2026-01-01", "-n", "1"], capsys)
    assert (code, out) == (0, "2026-01-01\n")
    if sys.version_info >= (3, 11):  # compact ISO 8601 dates need Python 3.11
        assert _run(["20260101", "-n", "1"], capsys)[:2] == (0, "2026-01-01\n")


def test_a_reader_that_goes_away_gets_no_traceback(tmp_path: Path) -> None:
    process = subprocess.Popen(
        [sys.executable, "-m", "stepdates", "2026-01-01", "-n", "1000000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert process.stdout is not None and process.stderr is not None
    assert process.stdout.readline() == b"2026-01-01" + os.linesep.encode()
    process.stdout.close()
    err = process.stderr.read()
    assert process.wait(timeout=60) == 0, err
    assert err == b""
