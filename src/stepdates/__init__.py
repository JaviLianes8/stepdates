"""A range() for dates: iterate from start to stop by calendar day, week, month or year."""

from __future__ import annotations

from stepdates._range import InvalidPolicy, date_range, shift

__version__ = "0.2.0"

__all__ = ["InvalidPolicy", "date_range", "shift"]
