"""Cross-check against python-dateutil, used here as an oracle and never at runtime."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta

import pytest

from stepdates import date_range

rrule = pytest.importorskip("dateutil.rrule")
relativedelta = pytest.importorskip("dateutil.relativedelta").relativedelta

SEEDS = range(400)
UNITS = {"day": rrule.DAILY, "week": rrule.WEEKLY, "month": rrule.MONTHLY, "year": rrule.YEARLY}


def _case(seed: int) -> tuple[date, str, int, int]:
    rng = random.Random(seed)
    start = date(1990, 1, 1) + timedelta(days=rng.randrange(15000))
    if rng.random() < 0.5:  # month ends and leap days are where conventions differ
        start = start.replace(day=28) + timedelta(days=rng.choice([1, 2, 3, 4]))
    unit = rng.choice(list(UNITS))
    return start, unit, rng.randint(1, 7), rng.randint(0, 30)


@pytest.mark.parametrize("seed", SEEDS)
def test_skip_with_count_matches_rrule(seed: int) -> None:
    start, unit, interval, count = _case(seed)
    expected = rrule.rrule(UNITS[unit], dtstart=start, interval=interval, count=count)
    got = date_range(start, count=count, step=f"{interval} {unit}", invalid="skip")
    assert list(got) == [value.date() for value in expected]


@pytest.mark.parametrize("seed", SEEDS)
def test_skip_with_inclusive_stop_matches_rrule_until(seed: int) -> None:
    start, unit, interval, count = _case(seed)
    stop = start + timedelta(days=count * 40)
    until = datetime.combine(stop, datetime.min.time())
    expected = rrule.rrule(UNITS[unit], dtstart=start, interval=interval, until=until)
    got = date_range(start, stop, step=f"{interval} {unit}", invalid="skip", inclusive=True)
    assert list(got) == [value.date() for value in expected]


@pytest.mark.parametrize("seed", SEEDS)
def test_clamp_matches_relativedelta_both_ways(seed: int) -> None:
    start, unit, interval, count = _case(seed)
    sign = -1 if seed % 2 else 1
    months = {"day": 0, "week": 0, "month": 1, "year": 12}[unit]
    days = {"day": 1, "week": 7, "month": 0, "year": 0}[unit]
    expected = [
        start + relativedelta(months=sign * interval * months * i, days=sign * interval * days * i)
        for i in range(count)
    ]
    got = date_range(start, count=count, step=f"{sign * interval} {unit}")
    assert list(got) == expected


@pytest.mark.parametrize("seed", SEEDS)
def test_end_of_month_matches_rrule_last_day(seed: int) -> None:
    rng = random.Random(seed)
    first = date(1990 + rng.randrange(60), rng.randint(1, 12), 1)
    start = first + relativedelta(months=1) - timedelta(days=1)
    interval, count = rng.randint(1, 13), rng.randint(0, 30)
    expected = rrule.rrule(
        rrule.MONTHLY, dtstart=start, interval=interval, count=count, bymonthday=-1
    )
    got = date_range(start, count=count, step=f"{interval} months", end_of_month=True)
    assert list(got) == [value.date() for value in expected]


@pytest.mark.parametrize("zone", ["America/New_York", "Europe/Madrid", "Australia/Lord_Howe"])
@pytest.mark.parametrize("unit", list(UNITS))
def test_aware_wall_clock_matches_rrule(zone: str, unit: str) -> None:
    zoneinfo = pytest.importorskip("zoneinfo")
    start = datetime(2026, 1, 28, 2, 15, tzinfo=zoneinfo.ZoneInfo(zone))
    expected = rrule.rrule(UNITS[unit], dtstart=start, count=60)
    got = list(date_range(start, count=60, step=unit))
    assert [value.replace(tzinfo=None) for value in got] == [
        value.replace(tzinfo=None) for value in expected
    ]
    assert all(value.tzinfo is start.tzinfo for value in got)
