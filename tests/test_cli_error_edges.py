"""argparse error lines at the edges of quoting: lengths, quote kinds and odd characters."""

from __future__ import annotations

import pytest

from stepdates._cli import _parser, main

AMBIGUOUS = " could match --step, --skip-invalid"


def _error_line(argv: list[str], capsys: pytest.CaptureFixture[str]) -> str:
    try:
        main(argv)
    except SystemExit as stop:
        assert stop.code == 2
    else:
        raise AssertionError("no error")
    usage, _, error = capsys.readouterr().err.partition("stepdates: error: ")
    assert usage.startswith("usage: stepdates ")
    assert error.endswith("\n")
    assert "\n" not in error[:-1]
    return "stepdates: error: " + error[:-1]


@pytest.mark.parametrize(
    ("arg", "line"),
    [
        (
            "--inclusive=" + "y" * 80,
            "argument --inclusive: ignored explicit argument " + repr("y" * 80),
        ),
        (
            "--inclusive=" + "y" * 81,
            "argument --inclusive: ignored explicit argument "
            + repr("y" * 80)
            + "... (81 characters)",
        ),
        (
            "--inclusive='" + "y" * 100,
            "argument --inclusive: ignored explicit argument "
            + repr("'" + "y" * 79)
            + "... (101 characters)",
        ),
        (
            "--inclusive='" + "y" * 100 + '"' + "y" * 300,
            "argument --inclusive: ignored explicit argument "
            + repr("'" + "y" * 79)
            + "... (402 characters)",
        ),
        (
            "--s=" + "y" * 77,
            "ambiguous option: " + repr("--s=" + "y" * 76) + "... (81 characters)" + AMBIGUOUS,
        ),
        (
            "--s=" + "a" * 90 + " could match " + "b" * 300,
            "ambiguous option: " + repr("--s=" + "a" * 76) + "... (407 characters)" + AMBIGUOUS,
        ),
        ("--s='" + "\\" * 75, "ambiguous option: --s='" + "\\" * 75 + AMBIGUOUS),
        ("--s=it's", "ambiguous option: --s=it's" + AMBIGUOUS),
        (
            "--s=" + "\u200b" * 76,
            "ambiguous option: '--s=" + "\\u200b" * 12 + "'... (80 characters)" + AMBIGUOUS,
        ),
        (
            "--s=" + "\U000e0001" * 76,
            "ambiguous option: '--s=" + "\\U000e0001" * 7 + "'... (80 characters)" + AMBIGUOUS,
        ),
        ("--s=a\tb", "ambiguous option: '--s=a\\tb'" + AMBIGUOUS),
    ],
    ids=[
        "explicit 80",
        "explicit 81",
        "explicit with a single quote",
        "explicit with both quotes",
        "ambiguous 81",
        "ambiguous naming the tail",
        "ambiguous unclosed quote and backslashes",
        "ambiguous apostrophe",
        "ambiguous wide escapes",
        "ambiguous wider escapes",
        "ambiguous tab",
    ],
)
@pytest.mark.timeout(30)
def test_the_error_line_at_the_edges(
    arg: str, line: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _error_line(["2026-01-01", "-n", "1", arg], capsys) == "stepdates: error: " + line


def test_a_long_message_is_cut_once_and_names_its_own_length(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        _parser().error("x" * 600)
    line = capsys.readouterr().err.splitlines()[-1]
    assert line == "stepdates: error: " + "x" * 500 + "... (600 characters)"
