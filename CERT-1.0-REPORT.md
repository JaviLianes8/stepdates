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
- [x] Five QA lenses report PASS (item 19)
- [x] Independent reviewer reports PASS (item 16)
- [x] Final gates on a fresh clone of `release/1.0.0`
- [x] PR #3 and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Scorecard

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: 3 names kept, signatures pinned by `tests/test_contract_api.py`; behaviour changes in the CHANGELOG |
| 2 | `__all__` exact, no private imports in docs | PASS |
| 3 | Docstrings with runnable examples, doctests | PASS: doctests in 3 modules; README (3 blocks) and GUIDE (2 blocks) run as tests; `InvalidPolicy` carries an attribute docstring whose examples a contract test runs (reasoned exception for the alias: QA round 1, A8) |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed`, consumer typing checked by `tests/test_typing.py` |
| 5 | Typed, documented, bounded errors | PASS: `TypeError`, `ValueError`, `OverflowError`, each case documented in the docstrings and GUIDE; messages quote at most 80 characters with control characters escaped, the argument parser's own messages included (QA round 1) |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: RFC 5545 and RFC 3339 fetched live, python-dateutil 3.0.0, .NET 10.0.12 `DateTime` output |
| 8 | Real e2e from the wheel | PASS: wheel in a fresh venv, used from an empty folder with `-I`, CLI driven by subprocess; no PyPI release to upgrade from |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2, 3.14.2t; 3.13t not installed here; 3.9 refused by pip; suite run again on all six at b6c505c (QA round 1), 335f2a4 (QA round 2), 9416dfb (QA round 3), df4248d (QA round 4) and 4791a64 (QA round 5) |
| 11 | README and `twine check` | PASS: `twine check --strict`, absolute links, badge, GUIDE and CHANGELOG linked |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-23 |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | PASS: round 1 at 699fa55, every item pass (see Independent review) |
| 17 | PR and trace guard | PR #3 from `release/1.0.0`, trace guard CLEAN; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author 37 mutants, 36 killed, 1 equivalent; 4 later survivors closed by tests at c0c97d4; the 8 survivors of QA lens e and 10 mutants of the round 1 fixes all killed at b6c505c; round 2: 19 mutants, 18 killed, 1 equivalent; round 3: lens e's 5 survivors and 8 fix mutants killed (one on 3.10 and 3.11 only, by construction); round 4: lens e's survivor and 12 mutants of the argv rewriting killed on 3.13.2; round 5: lens e's 4 survivors killed on 3.11.5 and 3.13.2 |
| 19 | Five independent QA lenses | PASS: all five lenses report PASS (see QA verdicts); every finding of rounds 1 to 5 fixed and confirmed by its lens |

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

### Round 1 (reviewed at ea4eab6, fixed in 4c6e83b and b6c505c)

Lenses a (API and docs), c (adversarial), d (packaging and e2e) and e (contract strength)
reported findings; a defect reported by several lenses is listed once with every id. Each
behaviour fix was first written as a test that failed on ea4eab6 and passes now. No finding
is disputed.

| Finding | Resolution | Test |
| --- | --- | --- |
| a/A1: `shift` errors said `start` | `check_start` and `check_end_of_month` take the argument name; `shift` passes `value` | test_messages::test_shift_names_its_own_argument, test_date_range_names_start |
| a/A2: GUIDE said month ends always exist | GUIDE narrowed to dates and naive datetimes; an aware month end in a gap is dropped by `skip` | test_tzinfo::test_an_aware_month_end_inside_a_gap_is_dropped_by_skip |
| a/A3, d/F2: zone examples need tzdata on Windows | README and GUIDE say `pip install tzdata` next to the `zoneinfo` examples | test_docs::test_the_zone_examples_say_they_need_a_time_zone_database |
| a/A4, c/F2: argparse echoed whole arguments | `_Parser.error` passes the argparse message through `scrub()`: every argument (or value after `=`) over 80 characters becomes its `quote()`, and control characters are escaped | test_cli_output::test_argparse_errors_quote_at_most_a_short_prefix (unrecognized, unknown option, ambiguous option, explicit argument, secret-shaped), test_argparse_errors_escape_control_characters, test_short_unknown_arguments_are_named_as_given |
| a/A5, c/F1, d/F1: traceback and status 1 when stdout cannot encode the `--format` output | the `--format` check also encodes the sample with the encoding and error handler of stdout (status 2, `invalid --format`); a value that still fails in the output loop gives a one-line `stepdates: error:` and status 2; the same status on every interpreter | test_cli_output::test_a_format_the_output_cannot_encode_exits_two (CJK and a check mark on cp1252, a lone surrogate on UTF-8), test_a_value_the_output_cannot_encode_exits_two, test_a_cp1252_pipe_gets_no_traceback (subprocess) |
| a/A6: "after 1 values" | singular for one value | test_messages::test_the_overflow_message_counts_in_words |
| a/A7: GUIDE signature lacked `*` | `shift(value, step, *, end_of_month=False)` | docs |
| a/A8: `InvalidPolicy.__doc__` is None | `__doc__` is not assigned: typing caches `Literal["clamp", "skip"]`, so the text would leak to every identical literal in the process. Reasoned exception for the alias under item 3: an attribute docstring with a runnable example sits under the assignment in `_range.py` (read by Sphinx and editors), and the package docstring keeps its doctest | test_contract_api::test_the_policy_alias_has_an_attribute_docstring_with_a_running_example (runs its examples) |
| a/A9: CONTRIBUTING claimed no test touches disk or processes | reworded to the real layout: pure unit tests, subprocess CLI tests, the opt-in wheel test, and the .NET and RFC tests that skip without their tool or texts | docs |
| c/F3: `skip` with a tzinfo whose `dst()` is None or missing raised during iteration | `exists()` also catches `ValueError` and `NotImplementedError` from the default `fromutc()`: such a zone has no gap to find, so the term is kept | test_tzinfo::test_skip_with_a_zone_without_gaps_follows_the_naive_range, test_skip_with_a_zone_without_gaps_and_a_stop |
| e/F1-I04: `python -m` exit status untested | subprocess tests from the source tree and from the installed wheel assert status 1 | test_cli_output::test_python_dash_m_exits_one_after_the_values_that_fit_in_order, test_e2e_wheel |
| e/F2-X21: `skip` never run on an offsetless tzinfo | tests for day and month steps; after the c/F3 fix the mutant only differs where the value would be read as local time, so a test pins years 1, 1969 and 9999 | test_tzinfo::test_skip_with_a_zone_without_gaps_follows_the_naive_range, test_skip_never_reads_an_offsetless_value_as_local_time |
| e/F3-X47: naive start with an offsetless stop untested | both directions, plus an aware start with an offsetless stop | test_tzinfo::test_a_naive_start_takes_an_offsetless_stop_and_the_mirror |
| e/F4-R22: `inclusive` with `count=0` untested | added to the error contract | test_contract_api::test_date_range_raises_the_documented_error_at_call_time |
| e/F5-L13: order of values and overflow message untested | stderr merged into stdout, order asserted | test_cli_output::test_python_dash_m_exits_one_after_the_values_that_fit_in_order |
| e/F6-Q03: escaping untested | library messages (step, `invalid`) and the tool (START, STOP, `--count`, `--step`, argparse) | test_messages::test_messages_escape_control_characters, test_the_tool_escapes_control_characters |
| e/F7-S05: whitespace inside a step undocumented and untested | the GUIDE states that any ASCII whitespace or none separates count and unit; tests for both sides | test_step::test_any_ascii_whitespace_or_none_may_separate_a_count_and_its_unit, test_nothing_else_separates_a_count_and_its_unit |
| e/F8-X35-X36: `quote()` boundaries untested | boundaries at 78 to 81 characters and for escaped text. One behaviour change: a value of up to 80 characters is now quoted whole (before, 79 and 80 characters lost the closing quote and gained `...`) | test_messages::test_quote_bounds, test_a_step_message_quotes_eighty_characters_at_the_boundary |

The CHANGELOG 1.0.0 section records every behaviour change: the `quote()` boundary and
escaping, `value` in `shift` errors, the singular overflow message, status 2 for output the
encoding cannot hold, bounded argparse messages, and the `dst()` fix under Fixed.

One test scope changed: the 200-line rule in `test_docs` no longer binds this report and
`IMPROVEMENTS-round.md`. Both are records of the release work that grow with every round and
neither is in the sdist; the em-dash check still reads them.

Mutants of this round, each applied alone to a clone of b6c505c with the named test file run
with `-x`: the 8 survivors reported by lens e, then 10 written against the round 1 fixes. All
18 are killed.

| Mutant | Caught by |
| --- | --- |
| I04 `sys.exit(main())` to `main()` in `__main__` | test_cli_output::test_python_dash_m_exits_one_after_the_values_that_fit_in_order |
| X21 `exists` tests `tzinfo is None` | test_tzinfo::test_skip_never_reads_an_offsetless_value_as_local_time |
| X47 `check_stop` tests `tzinfo is not None` | test_tzinfo::test_a_naive_start_takes_an_offsetless_stop_and_the_mirror |
| R22 `inclusive` checked only for a non-zero count | test_contract_api::test_date_range_raises_the_documented_error_at_call_time |
| L13 no flush before the overflow message | test_cli_output::test_python_dash_m_exits_one_after_the_values_that_fit_in_order |
| Q03 `quote` without `repr` | test_messages::test_quote_bounds |
| S05 only a space between count and unit | test_step::test_any_ascii_whitespace_or_none_may_separate_a_count_and_its_unit |
| X35 `<=` to `<` on the length note | test_messages::test_quote_bounds |
| X36 `>` to `>=` on the escape cut | test_messages::test_quote_bounds |
| `scrub` keeps control characters | test_cli_output::test_argparse_errors_escape_control_characters |
| `scrub` quotes nothing | test_cli_output::test_argparse_errors_quote_at_most_a_short_prefix |
| `scrub` ignores the value after `=` | test_cli_output::test_argparse_errors_quote_at_most_a_short_prefix |
| no encoding check of `--format` | test_cli_output::test_a_format_the_output_cannot_encode_exits_two |
| no guard on the output loop | test_cli_output::test_a_value_the_output_cannot_encode_exits_two |
| `exists` catches only `OverflowError` | test_tzinfo::test_skip_with_a_zone_without_gaps_follows_the_naive_range |
| `shift` names `start` | test_messages::test_shift_names_its_own_argument |
| always "values" | test_messages::test_the_overflow_message_counts_in_words |
| parser errors not scrubbed | test_cli_output::test_argparse_errors_quote_at_most_a_short_prefix |

Interpreters at b6c505c, fresh venvs on this PC, the suite with the fetched RFC texts:
CPython 3.10.19, 3.11.5, 3.12.12, 3.14.2 and 3.14.2 free-threaded gave 2042 passed and 1
skipped each (the e2e test, which runs in the gates on 3.13.2).

Gates on this PC after the round (CPython 3.13.2, PowerShell 7 present, RFC texts fetched,
`STEPDATES_E2E=1`), each command on its own: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, `mypy --strict src tests` and `pytest` (2043 passed, none skipped) all
exit 0.

### Round 2 (reviewed at eeea114, fixed in 5bc799c and 335f2a4)

Every round 1 finding was confirmed fixed by its lens (a, c, d and e re-ran their repros at
eeea114). New findings came from lenses a, c, d and e; a defect reported by several lenses is
listed once with every id. Each behaviour fix was first written as a test that failed on
eeea114 and passes now. No finding is disputed.

| Finding | Resolution | Test |
| --- | --- | --- |
| a/N1, d/N1: the CHANGELOG said a value of up to 80 characters is quoted whole, but `quote()` cut the escaped text, so a short value with escapes lost its length and could end in half an escape | `quote()` keeps the longest prefix of the value whose `repr` has at most 80 characters between the quotes, so it never cuts inside an escape, and adds the length whenever the value is not shown whole. The CHANGELOG and GUIDE state that rule | test_messages::test_quote_bounds (reprs of 82 and 83 characters, `'a' + ESC * 30`, NUL * 21, zero-width spaces, tabs), test_quote_shows_the_longest_prefix_that_fits_whole (3,000 seeded values) |
| a/N2: GUIDE said nothing is dropped for any tzinfo whose `dst()` is None | narrowed to such a tzinfo that keeps the default `fromutc()`; one with its own `fromutc()` has its gaps dropped by `skip` | test_tzinfo::test_a_zone_without_dst_that_converts_from_utc_has_its_gap_dropped |
| c/N1: on 3.10 and 3.11 `-hTAIL` echoed TAIL whole ("ignored explicit argument") | `scrub()` no longer looks for the arguments in the message. argparse echoes a refused argument raw only in two messages: "unrecognized arguments", now listed by the tool itself, and "ambiguous option", whose option is quoted. Every other echo is a `repr`, and every `repr` in the message longer than 80 characters becomes the `quote()` of its value, whatever part of an argument it came from | test_cli_errors::test_a_dash_h_tail_is_quoted_as_older_pythons_report_it (the 3.10 message, any interpreter), test_a_dash_h_tail_is_never_echoed; on 3.10.19 and 3.11.5 the reviewer's repro now gives 333 bytes on stderr and the 1,000,000-character in-process case 333 characters |
| c/N2: `scrub()` was quadratic in the number of long arguments, and the message had no size bound | one pass over the message; unrecognized arguments are listed up to three, then "and N more"; `bound()` escapes control characters and cuts a message over 500 characters, with its length. 8,000 arguments of 81 characters now take 0.003 s (10.7 s before) for 524 characters of stderr | test_cli_errors::test_many_long_arguments_take_linear_time, test_many_long_arguments_give_a_short_message (unrecognized and ambiguous shapes), test_bound_cuts_whole_escapes_at_the_message_limit |
| e/N1-S08: the stdout error handler of the `--format` check untested | subprocess tests with `PYTHONIOENCODING=ascii:backslashreplace` and `ascii:replace` and a format with an accented letter (one that strftime takes on 3.10 and 3.11 under Windows too), exit 0 with the replaced text | test_cli_output::test_the_format_check_uses_the_error_handler_of_stdout |
| e/N2-S07: the `utf-8` fallback untested, and a closed stdout ended in a traceback | the fallback is reachable with a stdout that has no encoding (`io.StringIO`), now tested; a missing stdout (`>&-`) gives one line, "stepdates: error: there is no standard output to write to", and status 2 | test_cli_output::test_a_stdout_without_an_encoding_takes_utf_8, test_no_standard_output_is_a_one_line_error |
| e/N3-S15: the `quote()` boundary at a repr of 83 characters untested | covered by the new rule's tests: `'x' * 78 + TAB` is shown whole, `'x' * 79 + TAB` is cut to the 79 x's with its length | test_messages::test_quote_bounds |
| e/N4-S19-S20: the 80/81 boundary of `scrub()` untested | whole error lines for 80 characters (raw) and 81 (quoted), and for an ambiguous option of 80 (raw) and 104 (quoted) | test_cli_errors::test_the_whole_error_line |
| e/N5-S22-S24: the exact text of the scrubbed messages untested | whole error lines for `--inclusive=<100 y>`, `--bogus=<100 y>`, an ambiguous option, three and five unrecognized arguments, and an odd one | test_cli_errors::test_the_whole_error_line |
| e/N6-S27: escaping tested with ESC only | newline, carriage return, BEL, NEL (C1), U+2028 and a forged "stepdates: error:" line, in unrecognized, ambiguous and explicit-argument messages: the error stays on one printable line | test_cli_errors::test_no_argument_starts_a_new_line |

The CHANGELOG 1.0.0 section records the behaviour changes of this round: the `quote()` rule,
the listing of unrecognized arguments, the 500-character message bound and status 2 without
a standard output.

Mutants of this round, each applied alone to a copy of the fixed tree with the six CLI and
message test files run with `-x`: 19 written against the round 2 code, 18 killed. The one
survivor is equivalent: `quote()` starting from 81 characters instead of 80 changes nothing,
because 81 characters always give a `repr` of at least 83, so the loop cuts back to 80 first.
Two more candidates were not run because they are equivalent by construction: the early
return of short `repr` runs in `scrub()` (any threshold up to 82 gives the same text, since
`quote()` shows such a value whole), and `fail()` without `bound()` (the tool's own messages
are built from `quote()` and are short and printable already).

| Mutant | Caught by |
| --- | --- |
| `quote` cut at a repr of 83 (S15) | test_messages::test_quote_bounds |
| `quote` starts from 81 characters | equivalent (see above) |
| a short escaped value cut without its length | test_messages::test_quote_bounds |
| listing quotes 80 characters (S19) | test_cli_errors::test_the_whole_error_line[80 whole] |
| listing shows 81 characters raw (S20) | test_cli_errors::test_the_whole_error_line[81 quoted] |
| listing shows odd arguments raw | test_cli_errors::test_the_whole_error_line[odd] |
| four extras listed | test_cli_errors::test_the_whole_error_line[many] |
| "and 0 more" | test_cli_errors::test_the_whole_error_line[three] |
| message cut at 499 | test_cli_errors::test_bound_cuts_whole_escapes_at_the_message_limit |
| control characters kept (S27) | test_cli_errors::test_no_argument_starts_a_new_line |
| ambiguous option of 80 quoted | test_cli_errors::test_the_whole_error_line[ambiguous 80] |
| ambiguous option left raw | test_cli_errors::test_the_whole_error_line[ambiguous] |
| `repr` runs not bounded | test_cli_errors::test_the_whole_error_line[explicit argument] |
| `repr` runs quoted twice | test_cli_errors::test_the_whole_error_line[explicit argument] |
| argparse messages not scrubbed | test_cli_errors::test_the_whole_error_line[explicit argument] |
| no check for a missing stdout | test_cli_output::test_no_standard_output_is_a_one_line_error |
| `utf-8` fallback to `ascii` (S07) | test_cli_output::test_a_stdout_without_an_encoding_takes_utf_8 |
| stdout error handler ignored (S08) | test_cli_output::test_the_format_check_uses_the_error_handler_of_stdout |
| unrecognized arguments ignored | test_cli_errors::test_the_whole_error_line[80 whole] |

Lens c's seeded fuzz (`fuzz2.py`, seeds 11 and 22, 5,000 iterations each, CPython 3.13.2)
found no problem on the fixed tree.

Interpreters at 335f2a4: wheel and sdist built from a clean clone (`twine check --strict`
passes both), the wheel installed in a fresh venv per interpreter, the sdist's suite run
against it with the fetched RFC texts. CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and
3.14.2 free-threaded gave 2087 passed and 1 skipped each (the opt-in e2e test, which runs in
the gates), and the doctests pass on all six. The first run at 5bc799c failed 3 tests on 3.10
and 3.11 only: the new stdout encoding tests used a CJK format, which strftime refuses there
under Windows; 335f2a4 switched them to an accented letter.

Gates on this PC after the round (CPython 3.13.2, PowerShell 7 present, RFC texts fetched,
`STEPDATES_E2E=1`), each command on its own: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, `mypy --strict src tests` and `pytest` (2091 passed) all exit 0.

### Round 3 (reviewed at 9e69e30, fixed in 9416dfb)

Every round 2 finding was confirmed fixed by its lens (a, c, d and e re-ran their repros and
fuzz at 9e69e30). New findings came from lenses a, c, d and e; a defect reported by several
lenses is listed once with every id. Each behaviour fix was first written as a test that
failed on 9e69e30 (the parsing tests on 3.11.5, where the defect lives) and passes now. No
finding is disputed.

| Finding | Resolution | Test |
| --- | --- | --- |
| c/R3-1: `quote()` looped forever on a `str` subclass whose slices stay of the subclass and whose `repr` never gets shorter; `date_range(step=)`, `date_range(invalid=)` and `shift(step=)` reach it | `quote()` first takes the plain text of the value (`str.__str__`), so slicing, length and `repr` are those of `str`; the loop ends after at most 80 cuts. The three calls now raise `ValueError` at once | test_scrub::test_quote_reads_a_str_subclass_as_its_plain_text, test_a_str_subclass_is_refused_at_once (each under a 30 s timeout; both hung before) |
| c/R3-2: `scrub()` was quadratic on text full of quote characters that never close, against its docstring and the CHANGELOG | the closing quote of a `repr` run is optional in the pattern, so an opening that never closes is passed over in one scan to the end of its line and left as it is, instead of being scanned again from each later quote character. 20,000 escaped quotes now take 0.004 s (7.1 s before) | test_scrub::test_scrub_is_linear_on_runs_of_quotes (5 shapes, 5,000 against 20,000), test_scrub_leaves_an_unclosed_quote_as_it_is |
| d/N2 (and the note in e/RUN): an argparse message was bounded twice, so an ambiguous option made of wide escapes reported a length such as "(520 characters)" that matched nothing typed | `error()` hands the scrubbed message straight to argparse, so it is bounded once. An ambiguous option with a character that is not printable is now quoted like a long one, as unrecognized arguments already were, so the escaped text never outgrows the message | test_cli_error_edges::test_a_long_message_is_cut_once_and_names_its_own_length, test_the_error_line_at_the_edges[ambiguous wide escapes, ambiguous wider escapes, ambiguous tab] |
| a/F1, d/N3: with standard output closed, `--help` and `--version` printed to standard error and exited 0, against the documented status 2 | the check for a missing standard output runs before the arguments are read, so every run without one gives the one-line error and status 2. The CHANGELOG and GUIDE say so, `--help` and `--version` included | test_cli_parsing::test_without_a_stdout_every_run_is_a_one_line_error (`--help`, `--version`, `-h`, a run with `--help` last, an unknown option, no arguments) |
| a/F2: Python 3.10 and 3.11 refused a STOP that followed an option (`2026-01-01 --inclusive 2026-01-03`), 3.12 and later accepted it | the command line is read with `parse_known_intermixed_args`, so every supported Python reads options and START and STOP in any order. Recorded in the CHANGELOG, stated in the GUIDE | test_cli_parsing::test_stop_may_come_after_an_option (5 orders), test_extra_positionals_after_an_option_are_still_refused |
| e/E1-C8: nothing pinned that the single-quoted branch of the `repr` pattern excludes the backslash | exact error line for `--inclusive=` with a value over 80 characters holding both quote kinds (its `repr` escapes the single quote), and a 30 s bound on `--s='` followed by 75 backslashes. With the new pattern no input backtracks, so the mutant no longer hangs; it is killed by the exact line | test_cli_error_edges::test_the_error_line_at_the_edges[explicit with both quotes, ambiguous unclosed quote and backslashes] |
| e/E2-C7: the double-quoted branch untested | exact line for `--inclusive='` followed by 100 y | test_the_error_line_at_the_edges[explicit with a single quote] |
| e/E3-C4: the `rpartition` of the ambiguous message untested | exact line for an ambiguous option that itself contains " could match " | test_the_error_line_at_the_edges[ambiguous naming the tail] |
| e/E4-C3: the 81-character ambiguous option untested | exact line for an ambiguous option of 81 characters | test_the_error_line_at_the_edges[ambiguous 81] |
| e/E5-C5: the `repr` boundary of 83 characters in `scrub()` untested | exact lines for `--inclusive=` with 80 and with 81 y | test_the_error_line_at_the_edges[explicit 80, explicit 81] |

