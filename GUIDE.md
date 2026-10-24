# stepdates guide

The whole public API is `date_range`, `shift` and the `InvalidPolicy` type, all imported from
`stepdates`. Everything in this guide is part of the 1.0 promise: it changes only in a new
major version.

## Signatures

```
date_range(start, stop=None, *, step="day", count=None, inclusive=False,
           invalid="clamp", end_of_month=False) -> Iterator[same type as start]
shift(value, step, *, end_of_month=False) -> same type as value
InvalidPolicy = Literal["clamp", "skip"]
```

`date_range` checks every argument when it is called and returns a lazy iterator. Give exactly
one of `stop` (half-open, or closed with `inclusive=True`) and `count`.

## Steps

| Form | Examples | Meaning |
| --- | --- | --- |
| unit word, optional signed count | `"day"`, `"3 days"`, `"-2 weeks"`, `"quarter"`, `"10 YEARS"` | day, week (7 days), month, quarter (3 months), year (12 months) |
| ISO 8601 duration, date part | `"P1D"`, `"P2W"`, `"P1M"`, `"P1Y6M"`, `"-P1W"`, `"+P3M"` | RFC 3339 Appendix A grammar with the sign of RFC 5545 3.3.6 |
| `timedelta` | `timedelta(days=-7)` | whole days only |

Unit words and durations ignore case and surrounding ASCII whitespace. Between the count and
the unit of a unit word, any ASCII whitespace or none may stand (`"2weeks"`, `"2 weeks"`, a tab).
Digits are ASCII and a size has at most 18 digits. A duration that mixes months or years with days (`"P1M2D"`) is
refused, because a month and two days from 30 January has no single answer. A zero step is
refused. Times inside a duration (`"PT1H"`) are not steps.

## Month ends

Every term is measured from `start` (term n is `start` plus n steps), so a short month never
pulls the day down for good. What happens to a day the target month lacks is the `invalid`
argument:

```python
from datetime import date

from stepdates import date_range

start = date(2024, 1, 31)
print([str(d) for d in date_range(start, count=3, step="month")])
# ['2024-01-31', '2024-02-29', '2024-03-31']
print([str(d) for d in date_range(start, count=3, step="month", invalid="skip")])
# ['2024-01-31', '2024-03-31', '2024-05-31']
print([str(d) for d in date_range(date(2024, 2, 29), count=3, step="month", end_of_month=True)])
# ['2024-02-29', '2024-03-31', '2024-04-30']
```

- `"clamp"` (default): the last day of the shorter month.
- `"skip"`: the term is dropped and not counted, the RFC 5545 reading (3.3.10). `start` is
  always the first value. With a `stop`, the range still ends at the first term past it,
  dropped or not.
- `end_of_month=True`: from a `start` on the last day of its month, every term is the last
  day of its month. It needs a month, quarter or year step; anything else is a `ValueError`.
  For dates and naive datetimes such terms always exist, so `invalid` changes nothing. An aware
  month end can still fall in a DST gap, and `invalid="skip"` drops it as any other gap time.

`shift(value, step, *, end_of_month=False)` is the second term of the same range: one step,
clamped.

## Datetimes and time zones

A `datetime` start gives `datetime` values with its time and `tzinfo`. Steps move the wall
clock (09:00 stays 09:00 across a clock change). A term that lands on a wall time twice
takes the first occurrence (`fold=0`); a term inside a gap keeps that wall time, which
`astimezone()` reads with the offset before the gap. With `invalid="skip"` a term inside a
gap is dropped instead (RFC 5545 3.3.5 and 3.3.10). A `tzinfo` whose `dst()` returns `None` or
is not implemented, and that keeps the default `fromutc()`, cannot convert from UTC, so it has
no gap to find and nothing is dropped for it; one that implements its own `fromutc()` has its
gaps found as usual. A `tzinfo` whose `utcoffset()` is `None` makes the value naive, as Python
counts it. `stop` must match `start`: both dates, both naive or both aware. An aware `stop` is
compared as an instant.

The example uses `zoneinfo`, which reads the system's IANA time zone database. Windows has none,
so there (or on any system without one) run `pip install tzdata` first.

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from stepdates import date_range

madrid = ZoneInfo("Europe/Madrid")
start = datetime(2026, 3, 28, 2, 30, tzinfo=madrid)
print([d.day for d in date_range(start, count=3)])
# [28, 29, 30]
print([d.day for d in date_range(start, count=3, invalid="skip")])
# [28, 30, 31]
until = datetime(2026, 3, 30, 0, 30, tzinfo=timezone.utc)
print([d.day for d in date_range(start, until, inclusive=True)])
# [28, 29, 30]
```

## Errors

Every error names the argument at fault (`value` for `shift`, `start` for `date_range`) and
quotes it as its `repr` with at most 80 characters between the quotes, control characters
escaped. A value that does not fit is cut between two of its characters and followed by its
length.

| Raised | When |
| --- | --- |
| `TypeError` | `start` or `stop` (or the `value` of `shift`) is not a `date`; a `date` is mixed with a `datetime`, or naive with aware; `step` is neither `str` nor `timedelta`; `count` is not an `int` (a `bool` is refused); `invalid` is not a `str`; `inclusive` or `end_of_month` is not a `bool` |
| `ValueError` | both or neither of `stop` and `count`; a negative `count`; `inclusive` with `count`; a step that cannot be read, is zero, has more than 18 digits, is not whole days or mixes months with days; an `invalid` other than `"clamp"` and `"skip"`; `end_of_month` without a month-end start and a month, quarter or year step |
| `OverflowError` | `shift` leaves years 1 to 9999; a `count` range does so after the values that fit (raised by the iterator) |

A `stop` range never raises at the edges of the calendar: it ends.

## Command line

```
stepdates START [STOP] [-n COUNT] [-s STEP] [--inclusive] [--skip-invalid]
          [--end-of-month] [-f FORMAT] [--version]
```

The options map to the arguments of `date_range`; `python -m stepdates` is the same tool. START
and STOP are read by `date.fromisoformat`, then `datetime.fromisoformat`. Output is one ISO 8601
value per line, or a `strftime` pattern with `--format`. A dash-led step works without `=`:
`-s -P1M`. Options, known or not, may come before, between or after START and STOP, and every
argument after `--` is START or STOP; this reads the same on every supported Python, error
messages included. Exit status: 0 on success
(also when the reader closes the pipe early), 1 when a count runs past year 9999 (after printing
the values that fit), 2 for bad input, which includes a `--format` whose output the encoding of
standard output cannot hold, and when there is no standard output at all (whatever the
arguments, `--help` and `--version` included). Error messages, also the ones about unknown or
malformed options, quote at most 80 characters of an argument (one with a character that is
not printable is quoted too, with its escapes) and list at most three unrecognized arguments
(then how many more there are); a message over 500 characters is cut there and followed by
its length.

## Typing

The package ships `py.typed` and passes `mypy --strict`. `date_range` and `shift` are generic
over the type of `start`: a `date` gives `Iterator[date]`, a `datetime` gives
`Iterator[datetime]`, a `date` subclass keeps its class. `InvalidPolicy` is the type of the
`invalid` argument, for code that passes it along.
