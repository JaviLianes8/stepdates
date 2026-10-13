"""Argument checks that run before any value is produced."""

from __future__ import annotations

from datetime import date, datetime

from stepdates._calendar import is_month_end
from stepdates._step import Step


def check_start(start: object) -> None:
    if not isinstance(start, date):
        raise TypeError(f"start must be a date or a datetime, not {type(start).__name__}")


def check_stop(start: date, stop: object) -> None:
    """RFC 5545 asks UNTIL to share the value type of DTSTART; so does ``stop``."""
    if not isinstance(stop, date):
        raise TypeError(f"stop must be a date or a datetime, not {type(stop).__name__}")
    if isinstance(start, datetime) != isinstance(stop, datetime):
        raise TypeError("start and stop must both be dates or both be datetimes")
    aware = isinstance(start, datetime) and start.utcoffset() is not None
    if isinstance(stop, datetime) and aware != (stop.utcoffset() is not None):
        raise TypeError("start and stop must both be naive or both be aware")


def check_end_of_month(start: date, step: Step, end_of_month: bool) -> None:
    if not end_of_month:
        return
    if not step.months:
        raise ValueError("end_of_month needs a month, quarter or year step")
    if not is_month_end(start):
        raise ValueError(f"end_of_month needs a start on the last day of its month, not {start}")
