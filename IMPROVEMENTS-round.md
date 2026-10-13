# stepdates improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Step grammar: units, quarter, ISO 8601 durations, `timedelta`
- [x] `invalid="skip"` (RFC 5545 recurrence reading) next to the default clamp
- [x] `end_of_month` anchoring and `shift`
- [x] `datetime` support: type kept, wall clock time, DST gaps and overlaps
- [x] Strict validation and clean ends at the edges of the supported years
- [x] Command line tool (`stepdates`, `python -m stepdates`)
- [x] Contracts: RFC examples, dateutil oracle, typing, README, wheel e2e
- [x] Mutation run (guards removed one at a time, each must fail the suite)
- [x] Docs: README, CHANGELOG, docstrings, packaging metadata
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [x] Independent review findings fixed with regression tests
- [x] Pull request opened, guard clean

## Starting point

`0.1.0` (not on PyPI) ships one function, `date_range(start, stop=None, *, step, count,
inclusive)`, with day, week, month and year steps, month-end clamping anchored on `start`, and
negative steps. Read as a user who builds billing schedules, report periods or calendar views:

- Only one month-end convention. Calendars (RFC 5545) drop a 31st that does not exist; billing
  wants "the last day of every month"; the library only clamps.
- `datetime` input breaks: a day step keeps the time, a month step silently returns a `date`,
  and a `date` stop against a `datetime` start fails deep inside a comparison.
- Nothing is said about time zones. Daily steps on aware datetimes cross DST changes, and wall
  times that fall in a gap or an overlap have no stated meaning.
- Ranges near year 9999 or year 1 crash with the raw `OverflowError` or `ValueError` of
  `date`, even in `stop` mode where the range simply ends.
- Steps are free text only: no quarter, no ISO 8601 duration (`P1M`), no `timedelta`.
- `count=3, inclusive=True` is accepted and ignored; `count=True` is a count of one.
- No command line tool, README examples not executed, no wheel test, no oracle in the tests.

## Sources (fetched 2026-10-13)

- RFC 5545, https://www.rfc-editor.org/rfc/rfc5545.txt (sha256 c256f809...):
  - 3.3.5: a local time in an overlap means its first occurrence; a local time in a gap is read
    with the UTC offset before the gap (New York 2007-03-11 02:30 is 03:30 EDT).
  - 3.3.10: instances with an invalid date (February 30) or a nonexistent local time are
    ignored and not counted; `DTSTART` is the first occurrence; `UNTIL` is inclusive and has
    the same value type as `DTSTART`; `UNTIL` and `COUNT` never appear together.
  - 3.8.5.3 examples used as golden sequences (daily for 10, every 10 days for 5, weekly for
    10, monthly on day 15 and 30 skipping February 30).
- RFC 3339 Appendix A, https://www.rfc-editor.org/rfc/rfc3339.txt (sha256 9ab2b886...): the
  ISO 8601 duration grammar (`P` with year, month, week and day parts; months only follow years
  and days only follow months; weeks stand alone). RFC 5545 3.3.6 adds the leading sign.
- python-dateutil 2.9 `rrule` and `relativedelta` as test-only oracles (not a runtime
  dependency): `rrule` skips invalid dates exactly as RFC 5545 says; `relativedelta(months=n)`
  clamps; `rrule(bymonthday=-1)` gives month ends.
- The two RFC texts are third-party and not committed: `scripts/fetch_vectors.py` fetches
  them into a gitignored folder checked against a tracked MANIFEST; the test that reads them
  skips when the folder is absent.

## Ranked improvements

1. **Two month-end conventions, named.** `invalid="clamp"` (default, unchanged) and
   `invalid="skip"`, the RFC 5545 reading: a 31st that does not exist is dropped and not
   counted, so `count` counts real values. Cross-checked against `rrule` for many seeds.
2. **`end_of_month=True`.** From a month end, every month or year step lands on the last day of
   its month (30 April, 31 May, 30 June). Rejected unless `start` is a month end and the step
   is month based. Cross-checked against `rrule(bymonthday=-1)`.
3. **`datetime` in, `datetime` out.** The type of `start` is kept, with its time and tzinfo.
   Steps are calendar steps on the wall clock, as in RFC 5545. Every later term has `fold=0`,
   which is the RFC 5545 3.3.5 reading of overlaps and gaps; with `invalid="skip"` a term in a
   gap is dropped instead (3.3.10). `stop` must match `start` (date with date, naive with
   naive, aware with aware) or `TypeError` is raised up front.
