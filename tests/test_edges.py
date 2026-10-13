"""Argument checks and the edges of the supported years."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from stepdates import date_range


def test_stop_mode_ends_cleanly_at_the_last_supported_year() -> None:
    result = list(date_range(date(9999, 10, 31), date.max, step="month", inclusive=True))
    assert result == [date(9999, 10, 31), date(9999, 11, 30), date(9999, 12, 31)]


def test_stop_mode_ends_cleanly_with_day_steps_near_the_end() -> None:
    result = list(date_range(date(9999, 12, 29), date.max, step="2 days", inclusive=True))
    assert result == [date(9999, 12, 29), date(9999, 12, 31)]
    assert list(date_range(date(9999, 12, 30), date.max, step="week", inclusive=True)) == [
        date(9999, 12, 30)
    ]


def test_stop_mode_ends_cleanly_at_the_first_supported_year() -> None:
    result = list(date_range(date(1, 3, 1), date.min, step="-1 month", inclusive=True))
    assert result == [date(1, 3, 1), date(1, 2, 1), date(1, 1, 1)]
    assert list(date_range(date(1, 1, 5), date.min, step="-1 week", inclusive=True)) == [
        date(1, 1, 5)
    ]


def test_count_mode_raises_overflow_after_the_values_that_fit() -> None:
    values = date_range(date(9999, 11, 30), count=3, step="month")
    assert next(values) == date(9999, 11, 30)
    assert next(values) == date(9999, 12, 30)
    with pytest.raises(OverflowError, match="after 2 values"):
        next(values)


def test_count_mode_overflow_for_day_steps_and_backwards() -> None:
    with pytest.raises(OverflowError, match="1 to 9999"):
        list(date_range(date(9999, 12, 31), count=2))
    with pytest.raises(OverflowError, match="1 to 9999"):
        list(date_range(date(1, 1, 1), count=2, step="-1 year"))


def test_count_mode_overflow_for_datetimes() -> None:
    with pytest.raises(OverflowError, match="1 to 9999"):
        list(date_range(datetime(9999, 12, 31, 12), count=2))


def test_skip_count_runs_into_the_end_instead_of_looping() -> None:
    with pytest.raises(OverflowError):
        list(date_range(date(9996, 2, 29), count=3, step="year", invalid="skip"))


@pytest.mark.parametrize("start", ["2026-01-01", 20260101, None])
def test_start_must_be_a_date(start: object) -> None:
    with pytest.raises(TypeError, match="start must be"):
        date_range(start, count=1)  # type: ignore[type-var]


def test_stop_must_be_a_date() -> None:
    with pytest.raises(TypeError, match="stop must be"):
        date_range(date(2026, 1, 1), "2026-02-01")  # type: ignore[arg-type]


@pytest.mark.parametrize("count", [True, 2.0, "3"])
def test_count_must_be_an_int(count: object) -> None:
    with pytest.raises(TypeError, match="count must be an int"):
        date_range(date(2026, 1, 1), count=count)  # type: ignore[arg-type]


def test_inclusive_with_count_is_rejected() -> None:
    with pytest.raises(ValueError, match="inclusive"):
        date_range(date(2026, 1, 1), count=3, inclusive=True)


def test_inclusive_false_with_count_is_fine() -> None:
    assert len(list(date_range(date(2026, 1, 1), count=3, inclusive=False))) == 3


def test_errors_are_raised_before_iteration() -> None:
    with pytest.raises(TypeError):
        date_range(date(2026, 1, 1), count=1, step=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        date_range(date(2026, 1, 31), count=1, step="day", end_of_month=True)


def test_date_subclasses_keep_their_type() -> None:
    class Day(date):
        pass

    result = list(date_range(Day(2026, 1, 31), count=3, step="month"))
    assert all(type(value) is Day for value in result)
    assert list(date_range(Day(2026, 1, 1), count=2))[1] == date(2026, 1, 2)
    assert type(list(date_range(Day(2026, 1, 1), count=2))[1]) is Day