Lens a's second note (`bound()` cuts by the escaped length but reports the length of the
message) is left as it is: `quote()`, `listing()` and the ambiguous-option rule escape what
is not printable before `bound()` sees it, so the two lengths agree for every message the
suite and the lenses produced.

Mutants of this round, each applied alone to a copy of the fixed tree with the six CLI and
message test files run with `-x` and a 60 s timeout on CPython 3.13.2: the five survivors of
lens e and eight mutants of this round's fixes. Twelve are killed on 3.13.2. The thirteenth,
plain `parse_known_args` instead of the intermixed form, survives there by construction (3.12
and later already read STOP after an option) and is killed on 3.11.5 by
test_stop_may_come_after_an_option, which every interpreter run of the suite includes.

| Mutant | Caught by |
| --- | --- |
| single-quoted branch takes a backslash (E1-C8) | test_the_error_line_at_the_edges[explicit with both quotes] |
| no double-quoted branch (E2-C7) | test_the_error_line_at_the_edges[explicit with a single quote] |
| `partition` for `rpartition` (E3-C4) | test_the_error_line_at_the_edges[ambiguous naming the tail] |
| ambiguous option of 81 left raw (E4-C3) | test_the_error_line_at_the_edges[ambiguous 81] |
| `repr` run of 83 kept (E5-C5) | test_the_error_line_at_the_edges[explicit 81] |
| `quote()` keeps the subclass (R3-1) | test_scrub::test_quote_reads_a_str_subclass_as_its_plain_text (timeout) |
| ambiguous option that is not printable left raw (N2) | test_the_error_line_at_the_edges[ambiguous wide escapes] |
| unclosed `repr` run quoted | test_the_error_line_at_the_edges[ambiguous unclosed quote and backslashes] |
| closing single quote required again (R3-2) | test_scrub::test_scrub_is_linear_on_runs_of_quotes[escaped single quotes] |
| closing double quote required again (R3-2) | test_scrub::test_scrub_is_linear_on_runs_of_quotes[escaped double quotes] |
| argparse messages bounded twice (N2) | test_a_long_message_is_cut_once_and_names_its_own_length |
| no check for a missing stdout before parsing (F1, N3) | test_without_a_stdout_every_run_is_a_one_line_error[argv0] |
| `parse_known_args` instead of the intermixed form (F2) | test_stop_may_come_after_an_option[inclusive between] on 3.11.5; survives on 3.13.2 by construction |

