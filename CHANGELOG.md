# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

### Added

- `invalid="skip"` drops a day the target month lacks (31 February) and does not count it,
  the RFC 5545 recurrence reading; `invalid="clamp"` stays the default.
- `end_of_month=True` keeps a month-end start on the last day of every month.
- `shift(value, step)` takes one calendar step with the same rules.
- `quarter` steps, ISO 8601 duration steps (`"P1M"`, `"-P2W"`, `"P1Y6M"`) and whole-day
  `timedelta` steps.
- `datetime` support: the type, time and `tzinfo` of `start` are kept, steps follow the wall
  clock, later terms take `fold=0`, and with `invalid="skip"` wall times inside a DST gap are
  dropped.
- `InvalidPolicy` type alias for the `invalid` argument.
- A `stepdates` command line tool, also run as `python -m stepdates`.

### Changed

- A month or year step on a `datetime` now returns a `datetime`, not a `date`.
- In `stop` mode a range that would leave years 1 to 9999 ends cleanly; in `count` mode it
  raises `OverflowError` with a clear message once the values that fit are produced.
- Wrong argument types raise `TypeError` up front: a non-date `start` or `stop`, a `date`
  mixed with a `datetime`, naive mixed with aware, a non-int (or bool) `count`, a step that is
  neither a string nor a `timedelta`.
- `inclusive=True` together with `count` raises `ValueError` instead of being ignored.

## [0.1.0]

- First release: `date_range` iterates dates by calendar day, week, month or year, with a
  `stop` or a `count`, an `inclusive` endpoint flag, signed step sizes for backward ranges,
  and end-of-month and leap-day clamping anchored on the start date.
