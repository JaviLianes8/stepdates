"""Hostile input: huge, malformed or odd values never hang, blow up or flood a message."""

from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from datetime import date

import pytest

from stepdates import date_range, shift
from stepdates._cli import main
from stepdates._step import parse_step

SHAPES: dict[str, Callable[[int], str]] = {
    "leading blanks": lambda n: " " * n + "x",
    "blanks around a count": lambda n: " " * n + "1" + " " * n,
    "count then blanks": lambda n: "1" + " " * n + "x",
    "blank runs between digits": lambda n: "1 " * n,
    "long duration": lambda n: "P" + "1" * n + "X",
    "repeated designators": lambda n: "P" + "1M" * n,
    "unit repeated": lambda n: "day" * n,
    "signs": lambda n: "+-" * n + "day",
    "tabs and newlines": lambda n: "\t\n" * n + "month" + "\r\f" * n + "!",
}


def _seconds(text: str) -> float:
    best = float("inf")
    for _ in range(3):  # the best of three ignores a scheduler hiccup
        began = time.perf_counter()
        with contextlib.suppress(ValueError):
            parse_step(text)
        best = min(best, time.perf_counter() - began)
    return best


@pytest.mark.parametrize("shape", list(SHAPES))
def test_step_parsing_is_linear(shape: str) -> None:
    small, large = _seconds(SHAPES[shape](50_000)), _seconds(SHAPES[shape](200_000))
    # Four times the input may take at most about four times as long (plus a floor for noise).
    assert large < 10 * small + 0.05, (shape, small, large)


@pytest.mark.parametrize("shape", list(SHAPES))
def test_errors_quote_at_most_a_short_prefix(shape: str) -> None:
    text = SHAPES[shape](100_000)
    with pytest.raises(ValueError) as caught:
        parse_step(text)
    assert len(str(caught.value)) < 300
    assert f"{len(text)} characters" in str(caught.value)


def test_a_huge_policy_name_is_not_echoed() -> None:
    with pytest.raises(ValueError) as caught:
        date_range(date(2026, 1, 1), count=1, invalid="x" * 1_000_000)  # type: ignore[arg-type]
    assert len(str(caught.value)) < 300


@pytest.mark.parametrize("digits", [19, 4301, 100_000])
def test_more_than_eighteen_digits_is_a_clean_value_error(digits: int) -> None:
    for text in ("1" * digits + " days", "P" + "1" * digits + "M", "-P" + "1" * digits + "W"):
        with pytest.raises(ValueError, match="more than 18 digits") as caught:
            parse_step(text)
        assert len(str(caught.value)) < 300


def test_eighteen_digits_are_still_a_step() -> None:
    assert parse_step("9" * 18 + " days").days == 10**18 - 1
    assert list(date_range(date(2026, 1, 1), date(2027, 1, 1), step="9" * 18 + " months")) == [
        date(2026, 1, 1)
    ]
    with pytest.raises(OverflowError):
        shift(date(2026, 1, 1), "P" + "9" * 18 + "D")


@pytest.mark.parametrize("sign", ["+", "-"])
def test_a_sign_is_not_counted_as_a_digit(sign: str) -> None:
    assert parse_step(sign + "9" * 18 + " days").days == int(sign + "9" * 18)
    assert parse_step(sign + "P" + "9" * 18 + "M").months == int(sign + "9" * 18)
    with pytest.raises(ValueError, match="more than 18 digits"):
        parse_step(sign + "9" * 19 + " days")


@pytest.mark.parametrize("space", [chr(c) for c in (0xA0, 0x2003, 0x3000, 0x200B, 0x85)])
def test_only_ascii_whitespace_surrounds_a_step(space: str) -> None:
    for text in (f"{space}P1M", f"month{space}", f"1{space}month"):
        with pytest.raises(ValueError, match="invalid step"):
            parse_step(text)


# Fullwidth one, Arabic-Indic one, fullwidth P and M.
ONE, ARABIC_ONE, WIDE_P, WIDE_M = chr(0xFF11), chr(0x0661), chr(0xFF30), chr(0xFF2D)


@pytest.mark.parametrize(
    "text", [f"{ONE} day", f"{ARABIC_ONE} day", f"P{ARABIC_ONE}M", f"{WIDE_P}{ONE}{WIDE_M}"]
)
def test_non_ascii_digits_and_letters_are_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="invalid step"):
        parse_step(text)


def test_the_longest_ranges_finish_quickly() -> None:
    began = time.perf_counter()
    days = sum(1 for _ in date_range(date.min, date.max, inclusive=True))
    months = sum(1 for _ in date_range(date.min, date.max, step="month", invalid="skip"))
    assert (days, months) == ((date.max - date.min).days + 1, 9999 * 12)
    assert time.perf_counter() - began < 60


@pytest.mark.parametrize(
    "argv",
    [
        ["x" * 1_000_000, "-n", "1"],
        ["2026-01-01", "-n", "9" * 100_000],
        ["2026-01-01", "-n", "1", "-s", "z" * 1_000_000],
        ["2026-01-01", "-n", "1", "-f", "%" * 1_000_000 + "Q"],
    ],
)
def test_the_tool_keeps_error_lines_short(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    try:
        main(argv)
    except SystemExit as exit:
        code = exit.code
    else:
        code = 0
    err = capsys.readouterr().err
    if code == 2:
        assert len(err) < 1000
    else:  # a strftime pattern the platform accepts prints, with status 0
        assert code == 0
