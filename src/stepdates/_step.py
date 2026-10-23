"""Parse a step into whole months or whole days."""

from __future__ import annotations

import re
from datetime import timedelta
from typing import NamedTuple

from stepdates._quote import quote

_UNITS = ("day", "week", "month", "quarter", "year")
_UNIT_DAYS = {"day": 1, "week": 7}
_UNIT_MONTHS = {"month": 1, "quarter": 3, "year": 12}
_SPACE = " \t\n\r\f\v"
# Matched after the outer ASCII whitespace is stripped, so no two blank runs touch and the
# match stays linear in the length of the text.
_WORDS = re.compile(
    r"(?P<count>[+-]?[0-9]+)?[ \t\n\r\f\v]*(?P<unit>day|week|month|quarter|year)s?",
    re.IGNORECASE | re.ASCII,
)
# RFC 3339 Appendix A duration grammar, date part only, with the sign of RFC 5545 3.3.6.
_DURATION = re.compile(
    r"(?P<sign>[+-])?P(?:(?P<weeks>[0-9]+)W"
    r"|(?:(?P<years>[0-9]+)Y)?(?:(?P<months>[0-9]+)M)?(?:(?P<days>[0-9]+)D)?)",
    re.ASCII,
)
# A step of 10**18 days or months leaves years 1 to 9999 at once; longer numbers are refused
# before int() meets the interpreter's digit limit.
MAX_DIGITS = 18


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
    text = step.strip(_SPACE) if step.isascii() else ""
    parsed = _from_words(step, text) or _from_duration(step, text.upper())
    if parsed is None:
        raise ValueError(
            f"invalid step {quote(step)}: use a unit {_UNITS} with an optional signed count, "
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


def _number(step: str, digits: str) -> int:
    if len(digits.lstrip("+-")) > MAX_DIGITS:
        raise ValueError(f"invalid step {quote(step)}: a size has more than {MAX_DIGITS} digits")
    return int(digits)


def _from_words(step: str, text: str) -> Step | None:
    match = _WORDS.fullmatch(text)
    if match is None:
        return None
    size = _number(step, match.group("count")) if match.group("count") else 1
    unit = match.group("unit").lower()
    if unit in _UNIT_DAYS:
        return Step(0, size * _UNIT_DAYS[unit])
    return Step(size * _UNIT_MONTHS[unit], 0)


def _from_duration(step: str, text: str) -> Step | None:
    match = _DURATION.fullmatch(text)
    if match is None or not any(match.group(k) for k in ("weeks", "years", "months", "days")):
        return None
    if match.group("years") and match.group("days") and not match.group("months"):
        return None  # the grammar lets days follow months only
    sign = -1 if match.group("sign") == "-" else 1
    weeks, years, months, days = (
        _number(step, match.group(k) or "0") for k in ("weeks", "years", "months", "days")
    )
    if weeks:
        return Step(0, sign * 7 * weeks)
    months += 12 * years
    if months and days:
        raise ValueError(
            f"invalid step {quote(step)}: a duration that mixes months or years with days has "
            "no single order of application; give one of them"
        )
    return Step(sign * months, sign * days)
