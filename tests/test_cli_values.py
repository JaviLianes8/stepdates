"""Option values and positionals reach the tool exactly as written: empty, or with spaces."""

from __future__ import annotations

import pytest

from stepdates._cli import main

ERROR = "stepdates: error: "
EMPTY_STEP = (
    ERROR + "invalid step '': use a unit ('day', 'week', 'month', 'quarter', 'year') with an"
    ' optional signed count, for example "day", "2 weeks" or "-1 month", or an ISO 8601'
    ' duration such as "P1M"'
)
BAD_STOP = ERROR + "argument stop: not an ISO 8601 date or datetime: "


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    try:
        code = main(argv)
    except SystemExit as stop:
        code = int(stop.code or 0)
    out, err = capsys.readouterr()
    return code, out, err


@pytest.mark.parametrize(
    ("argv", "out"),
    [
        (["2026-01-01", "-n", "1", "-f", "-1 "], "-1 \n"),
        (["2026-01-01", "-n", "1", "--format=-1 "], "-1 \n"),
        (["2026-01-01", "-n", "1", "-f", " %d "], " 01 \n"),
        (["2026-01-01", "2026-01-03", "--format="], "2026-01-01\n2026-01-02\n"),
        (["2026-01-01", "2026-01-03", "-f", ""], "2026-01-01\n2026-01-02\n"),
    ],
    ids=["wrapped format", "glued wrapped format", "spaced format", "empty", "short empty"],
)
def test_a_format_is_used_as_written(
    argv: list[str], out: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(argv, capsys) == (0, out, "")


@pytest.mark.parametrize(
    ("argv", "last"),
    [
        (["2026-01-01", "2026-01-01", "--step="], EMPTY_STEP),
        (["2026-01-01", "2026-01-01", "-s", ""], EMPTY_STEP),
        (["2026-01-01", "2026-01-03", "--step", ""], EMPTY_STEP),
        (["--", "2026-01-01", " 2026-01-01", "-n", "2"], BAD_STOP + "' 2026-01-01'"),
        (["--", "2026-01-01", "-1 "], BAD_STOP + "'-1 '"),
        (["2026-01-01", "2026-01-03", "-1 "], ERROR + "unrecognized arguments: -1 "),
        (
            ["2026-01-01", "-n", "-1 "],
            ERROR + "argument -n/--count: not a whole number of at most 18 digits: '-1 '",
        ),
    ],
    ids=[
        "empty step",
        "short empty step",
        "long empty step",
        "spaced stop after double dash",
        "wrapped stop after double dash",
        "wrapped extra",
        "wrapped count",
    ],
)
def test_an_empty_or_spaced_value_is_refused_as_written(
    argv: list[str], last: str, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = _run(argv, capsys)
    assert (code, out) == (2, "")
    assert err.splitlines()[-1] == last
