"""Month-end conventions: clamp, skip, end_of_month, and shift."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from stepdates import date_range, shift


def test_skip_drops_days_a_month_lacks_and_does_not_count_them() -> None:
    result = list(date_range(date(2026, 1, 31), count=4, step="month", invalid="skip"))
    assert result == [date(2026, 1, 31), date(2026, 3, 31), date(2026, 5, 31), date(2026, 7, 31)]


def test_skip_with_a_stop_ends_at_the_stop() -> None:
    result = list(date_range(date(2026, 1, 30), date(2026, 4, 30), step="month", invalid="skip"))
    assert result == [date(2026, 1, 30), date(2026, 3, 30)]


def test_skip_with_inclusive_stop_on_a_valid_term() -> None:
    result = list(
        date_range(
            date(2026, 1, 30), date(2026, 4, 30), step="month", invalid="skip", inclusive=True
        )
    )
    assert result == [date(2026, 1, 30), date(2026, 3, 30), date(2026, 4, 30)]


def test_skip_stops_when_a_dropped_term_lands_beyond_the_stop() -> None:
    # 31 February is dropped; its clamped stand-in is past the stop, so the range ends.
    result = list(date_range(date(2026, 1, 31), date(2026, 2, 27), step="month", invalid="skip"))
    assert result == [date(2026, 1, 31)]


def test_skip_keeps_walking_past_dropped_terms_inside_the_stop() -> None:
    stop = date(2026, 3, 31)
    assert list(date_range(date(2026, 1, 31), stop, step="month", invalid="skip")) == [
        date(2026, 1, 31)
    ]
    assert list(
        date_range(date(2026, 1, 31), stop, step="month", invalid="skip", inclusive=True)
    ) == [date(2026, 1, 31), date(2026, 3, 31)]


def test_skip_backwards() -> None:
    result = list(date_range(date(2026, 5, 31), count=3, step="-1 month", invalid="skip"))
    assert result == [date(2026, 5, 31), date(2026, 3, 31), date(2026, 1, 31)]


def test_skip_backwards_with_stop() -> None:
    result = list(date_range(date(2026, 5, 31), date(2026, 2, 1), step="-1 month", invalid="skip"))
    assert result == [date(2026, 5, 31), date(2026, 3, 31)]


def test_skip_leap_day_yearly_waits_for_leap_years() -> None:
    result = list(date_range(date(2096, 2, 29), count=3, step="year", invalid="skip"))
    assert result == [date(2096, 2, 29), date(2104, 2, 29), date(2108, 2, 29)]


def test_skip_does_nothing_for_day_steps() -> None:
    a = list(date_range(date(2026, 1, 1), count=40, step="3 days", invalid="skip"))
    assert a == list(date_range(date(2026, 1, 1), count=40, step="3 days"))


def test_end_of_month_follows_month_ends() -> None:
    result = list(date_range(date(2026, 4, 30), count=5, step="month", end_of_month=True))
    assert result == [
        date(2026, 4, 30),
        date(2026, 5, 31),
        date(2026, 6, 30),
        date(2026, 7, 31),
        date(2026, 8, 31),
    ]


def test_end_of_month_from_february() -> None:
    result = list(date_range(date(2023, 2, 28), count=3, step="year", end_of_month=True))
    assert result == [date(2023, 2, 28), date(2024, 2, 29), date(2025, 2, 28)]


def test_end_of_month_backwards_with_stop() -> None:
    result = list(
        date_range(date(2026, 3, 31), date(2025, 12, 31), step="-1 month", end_of_month=True)
    )
    assert result == [date(2026, 3, 31), date(2026, 2, 28), date(2026, 1, 31)]


def test_end_of_month_needs_a_month_end_start() -> None:
    with pytest.raises(ValueError, match="last day of its month"):
        date_range(date(2026, 4, 29), count=2, step="month", end_of_month=True)


@pytest.mark.parametrize("step", ["day", "week", timedelta(days=30)])
def test_end_of_month_needs_a_month_based_step(step: str | timedelta) -> None:
    with pytest.raises(ValueError, match="month, quarter or year step"):
        date_range(date(2026, 4, 30), count=2, step=step, end_of_month=True)


def test_unknown_invalid_policy_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid must be one of"):
        date_range(date(2026, 1, 1), count=2, invalid="roll")  # type: ignore[arg-type]


def test_shift_clamps() -> None:
    assert shift(date(2026, 1, 31), "1 month") == date(2026, 2, 28)
    assert shift(date(2024, 2, 29), "year") == date(2025, 2, 28)
    assert shift(date(2024, 2, 29), "-P4Y") == date(2020, 2, 29)
    assert shift(date(2026, 3, 31), "-1 quarter") == date(2025, 12, 31)


def test_shift_by_days_and_timedelta() -> None:
    assert shift(date(2026, 12, 31), "day") == date(2027, 1, 1)
    assert shift(date(2026, 1, 1), timedelta(days=-1)) == date(2025, 12, 31)


def test_shift_end_of_month() -> None:
    assert shift(date(2026, 2, 28), "month", end_of_month=True) == date(2026, 3, 31)
    with pytest.raises(ValueError):
        shift(date(2026, 2, 27), "month", end_of_month=True)


def test_shift_rejects_bad_input() -> None:
    with pytest.raises(TypeError, match="must be a date"):
        shift("2026-01-01", "day")  # type: ignore[type-var]
    with pytest.raises(ValueError):
        shift(date(2026, 1, 1), "fortnight")


def test_shift_raises_outside_the_supported_years() -> None:
    with pytest.raises(OverflowError, match="1 to 9999"):
        shift(date(9999, 12, 31), "month")
    with pytest.raises(OverflowError, match="1 to 9999"):
        shift(date(1, 1, 1), "-1 day")


def test_end_of_month_terms_are_never_skipped() -> None:
    start = date(2026, 1, 31)
    clamped = list(date_range(start, count=4, step="month", end_of_month=True))
    skipped = list(date_range(start, count=4, step="month", end_of_month=True, invalid="skip"))
    assert (
        skipped
        == clamped
        == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)]
    )
