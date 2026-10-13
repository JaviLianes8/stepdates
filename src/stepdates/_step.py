"""Parse a step into whole months or whole days."""

from __future__ import annotations

import re
from datetime import timedelta
from typing import NamedTuple

_UNITS = ("day", "week", "month", "quarter", "year")
_UNIT_DAYS = {"day": 1, "week": 7}
_UNIT_MONTHS = {"month": 1, "quarter": 3, "year": 12}
_WORDS = re.compile(
    r"^\s*(?P<count>[+-]?\d+)?\s*(?P<unit>day|week|month|quarter|year)s?\s*$",
    re.IGNORECASE,
)
# RFC 3339 Appendix A duration grammar, date part only, with the sign of RFC 5545 3.3.6.
_DURATION = re.compile(
    r"^(?P<sign>[+-])?P(?:(?P<weeks>\d+)W|(?:(?P<years>\d+)Y)?(?:(?P<months>\d+)M)?"
    r"(?:(?P<days>\d+)D)?)$"
)


class Step(NamedTuple):
    """A signed calendar step: exactly one of ``months`` and ``days`` is non-zero."""

    months: int
    days: int

    @property
    def forward(self) -> bool:
        return self.months > 0 or self.days > 0


def parse_step(step: str | timedelta) -> Step:
    """Read ``"2 weeks"``, ``"-1 month"``, ``"P3M"`` or a whole-day ``timedelta``."""
    if isinstance(step, timedelta):
        return _from_timedelta(step)
    if not isinstance(step, str):
        raise TypeError(f"step must be a str or a timedelta, not {type(step).__name__}")
    parsed = _from_words(step) or _from_duration(step)
    if parsed is None:
        raise ValueError(
            f"invalid step {step!r}: use a unit {_UNITS} with an optional signed count, "
            'for example "day", "2 weeks" or "-1 month", or an ISO 8601 duration such as "P1M"'
        )
    if parsed == Step(0, 0):
        raise ValueError("step size must not be zero")
    return parsed


def _from_timedelta(step: timedelta) -> Step:
    if step % timedelta(days=1):
        raise ValueError(f"a timedelta step must be whole days, got {step!r}")
    if not step:
        raise ValueError("step size must not be zero")
    return Step(0, step.days)


def _from_words(step: str) -> Step | None:
    match = _WORDS.match(step)
    if match is None:
        return None
    size = int(match.group("count")) if match.group("count") else 1
    unit = match.group("unit").lower()
    if unit in _UNIT_DAYS:
        return Step(0, size * _UNIT_DAYS[unit])
    return Step(size * _UNIT_MONTHS[unit], 0)


def _from_duration(step: str) -> Step | None:
    match = _DURATION.match(step.strip().upper())
    if match is None or not any(match.group(k) for k in ("weeks", "years", "months", "days")):
        return None
    sign = -1 if match.group("sign") == "-" else 1
    if match.group("weeks"):
        return Step(0, sign * 7 * int(match.group("weeks")))
    months = 12 * int(match.group("years") or 0) + int(match.group("months") or 0)
    days = int(match.group("days") or 0)
    if months and days:
        raise ValueError(
            f"invalid step {step!r}: a duration that mixes months or years with days has no "
            "single order of application; give one of them"
        )
    return Step(sign * months, sign * days)