The reviewers' repros, run again by subprocess on the wheels built at 9416dfb: `--version`
and `--help` with `>&-` exit 2 with the one-line error on 3.10.19, 3.11.5 and 3.14.2;
`2026-01-01 --inclusive 2026-01-03` and `2026-01-01 -s week 2026-01-20` print three dates
on all three; an ambiguous option of 76 U+200B or 76 U+E0001 gives one quoted line with
"(80 characters)"; the three `Masked` calls raise `ValueError` at once; `scrub()` on 20,000
escaped double quotes takes 0.004 s.

Interpreters at 9416dfb: wheel and sdist built from a clean clone (`twine check --strict`
passes both), the wheel installed in a fresh venv per interpreter, the sdist's suite run
against it with the fetched RFC texts. CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and
3.14.2 free-threaded gave 2121 passed and 1 skipped each (the opt-in e2e test, which runs in
the gates), exit 0, and the doctests pass on all six.

Gates on this PC after the round (CPython 3.13.2, RFC texts fetched, `STEPDATES_E2E=1`), each
command on its own: `ruff format --check .`, `ruff check .`, `mypy --strict src`,
`mypy --strict src tests` and `pytest` (2125 passed) all exit 0.

### Round 4 (reviewed at a77c968, fixed in 0d558a0, 3cc58b3 and df4248d)

