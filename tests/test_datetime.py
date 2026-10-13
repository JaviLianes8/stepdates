"""Datetimes keep their type, time and zone; DST follows RFC 5545 3.3.5 and 3.3.10."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from stepdates import date_range, shift

zoneinfo = pytest.importorskip("zoneinfo")
try:
    NEW_YORK = zoneinfo.ZoneInfo("America/New_York")
    MADRID = zoneinfo.ZoneInfo("Europe/Madrid")
except zoneinfo.ZoneInfoNotFoundError:  # pragma: no cover - no tz database installed
    pytest.skip("no time zone database", allow_module_level=True)


def _utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


def test_naive_datetimes_keep_type_and_time() -> None:
    result = list(date_range(datetime(2026, 1, 31, 9, 15), count=3, step="month"))
    assert result == [
        datetime(2026, 1, 31, 9, 15),
        datetime(2026, 2, 28, 9, 15),
        datetime(2026, 3, 31, 9, 15),
    ]
    assert all(type(value) is datetime for value in result)


def test_microseconds_survive() -> None:
    start = datetime(2026, 1, 1, 0, 0, 0, 123456)
    assert next(iter(date_range(start, count=2, step="year"))) == start
    assert list(date_range(start, count=2, step="year"))[1].microsecond == 123456


def test_daily_steps_keep_the_wall_clock_across_dst() -> None:
    start = datetime(2026, 3, 28, 9, 0, tzinfo=MADRID)
    result = list(date_range(start, count=3))
    assert [value.hour for value in result] == [9, 9, 9]
    assert [value.utcoffset().total_seconds() / 3600 for value in result] == [1, 2, 2]  # type: ignore[union-attr]


def test_a_gap_time_is_read_with_the_offset_before_the_gap() -> None:
    # RFC 5545 3.3.5: New York 2007-03-11 02:30 means 03:30 EDT.
    start = datetime(2007, 3, 10, 2, 30, tzinfo=NEW_YORK)
    gap = list(date_range(start, count=2))[1]
    assert gap.replace(tzinfo=None) == datetime(2007, 3, 11, 2, 30)
    assert _utc(gap) == _utc(datetime(2007, 3, 11, 3, 30, tzinfo=NEW_YORK))


def test_skip_drops_a_gap_time_and_does_not_count_it() -> None:
    # RFC 5545 3.3.10: a nonexistent local time is ignored and not counted.
    start = datetime(2007, 3, 10, 2, 30, tzinfo=NEW_YORK)
    result = list(date_range(start, count=3, invalid="skip"))
    assert [value.day for value in result] == [10, 12, 13]


def test_skip_keeps_times_outside_the_gap() -> None:
    start = datetime(2007, 3, 10, 3, 30, tzinfo=NEW_YORK)
    result = list(date_range(start, count=3, invalid="skip"))
    assert [value.day for value in result] == [10, 11, 12]


def test_a_start_inside_a_gap_is_still_the_first_value() -> None:
    start = datetime(2007, 3, 11, 2, 30, tzinfo=NEW_YORK)
    result = list(date_range(start, count=2, step="week", invalid="skip"))
    assert result == [start, datetime(2007, 3, 18, 2, 30, tzinfo=NEW_YORK)]


def test_overlap_terms_take_the_first_occurrence() -> None:
    # RFC 5545 3.3.5: New York 2007-11-04 01:30 means 01:30 EDT, the first one.
    start = datetime(2007, 11, 3, 1, 30, tzinfo=NEW_YORK, fold=1)
    result = list(date_range(start, count=2))
    assert result[0].fold == 1
    assert result[1].fold == 0
    assert result[1].utcoffset().total_seconds() == -4 * 3600  # type: ignore[union-attr]


def test_month_steps_reset_fold_too() -> None:
    start = datetime(2007, 10, 4, 1, 30, tzinfo=NEW_YORK, fold=1)
    assert shift(start, "month").fold == 0


def test_aware_stop_in_another_zone_compares_as_instants() -> None:
    start = datetime(2026, 1, 1, 12, tzinfo=MADRID)
    stop = datetime(2026, 1, 3, 11, 30, tzinfo=timezone.utc)
    assert len(list(date_range(start, stop))) == 3


def test_fixed_offsets_never_skip() -> None:
    start = datetime(2007, 3, 10, 2, 30, tzinfo=timezone.utc)
    assert len(list(date_range(start, count=5, invalid="skip"))) == 5


def test_date_and_datetime_cannot_mix() -> None:
    with pytest.raises(TypeError, match="both be dates or both be datetimes"):
        date_range(datetime(2026, 1, 1), date(2026, 2, 1))
    with pytest.raises(TypeError, match="both be dates or both be datetimes"):
        date_range(date(2026, 1, 1), datetime(2026, 2, 1))


def test_naive_and_aware_cannot_mix() -> None:
    with pytest.raises(TypeError, match="naive"):
        date_range(datetime(2026, 1, 1), datetime(2026, 2, 1, tzinfo=timezone.utc))
