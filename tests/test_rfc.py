"""Example sequences from RFC 5545 3.8.5.3, https://www.rfc-editor.org/rfc/rfc5545.txt

The expected values are short sequences cited from the RFC as fetched on 2026-10-13. When the
RFC texts are present (``python scripts/fetch_vectors.py``), the citations themselves are
checked against them, so a sequence cannot drift from its source.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

import pytest

from stepdates import date_range

VECTORS = Path(__file__).resolve().parent / "vectors" / "rfc"

# (rule in the RFC, result line in the RFC, the same thing in this library's terms)
CITED = [
    ("RRULE:FREQ=DAILY;COUNT=10", "==> (1997 9:00 AM EDT) September 2-11"),
    ("RRULE:FREQ=DAILY;UNTIL=19971224T000000Z", "October 26-31;November 1-30;December 1-23"),
    ("RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5", "==> (1997 9:00 AM EDT) September 2,12,22;"),
    ("RRULE:FREQ=WEEKLY;COUNT=10", "==> (1997 9:00 AM EDT) September 2,9,16,23,30;October 7,14,21"),
    ("RRULE:FREQ=MONTHLY;BYMONTHDAY=15,30;COUNT=5", "(2007 EST) February 15"),
]


def test_daily_for_ten_occurrences() -> None:
    start = datetime(1997, 9, 2, 9)
    assert [value.day for value in date_range(start, count=10)] == list(range(2, 12))


def test_every_ten_days_five_occurrences() -> None:
    result = list(date_range(date(1997, 9, 2), count=5, step="10 days"))
    assert [(value.month, value.day) for value in result] == [
        (9, 2), (9, 12), (9, 22), (10, 2), (10, 12)
    ]  # fmt: skip


def test_weekly_for_ten_occurrences() -> None:
    result = list(date_range(date(1997, 9, 2), count=10, step="week"))
    assert [(value.month, value.day) for value in result] == [
        (9, 2), (9, 9), (9, 16), (9, 23), (9, 30), (10, 7), (10, 14), (10, 21), (10, 28), (11, 4)
    ]  # fmt: skip


def test_daily_until_is_inclusive() -> None:
    # "Daily until December 24, 1997" with UNTIL=19971224T000000Z, 9:00 AM local starts:
    # the last instance is December 23.
    result = list(date_range(datetime(1997, 9, 2, 9), datetime(1997, 12, 23, 9), inclusive=True))
    assert (result[0].day, result[-1].month, result[-1].day, len(result)) == (2, 12, 23, 113)


def test_february_30_is_ignored_and_not_counted() -> None:
    # The RFC rule picks days 15 and 30 (January 30, February 15, March 30 among its five);
    # the 30th alone is the month step from January 30. April 30 is derived, not cited.
    result = list(date_range(date(2007, 1, 30), count=3, step="month", invalid="skip"))
    assert result == [date(2007, 1, 30), date(2007, 3, 30), date(2007, 4, 30)]


def _rfc(name: str) -> str:
    path = VECTORS / name
    if not path.is_file():
        pytest.skip("RFC texts not fetched; run python scripts/fetch_vectors.py")
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize(("rule", "result"), CITED)
def test_citations_appear_in_rfc_5545(rule: str, result: str) -> None:
    text = _rfc("rfc5545.txt")
    assert rule in text
    assert result in text


def test_rfc_5545_rules_this_library_follows() -> None:
    text = " ".join(_rfc("rfc5545.txt").split())
    assert "Such recurrence instances MUST be ignored and MUST NOT be counted" in text
    assert "interpreted using the UTC offset before the gap in local times" in text
    assert "bounds the recurrence rule in an inclusive manner" in text
    assert 'The "DTSTART" property value always counts as the first occurrence' in text


def test_rfc_3339_duration_grammar_matches_the_parser() -> None:
    text = _rfc("rfc3339.txt")
    rules = dict(re.findall(r"^\s+(dur-[a-z]+)\s+=\s+(.+?)\s*$", text, flags=re.MULTILINE))
    assert rules["dur-week"] == '1*DIGIT "W"'
    assert rules["dur-month"] == '1*DIGIT "M" [dur-day]'
    assert rules["dur-year"] == '1*DIGIT "Y" [dur-month]'
    assert rules["dur-date"] == "(dur-day / dur-month / dur-year) [dur-time]"
