"""A calendar-aware ``range()`` for dates."""

from __future__ import annotations

import calendar
import re
from collections.abc import Iterator
from datetime import date, timedelta

_UNITS = ("day", "week", "month", "year")
_STEP_PATTERN = re.compile(
    r"^\s*(?P<count>[+-]?\d+)?\s*(?P<unit>day|week|month|year)s?\s*$",
    re.IGNORECASE,
)


def _parse_step(step: str) -> tuple[int, str]:
    """Split a step like ``"day"``, ``"2 weeks"`` or ``"-1 month"`` into (size, unit)."""
    match = _STEP_PATTERN.match(step)
    if match is None:
        raise ValueError(
            f"invalid step {step!r}: use a unit {_UNITS} with an optional signed count, "
            'for example "day", "2 weeks" or "-1 month"'
        )
    size = int(match.group("count")) if match.group("count") else 1
    if size == 0:
        raise ValueError("step size must not be zero")
    return size, match.group("unit").lower()


def _add_months(start: date, months: int) -> date:
    """Shift by whole months, clamping the day to the target month's last day."""
    index = start.month - 1 + months
    year = start.year + index // 12
    month = index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _term(start: date, unit: str, size: int, index: int) -> date:
    """The ``index``-th value, anchored on ``start`` so clamping never drifts."""
    offset = size * index
    if unit == "day":
        return start + timedelta(days=offset)
    if unit == "week":
        return start + timedelta(weeks=offset)
    if unit == "month":
        return _add_months(start, offset)
    return _add_months(start, offset * 12)


def _generate(
    start: date,
    stop: date | None,
    size: int,
    unit: str,
    count: int | None,
    inclusive: bool,
) -> Iterator[date]:
    if count is not None:
        for index in range(count):
            yield _term(start, unit, size, index)
        return
    assert stop is not None
    index = 0
    while True:
        value = _term(start, unit, size, index)
        if size > 0:
            reached = value < stop or (inclusive and value == stop)
        else:
            reached = value > stop or (inclusive and value == stop)
        if not reached:
            return
        yield value
        index += 1


def date_range(
    start: date,
    stop: date | None = None,
    *,
    step: str = "day",
    count: int | None = None,
    inclusive: bool = False,
) -> Iterator[date]:
    """Iterate dates from ``start`` by a calendar ``step``.

    Give exactly one of ``stop`` or ``count``. With ``stop`` the range is half-open
    (``stop`` excluded) unless ``inclusive`` is set. ``step`` is a unit (``"day"``,
    ``"week"``, ``"month"``, ``"year"``) with an optional signed count such as
    ``"2 weeks"`` or ``"-1 month"``; a negative step walks backwards. Month and year
    steps clamp to the last valid day, so 31 January plus one month is 28 February and
    each term is measured from ``start`` (so the day of month never drifts).
    """
    size, unit = _parse_step(step)
    if (stop is None) == (count is None):
        raise ValueError("pass exactly one of stop or count")
    if count is not None and count < 0:
        raise ValueError("count must not be negative")
    return _generate(start, stop, size, unit, count, inclusive)
