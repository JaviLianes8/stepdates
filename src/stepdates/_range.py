"""A calendar-aware ``range()`` for dates and datetimes."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta
from typing import Literal

from stepdates._calendar import D, exists, instant, term
from stepdates._quote import quote
from stepdates._step import Step, parse_step
from stepdates._validate import check_end_of_month, check_flags, check_start, check_stop

InvalidPolicy = Literal["clamp", "skip"]
"""The type of the ``invalid`` argument of :func:`date_range`: ``"clamp"`` or ``"skip"``.

>>> from datetime import date
>>> policy: InvalidPolicy = "clamp"
>>> [d.day for d in date_range(date(2026, 1, 31), count=2, step="month", invalid=policy)]
[31, 28]
>>> InvalidPolicy.__args__
('clamp', 'skip')
"""
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
    (``stop`` excluded) unless ``inclusive`` is set. An aware ``stop`` is compared as an
    instant, so a repeated wall time is ordered by its offset. A range that would leave
    years 1 to 9999 simply ends. With ``count`` exactly that many values are produced, or
    ``OverflowError`` is raised when the range leaves those years.

    ``step`` is a unit (``"day"``, ``"week"``, ``"month"``, ``"quarter"``, ``"year"``) with
    an optional signed count such as ``"2 weeks"`` or ``"-1 month"``, an ISO 8601 duration
    such as ``"P1M"`` or ``"-P2W"``, or a whole-day ``timedelta``. Every term is measured
    from ``start``, so a clamped day never drifts.

    ``invalid`` says what happens to a term that does not exist: ``"clamp"`` moves 31
    January plus one month to 28 February, ``"skip"`` drops it and does not count it (the
    RFC 5545 recurrence rule, which also drops wall times inside a DST gap).
    ``end_of_month`` keeps a month-end ``start`` on the last day of every month.

    Arguments are checked when the function is called; the values are produced lazily.

    Raises:
        TypeError: ``start`` or ``stop`` is not a date, they mix a ``date`` with a
            ``datetime`` or naive with aware, ``step`` is neither a ``str`` nor a
            ``timedelta``, ``count`` is not an ``int``, ``invalid`` is not a ``str``, or
            ``inclusive`` or ``end_of_month`` is not a ``bool``.
        ValueError: both or neither of ``stop`` and ``count``, a negative ``count``,
            ``inclusive`` with ``count``, a step that cannot be read or is zero, an
            ``invalid`` other than ``"clamp"`` or ``"skip"``, or ``end_of_month`` without a
            month-end ``start`` and a month, quarter or year step.
        OverflowError: during iteration, when ``count`` values do not fit in years 1 to
            9999.

    >>> from datetime import date
    >>> [str(d) for d in date_range(date(2026, 1, 31), count=3, step="month")]
    ['2026-01-31', '2026-02-28', '2026-03-31']
    >>> [str(d) for d in date_range(date(2026, 1, 31), count=3, step="P1M", invalid="skip")]
    ['2026-01-31', '2026-03-31', '2026-05-31']
    >>> [str(d) for d in date_range(date(2026, 1, 5), date(2026, 1, 1), step="-2 days")]
    ['2026-01-05', '2026-01-03']
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
    check_flags(inclusive=inclusive, end_of_month=end_of_month)
    if not isinstance(invalid, str):
        raise TypeError(f"invalid must be a str, not {type(invalid).__name__}")
    if invalid not in _POLICIES:
        raise ValueError(f"invalid must be one of {_POLICIES}, not {quote(invalid)}")
    check_end_of_month(start, parsed, end_of_month)
    return _generate(start, stop, parsed, count, inclusive, invalid == "skip", end_of_month)


def shift(value: D, step: str | timedelta, *, end_of_month: bool = False) -> D:
    """Move ``value`` by one ``step``, clamping to the last day of a shorter month.

    ``step`` reads as in :func:`date_range`. ``end_of_month`` moves a month end to the
    last day of the target month. A ``datetime`` keeps its time and ``tzinfo``.

    Raises:
        TypeError: ``value`` is not a date, ``step`` is neither a ``str`` nor a
            ``timedelta``, or ``end_of_month`` is not a ``bool``.
        ValueError: a step that cannot be read or is zero, or ``end_of_month`` without a
            month-end ``value`` and a month, quarter or year step.
        OverflowError: the result falls outside years 1 to 9999.

    >>> from datetime import date
    >>> shift(date(2026, 1, 31), "1 month")
    datetime.date(2026, 2, 28)
    >>> shift(date(2026, 2, 28), "month", end_of_month=True)
    datetime.date(2026, 3, 31)
    >>> shift(date(2024, 2, 29), "-P1Y")
    datetime.date(2023, 2, 28)
    """
    check_start(value, "value")
    parsed = parse_step(step)
    check_flags(end_of_month=end_of_month)
    check_end_of_month(value, parsed, end_of_month, "value")
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
                "the range leaves the supported years 1 to 9999 after "
                f"{produced} value{'' if produced == 1 else 's'}"
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
    value, stop = instant(value), instant(stop)
    if value == stop:
        return not inclusive
    return value > stop if forward else value < stop