Lens d confirmed the round 3 fixes N2 and N3 and that F1, F2 and N1 still hold, on seven
venvs; lens e confirmed E1 to E5 and killed 24 of its 25 new mutants. Two findings remained,
both fixed. Each behaviour fix was first written as a test that failed on a77c968 (on 3.11.5,
and on 3.13.2 for the parts that differed there too) and passes now. No finding is disputed.

| Finding | Resolution | Test |
| --- | --- | --- |
| d/N4: with an unknown option before STOP, Python 3.10 and 3.11 listed STOP among the unrecognized arguments (`2026-01-01 --inclsive 2026-01-03`), 3.12 and later only the option, against the CHANGELOG and GUIDE | the command line now reads the same on every supported Python, error messages included. When STOP is still empty after parsing, the first positional among the extras is taken as STOP and read like one (`argument stop: ...` when it is not a date), as 3.12 and later do; a parser with no options decides what is positional, so the answer follows that Python's own rules. Comparing every Python against 3.13.2 over all short command lines also showed that 3.10 and 3.11 read `--` otherwise (an option after it still counted; a dash-led argument after it was a missing START), dropped `--` given as an option value (`--step=--` failed with "not list", `--format=--` printed ISO dates), and that 3.14 reads an argument starting like a negative number (`-1x`, `-1_0`) as a value where 3.10 to 3.13 take it for an option. The argv is now rewritten before parsing (`_argv.py`): after the first `--` every argument is wrapped as a positional and the `--` becomes a mark that is dropped again, number-like arguments are wrapped (the 3.14 rule), and the value options use an action that puts a dropped `--` back. The wrapped text never reaches output. CHANGELOG and GUIDE updated | test_cli_parsing::test_unknown_options_and_double_dash_read_the_same_on_every_python (14 cases), test_option_values_read_the_same_on_every_python (9), test_a_rewritten_argument_never_shows_in_output, test_stop_may_come_after_an_option (2 new orders); test_argv (28 tests that pin each part on any Python) |
| e/S2: nothing pinned that `quote()` ignores a subclass's own `__str__`; the mutant `str(value)` survived | test subclasses whose `__str__` returns other text or raises: `quote()`, `date_range(step=)`, `date_range(invalid=)` and `shift(step=)` report `'nope'` with `ValueError` | test_scrub::test_quote_ignores_the_str_of_a_subclass, test_errors_quote_a_subclass_as_its_plain_text (6 cases) |

