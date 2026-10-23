"""Seeded property tests: random steps and ranges against hand-written models.

The models below are written by hand from the README rules, independently of the library
code, and are labelled as such: they are not an external source.
"""

from __future__ import annotations

import calendar
import itertools
import random
from datetime import date, datetime, timedelta

import pytest

from stepdates import date_range, shift
from stepdates._step import Step, parse_step

SEEDS = [11, 2026, 90210]
ALPHABET = (
    "PWYMDpwymd0123456789+- " + chr(9) + "dayweekmonthquarteryears" + chr(0xA0) + chr(0x2003) + "x."
)
UNITS = {"day": (0, 1), "week": (0, 7), "month": (1, 0), "quarter": (3, 0), "year": (12, 0)}


def _model_step(text: str) -> Step | None:
    """Hand-written reading of the step grammar, character by character."""
    if not text.isascii():
        return None
    body = text.strip(" \t\n\r\f\v")
    sign, rest = 1, body
    if rest[:1] in "+-" and rest[:1]:
        sign, rest = (-1 if rest[0] == "-" else 1), rest[1:]
    digits = ""
    while rest[:1].isdigit():
        digits, rest = digits + rest[0], rest[1:]
    unit = rest.lstrip(" \t\n\r\f\v").lower()
    unit = unit[:-1] if unit.endswith("s") and unit[:-1] in UNITS else unit
    if unit in UNITS and (digits or body[:1] not in "+-" or not body):
        size = sign * (int(digits) if digits else 1)
        months, days = UNITS[unit]
        return Step(size * months, size * days)
    upper = body.upper()
    sign = -1 if upper.startswith("-") else 1
    upper = upper[1:] if upper[:1] in "+-" else upper
    if not upper.startswith("P") or len(upper) < 3:
        return None
    parts, number = {}, ""
    for char in upper[1:]:
        if char.isdigit():
            number += char
        elif char in "WYMD" and number and char not in parts:
            parts[char], number = int(number), ""
        else:
            return None
    order = "".join(parts)
    if number or order not in ("W", "Y", "M", "D", "YM", "MD", "YMD"):
        return None
    if "W" in parts:
        return Step(0, sign * 7 * parts["W"])
    months = 12 * parts.get("Y", 0) + parts.get("M", 0)
    return Step(sign * months, sign * parts.get("D", 0))


@pytest.mark.parametrize("seed", SEEDS)
def test_random_steps_match_the_model(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(20_000):
        text = "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 9)))
        expected = _model_step(text)
        if expected is None or expected == Step(0, 0) or (expected.months and expected.days):
            with pytest.raises(ValueError) as caught:
                parse_step(text)
            assert len(str(caught.value)) < 300
        else:
            assert parse_step(text) == expected, text


def _model_term(start: date, months: int, days: int, index: int) -> date | None:
    """Clamped term ``index`` measured from ``start`` (hand-written), None outside 1..9999."""
    if days:
        try:
            return start + timedelta(days=days * index)
        except OverflowError:
            return None
    position = start.year * 12 + start.month - 1 + months * index
    year, month = divmod(position, 12)
    if not 1 <= year <= 9999:
        return None
    return start.replace(year=year, month=month + 1, day=min(start.day, _last(year, month + 1)))


def _last(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _random_case(rng: random.Random) -> tuple[date, str, int, int]:
    start: date = date(1, 1, 1) + timedelta(days=rng.randrange(3_652_059))
    if rng.random() < 0.5:
        start = start.replace(day=min(28 + rng.randint(0, 3), _last(start.year, start.month)))
    if rng.random() < 0.3:
        start = datetime.combine(start, datetime.min.time()).replace(hour=rng.randrange(24))
    unit = rng.choice(list(UNITS))
    size = rng.choice([-1, 1]) * rng.choice([1, 1, 2, 3, 7, 12, 100, 1000])
    months, days = UNITS[unit]
    return start, f"{size} {unit}", size * months, size * days


@pytest.mark.parametrize("seed", SEEDS)
def test_clamped_ranges_match_the_model_and_shift(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(2_000):
        start, step, months, days = _random_case(rng)
        count = rng.randint(0, 40)
        model = [_model_term(start, months, days, i) for i in range(count)]
        if None in model:
            fits = model.index(None)
            values = date_range(start, count=count, step=step)
            assert [next(values) for _ in range(fits)] == model[:fits]
            with pytest.raises(OverflowError):
                next(values)
            continue
        got = list(date_range(start, count=count, step=step))
        assert got == model, (start, step)
        if len(got) > 1:
            assert shift(start, step) == got[1]
            assert all(type(value) is type(start) for value in got)


@pytest.mark.parametrize("seed", SEEDS)
def test_skip_keeps_exactly_the_terms_that_needed_no_clamping(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(2_000):
        start, step, months, days = _random_case(rng)
        stop = _model_term(start, months, days, 60)
        if stop is None:
            continue
        clamped = list(date_range(start, stop, step=step, inclusive=True))
        kept = [v for i, v in enumerate(clamped) if i == 0 or v.day == start.day or days]
        assert list(date_range(start, stop, step=step, inclusive=True, invalid="skip")) == kept


@pytest.mark.parametrize("seed", SEEDS)
def test_a_stop_cuts_the_counted_range_where_the_model_says(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(2_000):
        start, step, months, days = _random_case(rng)
        full = [_model_term(start, months, days, i) for i in range(32)]
        if None in full:
            continue
        stop = full[rng.randrange(30)]
        assert stop is not None
        if rng.random() < 0.3:  # a stop between two terms
            stop = stop + timedelta(days=rng.choice([-1, 1]))
        forward = months > 0 or days > 0
        before = [v for v in full if v is not None and (v < stop if forward else v > stop)]
        exact = [v for v in full if v == stop]
        assert list(date_range(start, stop, step=step)) == before
        assert list(date_range(start, stop, step=step, inclusive=True)) == before + exact


@pytest.mark.parametrize("seed", SEEDS)
def test_end_of_month_lands_on_every_month_end(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(2_000):
        year, month = rng.randint(1, 9999), rng.randint(1, 12)
        start = date(year, month, _last(year, month))
        size = rng.choice([-1, 1]) * rng.randint(1, 30)
        stop = date.min if size < 0 else date.max
        got = list(
            itertools.islice(date_range(start, stop, step=f"{size} months", end_of_month=True), 50)
        )
        assert all(value.day == _last(value.year, value.month) for value in got)
        assert [(v.year * 12 + v.month - start.year * 12 - start.month) for v in got] == [
            size * i for i in range(len(got))
        ]