4. **Edges of the calendar.** In `stop` mode a range that would leave years 1 to 9999 ends
   cleanly; in `count` mode it raises `OverflowError` with a clear message once it gets there.
5. **Step grammar.** `"quarter"` units, ISO 8601 durations (`"P1M"`, `"-P2W"`, `"P1Y6M"`)
   following the RFC 3339 grammar with mixed month and day parts rejected (they have no single
   order of application), and `timedelta` steps of whole days.
6. **`shift(value, step)`.** One step from a date with the same clamping rules, the building
   block that people hand-roll wrong.
7. **Strict validation.** `TypeError` for non-date starts and wrong step or count types,
   `ValueError` for `inclusive` with `count`, unknown `invalid` policies and misplaced
   `end_of_month`, all before iteration starts.
8. **Command line tool.** `stepdates START [STOP] [--count N] [--step S] [--inclusive]
   [--skip-invalid] [--end-of-month] [--format FMT]`, one value per line for shell loops;
   exit 2 on bad input, quiet on a closed pipe.
9. **Contracts that bite.** RFC example sequences, a dateutil oracle, DST cases in
   America/New_York and Europe/Madrid, a mypy snippet over the typed API, executed README
   examples, an installed-wheel e2e and a mutation run.
10. **Docs and packaging.** README with runnable examples and the conventions spelled out,
    CHANGELOG 0.2.0, classifiers and keywords.

Left out on purpose: sub-day steps (hours are absolute time, not calendar steps, and mixing
both readings in one function invites DST bugs; `timedelta` arithmetic already covers them),
BYDAY, BYSETPOS and the rest of RRULE (that is a recurrence engine, which `dateutil.rrule`
already is), ISO week-numbering year stepping (ISO 8601 defines no clamping for week 53), and a
re-iterable range object with `len()` (an iterator keeps 0.x callers working; `list()` is one
call away).

## Verification

- Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src` (also `src tests`) and
  `pytest` exit 0 on Windows with Python 3.13 (1857 passed, 1 skipped: the wheel e2e). On a
  second machine with Python 3.14, a fresh clone, the RFC texts fetched by the script and
  `STEPDATES_E2E=1`, the whole suite passes with nothing skipped: it builds the wheel and the
  sdist, checks that no RFC text or tests ship in them, installs the wheel in a fresh venv,
  drives the API from an empty folder, and runs the installed `stepdates` script and
  `python -m stepdates`.
- Ground truth: the RFC 5545 example sequences (daily, every 10 days, weekly, daily until with
  the real UTC `UNTIL`, February 30 ignored) pass, and the cited lines and rules are checked
  against the fetched RFC texts. The RFC 3339 duration rules are read from the fetched text,
  and every ordering of the Y, M, W and D designators is checked against them.
- Oracle: python-dateutil 2.9 (tests only) agrees on 400 seeds each for `invalid="skip"` with
  a count (`rrule` COUNT) and with an inclusive stop (`rrule` UNTIL), for clamping in both
  directions (`relativedelta`) and for `end_of_month` (`rrule(bymonthday=-1)`), and on wall
  clock times for aware datetimes in New York, Madrid and Lord Howe (half-hour DST).
- Mutations: 67 mutants (step grammar and units, the ISO duration rules, ASCII digits, timedelta
  checks, month arithmetic, clamping, the year bounds, fold reset, gap detection, instant
  comparison, every argument check, skip and stop logic, `shift`, and every command line flag,
  parser, format check, exit code and pipe rule), applied one at a time with the bytecode cache
  disabled and purged before each run: all killed. Three first drafts were equivalent (a
  `<=` next to an equality branch, a `>=` on a day that cannot pass the month end, and an
  aware comparison that already ignores fold within one zone) and were replaced. The baseline
  was green before and after.
- Independent review: 13 findings. Fixed with regression tests: the duration grammar now
  rejects a day part straight after years (`P1Y1D`, `P0Y3D`); counts and durations take ASCII
  digits only; a reader that closes the pipe on Windows (EINVAL) ends quietly, checked with a
  real subprocess; a bad `--format` exits 2; dates are parsed before datetimes, so a compact
  date stays a date; `--step -P1M` works without an equals sign; the grammar test now drives
  the parser; the UNTIL example uses the RFC's UTC bound; the overlap test starts on a real
  fall-back day; `inclusive` and `end_of_month` must be booleans; an aware `stop` is compared
  as an instant. The Python floor stays 3.10, as on `main`.
