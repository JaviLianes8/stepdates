"""Calendar arithmetic on dates and wall clock datetimes."""

from __future__ import annotations

import calendar
from datetime import MAXYEAR, MINYEAR, date, datetime, timedelta, timezone
from typing import TypeVar, cast

from stepdates._step import Step

D = TypeVar("D", bound=date)

_OUT_OF_RANGE = "the result falls outside the supported years 1 to 9999"


def is_month_end(value: date) -> bool:
    return value.day == calendar.monthrange(value.year, value.month)[1]


def exists(value: date) -> bool:
    """False for an aware wall time that a DST gap skips (RFC 5545 3.3.10 ignores those)."""
    if not isinstance(value, datetime) or value.utcoffset() is None:
        return True
    try:
        back = value.astimezone(timezone.utc).astimezone(value.tzinfo)
    except OverflowError:
        return True
    return back.replace(tzinfo=None, fold=0) == value.replace(tzinfo=None, fold=0)


def instant(value: date) -> date:
    """An aware datetime as UTC, so comparisons ignore which zone object it carries."""
    if not isinstance(value, datetime) or value.utcoffset() is None:
        return value
    try:
        return value.astimezone(timezone.utc)
    except OverflowError:  # within hours of year 1 or 9999 the wall clock has to do
        return value


def term(start: D, step: Step, index: int, end_of_month: bool) -> tuple[D, bool]:
    """The ``index``-th value from ``start`` and whether it needed no clamping.

    Every term is measured from ``start``, so a clamped day never drifts. Raises
    ``OverflowError`` outside years 1 to 9999.
    """
    if index == 0:
        return start, True
    if step.days:
        try:
            value = start + timedelta(days=step.days * index)
        except OverflowError:
            raise OverflowError(_OUT_OF_RANGE) from None
        return _first_fold(value), True
    position = start.month - 1 + step.months * index
    year = start.year + position // 12
    if not MINYEAR <= year <= MAXYEAR:
        raise OverflowError(_OUT_OF_RANGE)
    month = position % 12 + 1
    last = calendar.monthrange(year, month)[1]
    day = last if end_of_month else min(start.day, last)
    shifted = start.replace(year=year, month=month, day=day)
    return _first_fold(shifted), end_of_month or start.day <= last


def _first_fold(value: D) -> D:
    # RFC 5545 3.3.5: an ambiguous wall time means its first occurrence, which is fold=0.
    if isinstance(value, datetime) and value.fold:
        return cast(D, value.replace(fold=0))
    return value