Differential check of the command line, run in process with `main()` on CPython 3.10.19,
3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded at df4248d: every command line of
up to 4 arguments over 12 tokens (22,621), of up to 3 over 20 tokens (8,421) and of up to 3
over 22 tokens aimed at option values (11,155), with exit status, standard output and the
last error line compared against 3.13.2: 0 differences, and no rewritten text in any output.
At a77c968, 3.11.5 differed from 3.13.2 on 1,842 command lines of the first set. Over the
third set, df4248d on 3.14.2 differs from a77c968 on 3.14.2 only where `-s` follows `--` (44
command lines): it is now START or STOP, as documented.

Mutants of this round, each applied alone with the argv and CLI test files run with `-x`, all
killed on CPython 3.13.2 (the first eleven also on 3.11.5):

| Mutant | Caught by |
| --- | --- |
| `quote()` reads `str(value)` (S2) | test_scrub::test_quote_ignores_the_str_of_a_subclass |
| no STOP taken from the extras | test_argv::test_late_stop_takes_the_first_positional |
| number rule of 3.10 to 3.13 | test_argv::test_prepare_wraps_what_starts_like_a_negative_number[-1x] |
| dropped `--` value not put back | test_argv::test_value_puts_back_a_dropped_double_dash |
| mark left among the extras | test_argv::test_settle_unwraps_values_and_drops_the_mark |
| wrapped option value not unwrapped | test_argv::test_settle_unwraps_values_and_drops_the_mark |
| arguments after `--` not wrapped | test_argv::test_prepare_wraps_everything_after_the_first_double_dash |
| `plain()` returns the wrapped text | test_argv::test_prepare_wraps_everything_after_the_first_double_dash |
| mark spelled `--` | test_argv::test_prepare_wraps_everything_after_the_first_double_dash |
| START and STOP read without unwrapping | test_cli_parsing::test_stop_may_come_after_an_option[options before double dash] |
| COUNT read without unwrapping | test_option_values_read_the_same_on_every_python[number-like count] |
| type error of a dropped `--` not turned into an argparse error | test_argv::test_value_reads_a_dropped_double_dash_with_its_type |
| bad late STOP raised instead of reported | test_argv::test_take_stop_reports_a_bad_stop_as_argparse_would |

