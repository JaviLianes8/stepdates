from datetime import date

import pytest

from stepdates import date_range


def test_daily_range_is_half_open() -> None:
    result = list(date_range(date(2026, 1, 1), date(2026, 1, 4)))
    assert result == [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]


def test_weekly_step() -> None:
    result = list(date_range(date(2026, 1, 1), date(2026, 1, 22), step="week"))
    assert result == [date(2026, 1, 1), date(2026, 1, 8), date(2026, 1, 15)]


def test_multiple_step_size() -> None:
    result = list(date_range(date(2026, 1, 1), count=3, step="2 days"))
    assert result == [date(2026, 1, 1), date(2026, 1, 3), date(2026, 1, 5)]


def test_monthly_step_clamps_to_end_of_month() -> None:
    result = list(date_range(date(2026, 1, 31), count=4, step="month"))
    # Each term is anchored on the 31st, so February clamps but March returns.
    assert result == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
        date(2026, 4, 30),
    ]


def test_yearly_step_handles_leap_day() -> None:
    result = list(date_range(date(2020, 2, 29), count=5, step="year"))
    assert result == [
        date(2020, 2, 29),
        date(2021, 2, 28),
        date(2022, 2, 28),
        date(2023, 2, 28),
        date(2024, 2, 29),
    ]


def test_count_mode_yields_exactly_count_values() -> None:
    result = list(date_range(date(2026, 1, 1), count=5))
    assert len(result) == 5
    assert result[-1] == date(2026, 1, 5)


def test_inclusive_includes_the_endpoint() -> None:
    result = list(date_range(date(2026, 1, 1), date(2026, 1, 3), inclusive=True))
    assert result == [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]


def test_inclusive_only_adds_when_a_term_lands_on_stop() -> None:
    result = list(date_range(date(2026, 1, 1), date(2026, 1, 4), step="2 days", inclusive=True))
    assert result == [date(2026, 1, 1), date(2026, 1, 3)]


def test_negative_step_descends() -> None:
    result = list(date_range(date(2026, 1, 5), date(2026, 1, 2), step="-1 day"))
    assert result == [date(2026, 1, 5), date(2026, 1, 4), date(2026, 1, 3)]


def test_negative_monthly_step_descends_with_clamping() -> None:
    result = list(date_range(date(2026, 3, 31), count=3, step="-1 month"))
    assert result == [date(2026, 3, 31), date(2026, 2, 28), date(2026, 1, 31)]


def test_empty_when_start_equals_stop_exclusive() -> None:
    assert list(date_range(date(2026, 1, 1), date(2026, 1, 1))) == []


def test_inclusive_single_point_when_start_equals_stop() -> None:
    assert list(date_range(date(2026, 1, 1), date(2026, 1, 1), inclusive=True)) == [
        date(2026, 1, 1)
    ]


def test_wrong_direction_is_empty_like_builtin_range() -> None:
    assert list(date_range(date(2026, 1, 5), date(2026, 1, 1))) == []


def test_zero_count_is_empty() -> None:
    assert list(date_range(date(2026, 1, 1), count=0)) == []


def test_plural_and_singular_units_are_equivalent() -> None:
    a = list(date_range(date(2026, 1, 1), count=2, step="week"))
    b = list(date_range(date(2026, 1, 1), count=2, step="weeks"))
    assert a == b


def test_requires_exactly_one_of_stop_or_count() -> None:
    with pytest.raises(ValueError):
        list(date_range(date(2026, 1, 1)))
    with pytest.raises(ValueError):
        list(date_range(date(2026, 1, 1), date(2026, 1, 5), count=3))


def test_rejects_zero_step() -> None:
    with pytest.raises(ValueError):
        date_range(date(2026, 1, 1), count=3, step="0 days")


def test_rejects_unknown_step_unit() -> None:
    with pytest.raises(ValueError):
        date_range(date(2026, 1, 1), count=3, step="fortnight")


def test_rejects_negative_count() -> None:
    with pytest.raises(ValueError):
        date_range(date(2026, 1, 1), count=-1)


def test_validation_happens_before_iteration() -> None:
    with pytest.raises(ValueError):
        date_range(date(2026, 1, 1), step="never")
