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
list(date_range(date(2026, 1, 1), date(2026, 1, 4)))
# [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]

# Step by week, with a count instead of a stop.
list(date_range(date(2026, 1, 1), count=3, step="week"))
# [date(2026, 1, 1), date(2026, 1, 8), date(2026, 1, 15)]

# A signed count in the step: every two days, backwards.
list(date_range(date(2026, 1, 5), date(2026, 1, 1), step="-2 days"))
# [date(2026, 1, 5), date(2026, 1, 3)]

# Include the endpoint when a term lands on it.
list(date_range(date(2026, 1, 1), date(2026, 1, 3), inclusive=True))
# [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]
```

Pass exactly one of `stop` or `count`. The range is half-open (`stop` excluded) unless
`inclusive=True`. The `step` is a unit (`"day"`, `"week"`, `"month"`, `"year"`), optionally
with a signed count such as `"2 weeks"` or `"-1 month"`; a negative step walks backwards.

### Month and year stepping

Month and year steps clamp to the last valid day, and every term is measured from `start`,
so the day of month never drifts:

```python
list(date_range(date(2026, 1, 31), count=4, step="month"))
# [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)]

list(date_range(date(2020, 2, 29), count=5, step="year"))
# [date(2020, 2, 29), date(2021, 2, 28), date(2022, 2, 28), date(2023, 2, 28), date(2024, 2, 29)]
```

The 31 January case clamps to 28 February but returns to 31 March, because each value is the
original day shifted by whole months rather than a walk over the previous clamped value. A leap
day clamps to 28 February in common years and returns on the next leap year.

## Why

The standard library has no date range. `range()` only counts integers, and `timedelta`
cannot express calendar months or years, where "one month later" has to clamp 31 January to
the end of February. People reach for `pandas.date_range` (a large dependency), hand-roll
month arithmetic (often with the clamping wrong), or use `dateutil.rrule` (heavy, and its API
is built for recurrence rules rather than a plain range). The dedicated packages are stale:
`daterange` has not been released since 2010, and `dateiter` is a days-only command line tool.
`stepdates` is a single, typed, zero-dependency function that does the obvious thing and gets
the month and year edges right.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