Interpreters at df4248d: wheel and sdist built from a clean clone (`twine check --strict`
passes both), the wheel installed in a fresh venv per interpreter, the sdist's suite run
against it with the fetched RFC texts. CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and
3.14.2 free-threaded gave 2183 passed and 1 skipped each (the opt-in e2e test), exit 0, and
the doctests pass on all six.

Gates on this PC after the round (CPython 3.13.2, `STEPDATES_E2E=1`), each command on its
own: `ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests`
and `pytest` (2148 passed, 23 skipped: this interpreter has no time zone database and the
working tree no fetched RFC texts; the interpreter runs above have both) all exit 0.

### Round 5 (reviewed at 9c974b7, fixed in 4791a64)

Lens e confirmed S2 fixed and swept the argv rewriting with 38 probes: 31 killed (4 of them on
3.10 and 3.11 only, where the code they touch does the work), 3 equivalent (0 differences over
10,736 command lines on four Pythons) and 4 survivors that change behaviour. All four were
gaps in the tests, not wrong behaviour: the command line already did what the new tests pin,
so the CHANGELOG is unchanged. Each new test was checked by applying its mutant alone to a
copy of `src` and running the argv and CLI test files, on CPython 3.11.5 and 3.13.2. No
finding is disputed.

| Finding | Resolution | Killed by (3.11.5 and 3.13.2) |
| --- | --- | --- |
| e/S2 recheck: fixed | nothing to do | |
| e/N1: nothing pinned that a wrapped argument keeps its spaces; `self.original = original.strip()` survived | tests that `plain()` returns `" -1 "` and `""` as written and that `prepare()` keeps the spaces of every wrapped argument; command lines `-f "-1 "` (prints `-1 `), `-- 2026-01-01 " 2026-01-01" -n 2` (refused, quoting `' 2026-01-01'`), `-- 2026-01-01 "-1 "`, `2026-01-01 2026-01-03 "-1 "` and `-n "-1 "` with their exact output or error line | test_argv::test_plain_returns_the_text_as_written; test_cli_values::test_a_format_is_used_as_written[wrapped format] |
| e/N2: nothing kept an empty option value apart from a dropped `--`; `if not values:` survived | a direct test that `Value` stores `""` as `""` (with and without a type); command lines `--format=` and `-f ""` print ISO dates | test_argv::test_value_stores_an_empty_value_as_empty[None]; test_cli_values::test_a_format_is_used_as_written[empty] |
| e/N3: nothing pinned the error of an empty `--step`; `values or None` survived | command lines `--step=`, `-s ""` and `--step ""` give the exact `invalid step ''` line | test_argv::test_value_stores_an_empty_value_as_empty[None]; test_cli_values::test_an_empty_or_spaced_value_is_refused_as_written[empty step] |
| e/N4: nothing pinned an empty STOP after an unknown option on 3.10 and 3.11; `if stop:` survived | `take_stop()` with `["--bogus", ""]` and `["-x", ""]` reports the STOP error on any Python; the command lines `2026-01-01 --bogus ""` and `2026-01-01 -x ""` were added to the cross-version cases | test_argv::test_take_stop_reads_an_empty_stop[--bogus]; on 3.11.5 also test_cli_parsing::test_unknown_options_and_double_dash_read_the_same_on_every_python[empty stop] |

