# stepdates 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to stepdates. Nothing is on PyPI yet
(`https://pypi.org/pypi/stepdates/json` answered 404 on 2026-10-23, and so did the
`step-dates`, `step_dates` and `stepdate` spellings), so 1.0.0 is the first release and there
is no upgrade path to check; every change against `main` (a3d2e3c, 0.2.0) is still listed in
the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (a3d2e3c, 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: specifications fetched live, reference implementations (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [x] Gates (item 15)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)
- [x] PR #3 and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Scorecard

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: 3 names kept, signatures pinned by `tests/test_contract_api.py`; behaviour changes in the CHANGELOG |
| 2 | `__all__` exact, no private imports in docs | PASS |
| 3 | Docstrings with runnable examples, doctests | PASS: doctests in 3 modules; README (3 blocks) and GUIDE (2 blocks) run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed`, consumer typing checked by `tests/test_typing.py` |
| 5 | Typed, documented, bounded errors | PASS: `TypeError`, `ValueError`, `OverflowError`, each case documented in the docstrings and GUIDE; messages quote at most 80 characters |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: RFC 5545 and RFC 3339 fetched live, python-dateutil 3.0.0, .NET 10.0.12 `DateTime` output |
| 8 | Real e2e from the wheel | PASS: wheel in a fresh venv, used from an empty folder with `-I`, CLI driven by subprocess; no PyPI release to upgrade from |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2, 3.14.2t; 3.13t not installed here; 3.9 refused by pip |
| 11 | README and `twine check` | PASS: `twine check --strict`, absolute links, badge, GUIDE and CHANGELOG linked |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-23 |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | pending |
| 17 | PR and trace guard | PR #3 from `release/1.0.0`, trace guard CLEAN; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author 37 mutants, 36 killed, 1 equivalent; 4 later survivors closed by tests at c0c97d4 |
| 19 | Five independent QA lenses | pending |

## Baseline on 0.2.0 (before any change)

Fresh clone at aca3500 (the 0.2.0 code) on another machine, CPython 3.14.2: `ruff format
--check .`, `ruff check .` and `mypy --strict src tests` exit 0; `pytest` 1857 passed, and
the installed-wheel test (`STEPDATES_E2E=1`) failed while building the sdist from a checkout
that held the run's `tmp` folder (the sdist took every file git did not ignore). The sdist
now uses an explicit file list, and the same setup passes. No doctests existed.

Defects found in 0.2.0 by reading and then reproducing:

- Reading a step was quadratic: blanks in front of a step that was not valid took 0.03 s
  for 1,000 spaces, 0.1 s for 2,000 and 0.6 s for 4,000.
- Error messages echoed the whole input (a 1 MB step gave a 1 MB message), in the library
  and the command line.
- A step size past 4,300 digits raised Python's own digit-limit `ValueError`.
- `" P1M"` (a non-ASCII space) was a valid duration while `" month"` was not.
- `invalid=1` raised `ValueError` while every other wrong type raised `TypeError`.
- No public docstring had an example or listed its errors; the README linked LICENSE
  relatively; there was no GUIDE.

## API review (item 1)

Kept: `date_range`, `shift` and `InvalidPolicy` with their 0.2.0 signatures, parameter
names, kinds and defaults, now pinned. `start` and `stop` stay positional-or-keyword, the
rest keyword-only. Errors stay the built-in types: a step, a policy or a flag that is wrong
is a `ValueError` or `TypeError` as Python callers expect, and a date leaving years 1 to 9999
is the `OverflowError` that `date` itself raises. Changed (all in the CHANGELOG): linear step
reading, ASCII-only whitespace, the 18-digit size limit, `TypeError` for a non-`str`
`invalid`, bounded messages, the `--count` digit limit. New private module `_quote.py`.

## Ground truth (item 7)

- RFC 5545 and RFC 3339, fetched on 2026-10-23 by `scripts/fetch_vectors.py` from
  rfc-editor.org into the ignored `tests/vectors/rfc` folder; size and sha256 checked against
  `tests/vectors/rfc/MANIFEST.txt`. `tests/test_rfc_examples.py` reads the result blocks of
  the five plain-FREQ examples of 3.8.5.3 out of the text and compares them with the library
  (New York, 09:00, COUNT and UNTIL); `tests/test_rfc_grammar.py` compiles the `dur-*` ABNF
  of RFC 3339 Appendix A (with the RFC 5545 sign) into a regular expression and checks every
  string of up to five characters over `+-P10WYMDTHS` (271,452 strings): the library accepts
  exactly the 81 non-zero date-part durations and reads their values.
- python-dateutil 3.0.0 (`tests/test_oracle.py`): `rrule` for the skip convention with
  COUNT and UNTIL, `relativedelta` for clamping both ways, `rrule(bymonthday=-1)` for
  `end_of_month`, wall-clock steps in three zones; 1,600 seeded cases plus 12 zone cases.
- .NET 10.0.12 `System.DateTime` (`tests/test_oracle_dotnet.py`): `scripts/dotnet_oracle.ps1`
  run with PowerShell 7 on this PC on 2026-10-23 wrote `tests/data/dotnet_calendar.csv`
  (3,000 seeded AddDays, AddMonths and AddYears results, 127 out of range). `shift` agrees on
  every row, anchored month ranges agree with one .NET jump in more than 1,000 cases, and
  the script is run again whenever PowerShell 7 is present.
- README comparison, run on 2026-10-23: pandas 3.1.0, python-dateutil 3.0.0, arrow 1.4.0 and
  pendulum 3.3.0 from 31 January 2026, monthly; their dependencies read from the installed
  metadata.

## Fuzz and hostile input (item 9)

`tests/test_fuzz.py`, three seeds each: 60,000 random step strings against a hand-written
reading of the grammar; 6,000 random clamped ranges over years 1 to 9999 (dates and naive
datetimes, both directions, sizes up to 1,000) against a hand-written calendar model,
including the lazy `OverflowError`; skip equals clamp minus the clamped terms; stop cuts
equal the model, exclusive and inclusive; `end_of_month` always lands on month ends.
`tests/test_fuzz_cli.py`: 4,500 random command lines end with status 0, 1 or 2 and no
traceback. `tests/test_hostile.py`: nine input shapes timed at 50,000 and 200,000
characters (linear), 100,000-character errors under 300 characters, 19 to 100,000 digits,
non-ASCII spaces and digits, the full 3,652,059-day and 119,988-month ranges, and huge
command line arguments.

## Author mutation round (item 18)

Each mutant applied alone to a fresh clone of a6f8d79 on another machine, full suite with
the fetched RFC texts, `-x`, 300 s per test. Killed by the first failing test shown.

| # | Mutation | Caught by |
| --- | --- | --- |
| 1 | digit limit 18 to 19 | test_hostile::test_more_than_eighteen_digits_is_a_clean_value_error |
| 2 | `forward` true for a backward day step | doctest of `date_range` |
| 3 | a week is 6 days | test_datetime::test_a_start_inside_a_gap_is_still_the_first_value |
| 4 | a quarter is 4 months | test_conventions::test_shift_clamps |
| 5 | duration sign dropped | doctest of `shift` |
| 6 | years directly followed by days accepted | test_rfc_grammar::test_every_short_string_is_read_as_the_rfc_grammar_says |
| 7 | a year is one month | doctest of `shift` |
| 8 | partial-day `timedelta` accepted | test_contract_api::test_date_range_raises_the_documented_error_at_call_time |
| 9 | non-ASCII text and spaces accepted | test_hostile::test_only_ascii_whitespace_surrounds_a_step |
| 10 | a duration week is one day | test_fuzz::test_random_steps_match_the_model |
| 11 | `end_of_month` ignored | doctest of `shift` |
| 12 | a last-day term counted as clamped | doctest of the package |
| 13 | month off by one | doctest of `date_range` |
| 14 | year 9999 refused | test_contract_api::test_count_overflow_is_raised_lazily_after_the_values_that_fit |
| 15 | `fold=1` kept on later terms | test_datetime::test_month_steps_reset_fold_too |
| 16 | DST gap times never skipped | test_datetime::test_skip_drops_a_gap_time_and_does_not_count_it |
| 17 | aware stop compared by wall time | test_datetime::test_an_aware_stop_is_compared_as_an_instant |
| 18 | `start` can be skipped | test_datetime::test_a_start_inside_a_gap_is_still_the_first_value |
| 19 | `inclusive` inverted | doctest of `date_range` |
| 20 | forward bound `>` to `>=` | equivalent: equality is decided on the line before |
| 21 | overflow handling swapped | test_cli::test_overflow_exits_one_after_the_values_that_fit |
| 22 | `count=-1` accepted | test_cli::test_bad_input_exits_two |
| 23 | `inclusive` with `count` accepted | test_cli::test_bad_input_exits_two |
| 24 | a `bool` count accepted | test_contract_api::test_date_range_raises_the_documented_error_at_call_time |
| 25 | `shift` takes two steps | doctest of `shift` |
| 26 | non-`str` policy gives `ValueError` | test_contract_api::test_date_range_raises_the_documented_error_at_call_time |
| 27 | `end_of_month` from a mid-month start | test_cli::test_bad_input_exits_two |
| 28 | naive mixed with aware | test_contract_api::test_date_range_raises_the_documented_error_at_call_time |
| 29 | messages quote 800 characters | test_hostile::test_errors_quote_at_most_a_short_prefix |
| 30 | `--skip-invalid` ignored | test_cli::test_skip_invalid |
| 31 | a closed pipe raises | test_cli::test_a_closed_pipe_stops_quietly |
| 32 | overflow exits 0 | test_cli::test_overflow_exits_one_after_the_values_that_fit |
| 33 | dash-led step value lost | test_cli::test_count_step_and_clamping |
| 34 | `--count` digit limit removed | test_hostile::test_the_tool_keeps_error_lines_short |
| 35 | backward stop compared forwards | doctest of `date_range` |
| 36 | a term equal to the stop not special-cased | doctest of `date_range` |
| 37 | 29 February treated as missing | doctest of `date_range` |

A second round of 64 mutants on aa13b7b, written independently, left four alive. Each was a real
gap in the tests, not an equivalent mutant; c0c97d4 adds the tests below, and each of the four
now fails the suite when applied alone:

| # | Mutation | Caught by |
| --- | --- | --- |
| 38 | the sign of a size counted as one of its 18 digits | test_hostile::test_a_sign_is_not_counted_as_a_digit |
| 39 | a wall time whose UTC instant leaves year 9999 treated as missing (dropped by `skip`) | test_datetime::test_an_aware_value_near_year_9999_is_not_dropped_by_skip |
| 40 | an aware stop whose UTC instant leaves years 1 to 9999 raises instead of comparing by wall time | test_datetime::test_an_aware_stop_near_year_9999_compares_by_wall_time |
| 41 | aware decided by `tzinfo is not None` instead of `utcoffset() is not None` | test_datetime::test_a_tzinfo_without_an_offset_is_naive |

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

- `tests/test_e2e_wheel.py` (`STEPDATES_E2E=1`) builds the wheel and sdist, checks that the
  wheel holds exactly the package modules, `py.typed` and the licence, that the sdist holds
  exactly the listed top-level files, `src`, `tests` (no fetched RFC text) and `scripts`, then
  installs the wheel in a fresh venv, uses it from an empty folder with `-I` and drives the
  `stepdates` script and `python -m stepdates` by subprocess (version, steps, a backward
  inclusive range, exit status 2). `twine check --strict` passes on both.
- Every interpreter on this PC from `requires-python` up, at c0c97d4: wheel installed in a
  fresh venv, the sdist's suite run against it with `src` removed and the RFC texts fetched,
  plus the installed package's doctests: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2
  and 3.14.2 free-threaded, 1980 passed and 1 skipped each (the e2e test, which runs in the
  gates), 3 doctest modules passed each; `twine check --strict` passed on both files.
  3.9.25 refuses the wheel (`>=3.10`). The same run at a6f8d79 gave 1975 passed each.

## Gates (item 15)

At a6f8d79 on another machine from a fresh clone, each command on its own, with the RFC
texts and `STEPDATES_E2E=1`: `ruff format --check .`, `ruff check .`, `mypy --strict src`,
`mypy --strict src tests` and `pytest` (1978 passed, 1 skipped: the .NET re-run, PowerShell 7
is not installed there; it passes on this PC) all exit 0.

At c0c97d4 on this PC (PowerShell 7 present), the same five commands with the RFC texts and
`STEPDATES_E2E=1` all exit 0; `pytest` collects 1984 tests and doctests.

## QA lenses (item 19)

Pending.

## Independent review (item 16)

Pending.
