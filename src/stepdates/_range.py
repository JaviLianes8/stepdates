"""A calendar-aware ``range()`` for dates and datetimes."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta
from typing import Literal

from stepdates._calendar import D, exists, term
from stepdates._step import Step, parse_step
from stepdates._validate import check_end_of_month, check_start, check_stop

InvalidPolicy = Literal["clamp", "skip"]
_POLICIES = ("clamp", "skip")


def date_range(
    start: D,
    stop: D | None = None,
    *,
    step: str | timedelta = "day",
    count: int | None = None,
    inclusive: bool = False,
    invalid: InvalidPolicy = "clamp",
    end_of_month: bool = False,
) -> Iterator[D]:
    """Iterate dates (or datetimes) from ``start`` by a calendar ``step``.

    Give exactly one of ``stop`` or ``count``. With ``stop`` the range is half-open
    (``stop`` excluded) unless ``inclusive`` is set; a range that would leave years 1 to
    9999 simply ends. With ``count`` exactly that many values are produced, or
    ``OverflowError`` is raised when the range leaves those years.

    ``step`` is a unit (``"day"``, ``"week"``, ``"month"``, ``"quarter"``, ``"year"``) with
    an optional signed count such as ``"2 weeks"`` or ``"-1 month"``, an ISO 8601 duration
    such as ``"P1M"`` or ``"-P2W"``, or a whole-day ``timedelta``. Every term is measured
    from ``start``, so a clamped day never drifts.

    ``invalid`` says what happens to a term that does not exist: ``"clamp"`` moves 31
    January plus one month to 28 February, ``"skip"`` drops it and does not count it (the
    RFC 5545 recurrence rule, which also drops wall times inside a DST gap).
    ``end_of_month`` keeps a month-end ``start`` on the last day of every month.
    """
    check_start(start)
    parsed = parse_step(step)
    if (stop is None) == (count is None):
        raise ValueError("pass exactly one of stop or count")
    if count is not None:
        if isinstance(count, bool) or not isinstance(count, int):
            raise TypeError(f"count must be an int, not {type(count).__name__}")
        if count < 0:
            raise ValueError("count must not be negative")
        if inclusive:
            raise ValueError("inclusive only applies to a stop, not to a count")
    if stop is not None:
        check_stop(start, stop)
    if invalid not in _POLICIES:
        raise ValueError(f"invalid must be one of {_POLICIES}, not {invalid!r}")
    check_end_of_month(start, parsed, end_of_month)
    return _generate(start, stop, parsed, count, inclusive, invalid == "skip", end_of_month)


def shift(value: D, step: str | timedelta, *, end_of_month: bool = False) -> D:
    """Move ``value`` by one ``step``, clamping to the last day of a shorter month.

    ``shift(date(2026, 1, 31), "1 month")`` is 28 February 2026. ``end_of_month`` moves a
    month end to the last day of the target month. Raises ``OverflowError`` outside years
    1 to 9999.
    """
    check_start(value)
    parsed = parse_step(step)
    check_end_of_month(value, parsed, end_of_month)
    return term(value, parsed, 1, end_of_month)[0]


def _generate(
    start: D,
    stop: D | None,
    step: Step,
    count: int | None,
    inclusive: bool,
    skip: bool,
    end_of_month: bool,
) -> Iterator[D]:
    index = produced = 0
    while count is None or produced < count:
        try:
            value, fits = term(start, step, index, end_of_month)
        except OverflowError:
            if count is None:
                return
            raise OverflowError(
                f"the range leaves the supported years 1 to 9999 after {produced} values"
            ) from None
        # A clamped term sits in the same month as the dropped one, so it is a safe bound.
        if stop is not None and _beyond(value, stop, step.forward, inclusive):
            return
        index += 1
        if skip and index > 1 and not (fits and exists(value)):
            continue
        yield value
        produced += 1


def _beyond(value: date, stop: date, forward: bool, inclusive: bool) -> bool:
    if value == stop:
        return not inclusive
    return value > stop if forward else value < stop