Interpreters at 4791a64: wheel and sdist built from a clean clone (`twine check --strict`
passes both), the wheel installed in a fresh venv per interpreter, the sdist's suite run
against it with the fetched RFC texts. CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and
3.14.2 free-threaded gave 2202 passed and 1 skipped each (the opt-in e2e test), exit 0, and
the 3 doctests pass on all six.

Gates on this PC after the round (CPython 3.13.2, `STEPDATES_E2E=1`), each command on its
own: `ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests`
and `pytest` (2167 passed, 23 skipped: this interpreter has no time zone database and the
working tree no fetched RFC texts) all exit 0.

### Round 6 (reviewed at 699fa55, nothing to fix)

Lens e confirmed the four round 5 survivors killed on CPython 3.10.19, 3.11.5, 3.12.12,
3.13.2 and 3.14.2 by the tests named in round 5, and checked the new command lines by hand on
3.10, 3.11 and 3.14 (same output on all three). It then swept `Escaped`, `Value.__call__`,
`plain()` and `take_stop()` with 10 new probes: 9 killed on all five interpreters, and one
equivalent: wrapping the stripped text while keeping the original value changes nothing,
because argparse reads the wrapped text only to classify the argument (it always starts with
the wrap mark, so it is always a positional), and every value and every output goes through
the original. 22,064 differential command lines gave 0 differences between the original and
that probe on each of the five interpreters, with no exception. Between 9c974b7 and 699fa55
only tests and this report changed; `src` is identical to 4791a64.

## QA verdicts (item 19)

Each lens ran on its own, from its own clone, and reported back only. Rounds count every
pass of that lens, re-verification included. The lens reports and their evidence (probe
scripts, logs, fetched sources) are kept with the maintainer, outside the repository, in the
local certification folder named below.

