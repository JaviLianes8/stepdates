"""Unusual tzinfo objects and aware month ends, with both conventions."""

from __future__ import annotations

from datetime import datetime, timedelta, tzinfo

import pytest

from stepdates import date_range

HOUR = timedelta(hours=1)


class _DstNone(tzinfo):
    """A fixed offset whose dst() is None, which the tzinfo documentation allows."""

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return HOUR

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "plus one"


class _NoDst(tzinfo):
    """A fixed offset whose dst() is left as the tzinfo base class has it."""

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return HOUR

    def dst(self, dt: datetime | None) -> timedelta | None:
        raise NotImplementedError("a tzinfo subclass must implement dst()")

    def tzname(self, dt: datetime | None) -> str:
        return "plus one"


class _NoOffset(tzinfo):
    """A tzinfo whose utcoffset is None: Python counts such a datetime as naive."""

    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none"


def _wall(values: list[datetime]) -> list[datetime]:
    return [value.replace(tzinfo=None) for value in values]


@pytest.mark.parametrize(
    "zone", [_DstNone(), _NoDst(), _NoOffset()], ids=lambda zone: type(zone).__name__
)
@pytest.mark.parametrize("step", ["day", "month", "-1 month"])
def test_skip_with_a_zone_without_gaps_follows_the_naive_range(zone: tzinfo, step: str) -> None:
    naive = datetime(2026, 1, 31, 9)
    aware = list(date_range(naive.replace(tzinfo=zone), count=4, step=step, invalid="skip"))
    assert _wall(aware) == list(date_range(naive, count=4, step=step, invalid="skip"))
    assert all(value.tzinfo is aware[0].tzinfo for value in aware)


@pytest.mark.parametrize("zone", [_DstNone(), _NoDst()], ids=lambda zone: type(zone).__name__)
def test_skip_with_a_zone_without_gaps_and_a_stop(zone: tzinfo) -> None:
    start = datetime(2026, 1, 31, 9, tzinfo=zone)
    stop = datetime(2026, 6, 1, tzinfo=zone)
    days = [value.day for value in date_range(start, stop, step="month", invalid="skip")]
    assert days == [31, 31, 31]


def test_a_naive_start_takes_an_offsetless_stop_and_the_mirror() -> None:
    naive, offsetless = datetime(2026, 1, 1), datetime(2026, 1, 3, tzinfo=_NoOffset())
    assert list(date_range(naive, offsetless)) == [naive, naive.replace(day=2)]
    start = naive.replace(tzinfo=_NoOffset())
    assert list(date_range(start, datetime(2026, 1, 3))) == [start, start.replace(day=2)]
    with pytest.raises(TypeError, match="naive or both be aware"):
        date_range(naive.replace(tzinfo=_DstNone()), offsetless)


def test_an_aware_month_end_inside_a_gap_is_dropped_by_skip() -> None:
    zoneinfo = pytest.importorskip("zoneinfo")
    try:
        madrid = zoneinfo.ZoneInfo("Europe/Madrid")
    except zoneinfo.ZoneInfoNotFoundError:  # pragma: no cover - no tz database installed
        pytest.skip("no time zone database")
    start = datetime(2024, 1, 31, 2, 30, tzinfo=madrid)
    kept = date_range(start, count=4, step="month", end_of_month=True)
    assert [(v.month, v.day) for v in kept] == [(1, 31), (2, 29), (3, 31), (4, 30)]
    skipped = date_range(start, count=4, step="month", end_of_month=True, invalid="skip")
    assert [(v.month, v.day) for v in skipped] == [(1, 31), (2, 29), (4, 30), (5, 31)]
