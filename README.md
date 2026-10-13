# stepdates

A range() for dates: iterate from start to stop by calendar day, week, month or year.

## Install

```
pip install stepdates
```

## Usage

```python
from datetime import date

from stepdates import date_range

# Half-open daily range, like range() but for dates.
print([str(d) for d in date_range(date(2026, 1, 1), date(2026, 1, 4))])
# ['2026-01-01', '2026-01-02', '2026-01-03']

# A count instead of a stop, and a step with a size.
print([str(d) for d in date_range(date(2026, 1, 1), count=3, step="2 weeks")])
# ['2026-01-01', '2026-01-15', '2026-01-29']

# A negative step walks backwards; inclusive keeps a stop the range lands on.
back = date_range(date(2026, 1, 5), date(2026, 1, 1), step="-2 days", inclusive=True)
print([str(d) for d in back])
# ['2026-01-05', '2026-01-03', '2026-01-01']
```

The full signature is `date_range(start, stop=None, *, step="day", count=None,
inclusive=False, invalid="clamp", end_of_month=False)`. Pass exactly one of `stop` or
`count`. The range is half-open (`stop` excluded) unless `inclusive=True`.
The result is a lazy iterator.

The `step` is one of:

- a unit, `"day"`, `"week"`, `"month"`, `"quarter"` or `"year"` (plural too), with an
  optional signed count: `"3 days"`, `"-1 month"`, `"2 quarters"`;
- an ISO 8601 duration with a date part, signed as in RFC 5545: `"P1D"`, `"P2W"`, `"P1M"`,
  `"P1Y6M"`, `"-P1W"`. A duration that mixes months or years with days (`"P1M2D"`) is
  rejected, because "a month and two days" from 30 January has no single answer;
- a `timedelta` of whole days.

## Month ends

A month or year step can land on a day the target month lacks, such as 31 February. Every
term is measured from `start`, never from the previous term, so a short month never drags the
day down for good. Three conventions are on offer:

```python
from datetime import date

from stepdates import date_range, shift

# invalid="clamp" (the default): use the last day of the shorter month.
print([str(d) for d in date_range(date(2026, 1, 31), count=4, step="month")])
# ['2026-01-31', '2026-02-28', '2026-03-31', '2026-04-30']

# invalid="skip": drop the missing day and do not count it, as RFC 5545 recurrences do.
print([str(d) for d in date_range(date(2026, 1, 31), count=4, step="month", invalid="skip")])
# ['2026-01-31', '2026-03-31', '2026-05-31', '2026-07-31']

# end_of_month=True: from a month end, stay on the last day of every month.
print([str(d) for d in date_range(date(2026, 4, 30), count=4, step="month", end_of_month=True)])
# ['2026-04-30', '2026-05-31', '2026-06-30', '2026-07-31']

# A leap day clamps to 28 February and comes back in the next leap year.
print([str(d) for d in date_range(date(2024, 2, 29), count=5, step="year")])
# ['2024-02-29', '2025-02-28', '2026-02-28', '2027-02-28', '2028-02-29']

# shift() takes one step with the same rules.
print(shift(date(2026, 1, 31), "1 month"), shift(date(2026, 2, 28), "month", end_of_month=True))
# 2026-02-28 2026-03-31
```

`shift(value, step, *, end_of_month=False)` takes a single step with the clamping rules.
The `invalid` argument is typed as `InvalidPolicy`, a `Literal["clamp", "skip"]` alias.
`end_of_month` needs a `start` on the last day of its month and a month, quarter or year step;
anything else raises `ValueError`. With `invalid="skip"` and a `stop`, the range still ends at
the first term past the stop, skipped or not.

## Datetimes and time zones

A `datetime` start gives `datetime` values with the same time and `tzinfo`. Steps are calendar
steps on the wall clock, as in RFC 5545: one day after 09:00 is 09:00 the next day, whether or
not the clocks changed overnight. `stop` must be the same kind of value as `start` (date with
date, naive with naive, aware with aware), or `TypeError` is raised.

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from stepdates import date_range

new_york = ZoneInfo("America/New_York")
start = datetime(2007, 3, 10, 2, 30, tzinfo=new_york)

# 02:30 on 11 March 2007 never happened in New York; it reads as 03:30 EDT (RFC 5545 3.3.5).
day = list(date_range(start, count=2))[1]
print(day.time(), day.astimezone(timezone.utc).time())
# 02:30:00 07:30:00

# With invalid="skip" that wall time is dropped and not counted (RFC 5545 3.3.10).
print([d.day for d in date_range(start, count=3, invalid="skip")])
# [10, 12, 13]
```

Every term after `start` has `fold=0`, so a wall time that happens twice (when the clocks go
back) means its first occurrence, and a wall time inside a gap is read with the offset in force
before the gap. Both are the RFC 5545 readings, and both are what `astimezone()` does with
`fold=0`. `start` itself is returned as given. An aware `stop` is compared as an instant,
so 01:30 before the clocks go back comes before 01:30 after, even in the same zone.

## Edges of the calendar

Python dates run from year 1 to year 9999. In `stop` mode a range that would step past either
end simply stops. In `count` mode the values that fit are produced and then `OverflowError` is
raised, since the count cannot be met.

## Command line

```
$ stepdates 2026-01-31 --count 3 --step "1 month"
2026-01-31
2026-02-28
2026-03-31
$ stepdates 2026-01-31 --count 3 --step month --skip-invalid --format "%d %b %Y"
31 Jan 2026
31 Mar 2026
31 May 2026
```

`stepdates START [STOP] [--count N] [--step STEP] [--inclusive] [--skip-invalid]
[--end-of-month] [--format FMT]` prints one value per line (ISO 8601 unless `--format` gives a
`strftime` pattern). START and STOP are ISO 8601 dates or datetimes as Python's
`fromisoformat` reads them (compact forms such as `20260131` need Python 3.11 or later). A step
that starts with a dash works as is: `--step -P1M`. Bad input, including a bad `--format`,
exits with status 2; a count that runs past year 9999 exits with status 1 after the values that
fit. A reader that stops early (`| head`) ends the output quietly. `python -m stepdates` does
the same.

## Why

The standard library has no date range. `range()` only counts integers, and `timedelta`
cannot express calendar months or years, where "one month later" has to decide what happens to
31 January. People reach for `pandas.date_range` (a large dependency), hand-roll month
arithmetic (often with the clamping wrong, or drifting from 31 to 28 for good), or use
`dateutil.rrule` (a full recurrence engine whose API is built for rules rather than a plain
range). `stepdates` is a small, typed, zero-dependency function that does the obvious thing,
names its month-end convention, and agrees with `dateutil` where their conventions meet (the
test suite checks it).

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
