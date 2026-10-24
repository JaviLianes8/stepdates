# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-23

The first release on PyPI (0.1.0 and 0.2.0 were never published). The public API
(`date_range`, `shift`, `InvalidPolicy`), the step grammar, the clamp, skip and end-of-month
conventions, the datetime rules, the error types and the command line are now stable: they
change only in a new major version. The GUIDE describes all of it.

### Changed

- A step is read in time linear in its length. Before, blanks in front of a step that was
  not valid made the check quadratic (4,000 spaces took about half a second).
- Only ASCII whitespace may surround a step. An ISO 8601 duration with a non-ASCII space
  around it (such as U+2003) was accepted and is now a `ValueError`, as unit words already
  were.
- A step size with more than 18 digits raises `ValueError` naming that limit. Before, a size
  past Python's 4,300-digit conversion limit raised that limit's own `ValueError`, and smaller
  ones could never give a second value anyway.
- An `invalid` argument that is not a `str` raises `TypeError` instead of `ValueError`.
- Error messages quote the value at fault as its `repr`, with at most 80 characters between
  the quotes and control characters escaped, in the library and in the command line. A value
  that does not fit (over 80 characters, or a shorter one whose escapes such as `\t` make its
  `repr` longer) is cut between two of its characters, never inside an escape, and followed
  by its length. A `str` subclass is quoted as its plain text. Before, the whole value was
  echoed. In the command line this covers the messages about unknown or malformed options
  too: an option over 80 characters, or with a character that is not printable, is quoted
  the same way, unrecognized arguments are listed up to three, followed by how many more
  there are, and a message over 500 characters is cut there once and followed by its
  length. Building a message takes time linear in its length, however many arguments there
  are.
- The errors of `shift` name its own argument, `value`; before they said `start`.
- The `OverflowError` of a `count` range says "after 1 value" when one value fits.
- The command line `--count` accepts at most 18 digits.
- The command line exits with status 2 and a one-line message when the output encoding cannot
  hold a value (a `--format` with characters the terminal or file encoding lacks). Before, it
  stopped with a traceback and status 1.
- The command line started without a standard output (closed with `>&-`) exits with status 2
  and a one-line message, whatever its arguments, `--help` and `--version` included. Before,
  it stopped with a traceback and status 1.
- The command line reads options and START and STOP in any order on every supported Python,
  with the same error messages. Before, Python 3.10 and 3.11 refused a STOP that came after an
  option (`stepdates 2026-01-01 --inclusive 2026-01-03`) as an unrecognized argument, while
  3.12 and later accepted it, and after an unknown option they listed STOP among the
  unrecognized arguments (`stepdates 2026-01-01 --inclsive 2026-01-03`).
- In the command line every argument after `--` is START or STOP, on every supported Python.
  Before, Python 3.10 and 3.11 still read an option there
  (`stepdates -- 2026-01-01 2026-01-03 --inclusive` printed three dates) and refused a
  dash-led argument there as a missing START.

### Fixed

- `invalid="skip"` with an aware datetime whose `tzinfo` returns `None` from `dst()`, or does
  not implement it, raised `ValueError` or `NotImplementedError` during iteration. Such a zone
  has no gap that can be found, so every term is kept, as with `invalid="clamp"`.

### Added

- Every public docstring lists the errors it raises and carries runnable examples, checked
  as doctests.
- GUIDE.md: the step grammar, the conventions, time zones, every error, the command line and
  the typing.

### Packaging

- `Development Status :: 5 - Production/Stable`, a `Source` project URL, and an sdist built
  from an explicit list of files.

## [0.2.0] - not published

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
- `inclusive` and `end_of_month` must be booleans (`TypeError` otherwise).
- An aware `stop` is compared as an instant, so repeated wall times are ordered correctly.
- Step counts and durations accept ASCII digits only, and an ISO 8601 duration must follow
  the RFC 3339 grammar (days follow months, never years directly).

## [0.1.0] - not published

- First release: `date_range` iterates dates by calendar day, week, month or year, with a
  `stop` or a `count`, an `inclusive` endpoint flag, signed step sizes for backward ranges,
  and end-of-month and leap-day clamping anchored on the start date.