| Lens | Rounds | Final verdict | Report | Commit |
| --- | --- | --- | --- | --- |
| a. API and docs | 4 | PASS | `stepdates-cert/lens-a-r4` | a77c968 |
| b. Correctness and ground truth | 1 | PASS | `stepdates-cert/lens-b-r1` | ea4eab6 |
| c. Adversarial and robustness | 4 | PASS | `stepdates-cert/lens-c-r4` | a77c968 |
| d. Packaging and real e2e | 5 | PASS | `stepdates-cert/lens-d-r5/logs` | 9c974b7 |
| e. Contract strength | 6 | PASS | `stepdates-cert/lens-e-r6` | 699fa55 |

Lenses a and c gave their final PASS at a77c968; the later commits change only the command
line's argument reading (`_argv.py`, `_cli.py`) and tests, which lenses d and e and the
independent reviewer checked at 9c974b7 and 699fa55.

Lens b (CPython 3.13.2 and 3.11, at ea4eab6), independent of the library's own tests:

- Duration grammar: a matcher written by hand from the RFC 3339 Appendix A rules (text
  fetched from rfc-editor.org on 2026-10-23), with the RFC 5545 sign and RFC 5234 case
  rules and the documented refusals. Every string of up to 5 characters over
  `P0127YMWDTHS+-` (579,194) and of up to 7 over `P1YMWDT-` (2,396,744), each also in lower
  case and padded with ASCII blanks: 0 mismatches.
- java.time (OpenJDK 21.0.8) as oracle for clamp, skip, stop (inclusive and exclusive),
  `shift`, `end_of_month` and day, week and `timedelta` steps, years 1 to 3 and 9997 to 9999
  and overflow included: 55,760 comparisons, 0 mismatches. A copy with the skip rule broken
  gave 1,334 mismatches, so the check can fail.
- Aware datetimes against java.time in 20 zones (Lord Howe, Troll, Apia 2011, Kiritimati,
  Sao Paulo, Dublin, Casablanca, Sitka 1867 and others), years 1867 to 2023: wall clock, fold,
  the instant per RFC 5545 3.3.5, skip dropping exactly the gap terms (3.3.10) and a UTC stop
  at plus and minus one second. 867,260 terms (320 in gaps), 0 mismatches.
- python-dateutil 3.0.0 `rrule`: 19,987 DAILY, WEEKLY, MONTHLY and YEARLY rules with INTERVAL,
  COUNT and inclusive UNTIL against `invalid="skip"`: 0 mismatches.
- RFC 5545 3.8.5.3 examples, expected dates parsed from the fetched text: 8 of 8, the
  `BYMONTHDAY=15,30` invalid-date example included.
- 4,084 hand-written probes and 20 command lines by subprocess on both interpreters: 0
  failures. The README comparison rerun with pandas 3.1.0, python-dateutil 3.0.0, arrow 1.4.0
  and pendulum 3.3.0: every row confirmed.

## Final gates (fresh clone of `release/1.0.0` at 10617cf)

A fresh clone from GitHub on this PC, CPython 3.13.2, development requirements installed,
RFC texts fetched, `STEPDATES_E2E=1`, each command on its own: `ruff format --check .`,
`ruff check .`, `mypy --strict src`, `mypy --strict src tests` and `pytest` (2206 passed,
none skipped) all exit 0. `python -m build` built `stepdates-1.0.0.tar.gz` and
`stepdates-1.0.0-py3-none-any.whl`, and `twine check --strict` passes both. The wheel was
installed in a throwaway venv, the sdist's suite run against it with `src` removed and the RFC
texts present: 2192 passed and 3 skipped (the opt-in e2e test, and the two typing tests that
need mypy, which that venv does not hold), exit 0; the installed package's 3 doctest modules
pass; from an empty folder the `stepdates` script prints the documented month ends and
`python -I -m stepdates` gives the version and status 2 with a one-line error for a bad STOP.
The commit after 10617cf changes only this section.

## Disputed findings

None in rounds 1 to 6.

## Independent review (item 16)

A fresh reviewer audited 699fa55 against the 19 items, running each check: a clone at
699fa55, wheel and sdist built (hatchling 1.32.4), the README rendered, the wheel installed in
a fresh venv per interpreter with the sdist's suite and the doctests run against it, a seeded
command line fuzz, and six mutants of its own. Round 1 verdict: PASS, every item pass.

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS |
| 2 | `__all__` exact, no private imports in docs | PASS |
| 3 | Docstrings with runnable examples, doctests | PASS: 3 doctest modules pass on every interpreter below |
| 4 | Typed end to end | PASS |
| 5 | Typed, documented, bounded errors | PASS |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS |
| 8 | Real e2e from the wheel | PASS |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS: seeds 1 and 2, 6,000 command lines each, 0 problems on 3.10.19 and 3.14.2 |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.14.2 and 3.14.2 free-threaded, 2192 passed and 3 skipped each; 3.13.2 in the gates |
| 11 | README and `twine check` | PASS |
| 12 | Dated CHANGELOG section | PASS |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS |
| 16 | Independent reviewer | PASS: this review |
| 17 | PR and trace guard | PASS: PR #3 from `release/1.0.0`; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: the reviewer's 6 mutants (quote limit, month day, signed digit limit, late STOP, number rule, message limit) all killed |
| 19 | Five independent QA lenses | PASS |

One note, not a defect of the library: on CPython 3.10 the time argparse takes for 20,000
unknown options or repeated `-s` options grows faster than linearly, with plain
`parse_known_args` as much as with the intermixed form (11.7 s against 0.05 s on 3.13.2),
so it comes from that Python's argparse. Every other shape scales linearly on both.
