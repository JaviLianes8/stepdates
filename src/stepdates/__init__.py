"""A range() for dates: iterate from start to stop by calendar day, week, month or year.

Public names: :func:`date_range`, :func:`shift` and :data:`InvalidPolicy`, the
``Literal["clamp", "skip"]`` type of the ``invalid`` argument of :func:`date_range`.

>>> from datetime import date
>>> from stepdates import InvalidPolicy, date_range
>>> policy: InvalidPolicy = "skip"
>>> [d.month for d in date_range(date(2026, 1, 31), count=4, step="month", invalid=policy)]
[1, 3, 5, 7]
>>> InvalidPolicy.__args__
('clamp', 'skip')
"""

from __future__ import annotations

from stepdates._range import InvalidPolicy, date_range, shift

__version__ = "1.0.0"

__all__ = ["InvalidPolicy", "date_range", "shift"]
