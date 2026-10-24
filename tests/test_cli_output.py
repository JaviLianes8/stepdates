"""The command line tool: output encodings, argparse's own errors and exit statuses."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

import stepdates._cli
from stepdates._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"
BIG = "z" * 30_000


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    try:
        code = main(argv)
    except SystemExit as stop:
        code = int(stop.code or 0)
    return code, capsys.readouterr().err


def _module(*argv: str, **env: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-m", "stepdates", *argv],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1", **env},
    )


@pytest.mark.parametrize("pattern", ["%d \u6708", "%Y \u2713", "%Y \ud800"])
def test_a_format_the_output_cannot_encode_exits_two(
    pattern: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    buffer = io.BytesIO()
    encoding = "utf-8" if "\ud800" in pattern else "cp1252"
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(buffer, encoding=encoding))
    code, err = _run(["2026-01-01", "-n", "2", "-f", pattern], capsys)
    assert (code, buffer.getvalue()) == (2, b"")
    assert "invalid --format" in err
    assert "Traceback" not in err


def test_a_value_the_output_cannot_encode_exits_two(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Odd(date):
        def isoformat(self) -> str:
            return "\u6708"

    monkeypatch.setattr(stepdates._cli, "date_range", lambda *a, **k: iter([Odd(2026, 1, 1)]))
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))
    code, err = _run(["2026-01-01", "-n", "1"], capsys)
    assert code == 2
    assert err.startswith("stepdates: error: ")
    assert "Traceback" not in err


def test_a_cp1252_pipe_gets_no_traceback() -> None:
    result = _module("2026-01-01", "-n", "2", "-f", "%d \u6708", PYTHONIOENCODING="cp1252")
    assert result.returncode == 2
    assert b"Traceback" not in result.stdout
    assert b"invalid --format" in result.stdout


def test_python_dash_m_exits_one_after_the_values_that_fit_in_order() -> None:
    result = _module("9999-12-30", "-n", "5")
    assert result.returncode == 1
    assert result.stdout.decode().splitlines() == [
        "9999-12-30",
        "9999-12-31",
        "stepdates: the range leaves the supported years 1 to 9999 after 2 values",
    ]


@pytest.mark.parametrize(
    ("argv", "shown"),
    [
        (["2026-01-01", "2026-01-03", BIG], BIG),
        (["2026-01-01", "-n", "1", "--" + BIG], "--" + BIG),
        (["2026-01-01", "-n", "1", "--s=" + BIG], "--s=" + BIG),
        (["2026-01-01", "-n", "1", "--inclusive=" + BIG], BIG),
        (["2026-01-01", "-n", "1", "--token=sk-SECRET-" + "x" * 200], "x" * 200),
    ],
    ids=["unrecognized", "unknown option", "ambiguous option", "explicit argument", "secret"],
)
def test_argparse_errors_quote_at_most_a_short_prefix(
    argv: list[str], shown: str, capsys: pytest.CaptureFixture[str]
) -> None:
    code, err = _run(argv, capsys)
    assert code == 2
    assert len(err) < 1000
    assert shown[:81] not in err
    assert "characters)" in err


def test_argparse_errors_escape_control_characters(capsys: pytest.CaptureFixture[str]) -> None:
    code, err = _run(["2026-01-01", "2026-01-03", "\x1b[2J"], capsys)
    assert code == 2
    assert "unrecognized arguments" in err
    assert "\x1b" not in err
    assert "\\x1b[2J" in err


def test_short_unknown_arguments_are_named_as_given(capsys: pytest.CaptureFixture[str]) -> None:
    code, err = _run(["2026-01-01", "2026-01-03", "--colour", "x"], capsys)
    assert code == 2
    assert err.endswith("stepdates: error: unrecognized arguments: --colour x\n")


def test_no_standard_output_is_a_one_line_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    assert main(["2026-01-01", "-n", "1", "-f", "%d \u6708"]) == 2
    assert capsys.readouterr().err == "stepdates: error: there is no standard output to write to\n"


# Python 3.10 and 3.11 on Windows encode a strftime format with the locale codec, which
# refuses most non-Latin text; an accented letter passes everywhere this suite runs.
ACCENT = "%d \u00e9"


def _strftime_takes_the_accent() -> None:
    try:
        date(2026, 1, 1).strftime(ACCENT)
    except UnicodeError:  # pragma: no cover - a locale without that letter
        pytest.skip("strftime cannot encode the format with this locale")


def test_a_stdout_without_an_encoding_takes_utf_8(monkeypatch: pytest.MonkeyPatch) -> None:
    _strftime_takes_the_accent()
    sink = io.StringIO()  # its encoding is None
    monkeypatch.setattr(sys, "stdout", sink)
    assert main(["2026-01-01", "-n", "2", "-f", ACCENT]) == 0
    assert sink.getvalue() == "01 \u00e9\n02 \u00e9\n"


@pytest.mark.parametrize(
    ("handler", "shown"), [("backslashreplace", b"01 \\xe9"), ("replace", b"01 ?")]
)
def test_the_format_check_uses_the_error_handler_of_stdout(handler: str, shown: bytes) -> None:
    _strftime_takes_the_accent()
    result = _module("2026-01-01", "-n", "2", "-f", ACCENT, PYTHONIOENCODING=f"ascii:{handler}")
    assert result.returncode == 0
    assert result.stdout.splitlines() == [shown, shown.replace(b"01", b"02")]
