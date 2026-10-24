"""Error messages: the argument they name, their length bounds and their escaping."""

from __future__ import annotations

import random
from datetime import date

import pytest

from stepdates import date_range, shift
from stepdates._cli import main
from stepdates._quote import quote
from stepdates._step import parse_step


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("x" * 78, repr("x" * 78)),
        ("x" * 79, repr("x" * 79)),
        ("x" * 80, repr("x" * 80)),
        ("x" * 81, repr("x" * 80) + "... (81 characters)"),
        ("\t" * 30, "'" + "\\t" * 30 + "'"),
        ("\t" * 40, "'" + "\\t" * 40 + "'"),
        ("\t" * 41, "'" + "\\t" * 40 + "'... (41 characters)"),
        ("\t" * 50, "'" + "\\t" * 40 + "'... (50 characters)"),
        ("\t" * 100, "'" + "\\t" * 40 + "'... (100 characters)"),
        ("x" * 78 + "\t", repr("x" * 78 + "\t")),
        ("x" * 79 + "\t", repr("x" * 79) + "... (80 characters)"),
        ("x" * 79 + "\x00", repr("x" * 79) + "... (80 characters)"),
        ("\x00" * 21, "'" + "\\x00" * 20 + "'... (21 characters)"),
        ("a" + "\x1b" * 30, "'a" + "\\x1b" * 19 + "'... (31 characters)"),
        ("\u200b" * 14, "'" + "\\u200b" * 13 + "'... (14 characters)"),
    ],
)
def test_quote_bounds(value: str, expected: str) -> None:
    assert quote(value) == expected


def test_quote_shows_the_longest_prefix_that_fits_whole() -> None:
    pool = ["x", "'", '"', "\\", "\t", "\x00", "\x1b", "\u200b", "\U000e0001", "\u00e9", " "]
    picks = random.Random(5545)
    for _ in range(3000):
        value = "".join(picks.choice(pool) for _ in range(picks.randint(0, 120)))
        text = quote(value)
        if len(value) <= 80 and len(repr(value)) <= 82:
            assert text == repr(value)
            continue
        note = f"... ({len(value)} characters)"
        assert text.endswith(note)
        shown = text[: -len(note)]
        size = next(n for n in range(len(value)) if repr(value[:n]) == shown)
        assert len(shown) <= 82
        assert size == 80 or len(repr(value[: size + 1])) > 82


def test_a_step_message_quotes_eighty_characters_at_the_boundary() -> None:
    with pytest.raises(ValueError) as caught:
        parse_step("x" * 80)
    assert repr("x" * 80) + ":" in str(caught.value)
    assert "characters)" not in str(caught.value)


def test_messages_escape_control_characters() -> None:
    with pytest.raises(ValueError) as step:
        parse_step("\x1b[2Jbad")
    with pytest.raises(ValueError) as policy:
        date_range(date(2026, 1, 1), count=1, invalid="\x1b[2J")  # type: ignore[arg-type]
    for caught in (step, policy):
        assert "\x1b" not in str(caught.value)
        assert "\\x1b[2J" in str(caught.value)


@pytest.mark.parametrize(
    "argv",
    [
        ["\x1b[2J", "-n", "1"],
        ["2026-01-01", "\x1b[2J"],
        ["2026-01-01", "-n", "\x1b[2J"],
        ["2026-01-01", "-n", "1", "-s", "\x1b[2J"],
    ],
)
def test_the_tool_escapes_control_characters(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as stop:
        main(argv)
    err = capsys.readouterr().err
    assert stop.value.code == 2
    assert "\x1b" not in err
    assert "\\x1b[2J" in err


def test_shift_names_its_own_argument() -> None:
    with pytest.raises(TypeError, match=r"^value must be a date or a datetime, not str$"):
        shift("2026-01-31", "month")  # type: ignore[type-var]
    with pytest.raises(
        ValueError,
        match=r"^end_of_month needs a value on the last day of its month, not 2026-01-30$",
    ):
        shift(date(2026, 1, 30), "month", end_of_month=True)


def test_date_range_names_start() -> None:
    with pytest.raises(TypeError, match=r"^start must be a date or a datetime, not str$"):
        date_range("2026-01-31", count=1)  # type: ignore[type-var]
    with pytest.raises(
        ValueError,
        match=r"^end_of_month needs a start on the last day of its month, not 2026-01-30$",
    ):
        date_range(date(2026, 1, 30), count=1, step="month", end_of_month=True)


@pytest.mark.parametrize(
    ("start", "words"), [(date(9999, 12, 1), "1 value"), (date(9999, 11, 1), "2 values")]
)
def test_the_overflow_message_counts_in_words(start: date, words: str) -> None:
    with pytest.raises(OverflowError, match=rf"after {words}$"):
        list(date_range(start, count=3, step="month"))
