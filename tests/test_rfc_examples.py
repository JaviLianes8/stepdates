"""RFC 5545 3.8.5.3 examples, with the expected dates read out of the fetched RFC text.

Source: https://www.rfc-editor.org/rfc/rfc5545.txt, fetched by ``scripts/fetch_vectors.py``
(sha256 checked against the manifest; last fetched 2026-10-23). For every example whose rule
is a plain FREQ with INTERVAL, COUNT or UNTIL (the subset a range can express), the result
block printed under the rule is parsed here and compared with the library, so the expected
values come from the RFC and not from this file.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from stepdates import date_range

VECTORS = Path(__file__).resolve().parent / "vectors" / "rfc"
MONTHS = {name: number for number, name in enumerate(calendar.month_name) if name}
UNITS = {"DAILY": "day", "WEEKLY": "week", "MONTHLY": "month", "YEARLY": "year"}
PLAIN = re.compile(r"RRULE:FREQ=(DAILY|WEEKLY|MONTHLY|YEARLY)((?:;(?:INTERVAL|COUNT|UNTIL)=\w+)*)")


def _examples() -> list[tuple[str, datetime, str, list[date]]]:
    path = VECTORS / "rfc5545.txt"
    if not path.is_file():
        pytest.skip("RFC texts not fetched; run python scripts/fetch_vectors.py")
    text = path.read_text(encoding="utf-8")
    found = []
    pattern = r"DTSTART;TZID=America/New_York:(\d{8})T(\d{6})\n\s+(RRULE:\S+)\n\n\s+==> (.*?)\n\n"
    for day, time, rule, block in re.findall(pattern, text, flags=re.DOTALL):
        match = PLAIN.fullmatch(rule)
        if match is None or "..." in block:  # other parts, or an open-ended result
            continue
        start = datetime.strptime(day + time, "%Y%m%d%H%M%S")
        found.append((rule, start, block, _dates(block)))
    return found


def _dates(block: str) -> list[date]:
    """Read "(1997 9:00 AM EDT) September 2,9,16;October 7-9" style result lines."""
    result: list[date] = []
    year = 0
    for line in block.splitlines():
        heading = re.match(r"\s*\((\d{4}) [^)]*\)\s*(.*)", line)
        if heading:
            year, line = int(heading.group(1)), heading.group(2)
        for part in filter(None, (p.strip() for p in line.split(";"))):
            month, days = part.split(" ", 1)
            for item in days.split(","):
                first, _, last = item.strip().partition("-")
                for number in range(int(first), int(last or first) + 1):
                    result.append(date(year, MONTHS[month], number))
    return result


def test_the_plain_rules_of_the_rfc_are_all_found() -> None:
    rules = [rule for rule, *_ in _examples()]
    assert rules == [
        "RRULE:FREQ=DAILY;COUNT=10",
        "RRULE:FREQ=DAILY;UNTIL=19971224T000000Z",
        "RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5",
        "RRULE:FREQ=WEEKLY;COUNT=10",
        "RRULE:FREQ=WEEKLY;UNTIL=19971224T000000Z",
    ]


@pytest.mark.parametrize("index", range(5))
def test_the_library_produces_the_dates_printed_in_the_rfc(index: int) -> None:
    zoneinfo = pytest.importorskip("zoneinfo")
    try:
        new_york = zoneinfo.ZoneInfo("America/New_York")
    except zoneinfo.ZoneInfoNotFoundError:  # pragma: no cover
        pytest.skip("no time zone database")
    rule, start, _, expected = _examples()[index]
    parts = dict(p.split("=") for p in rule.removeprefix("RRULE:").split(";"))
    step = f"{parts.get('INTERVAL', '1')} {UNITS[parts['FREQ']]}"
    aware = start.replace(tzinfo=new_york)
    if "COUNT" in parts:
        values = list(date_range(aware, count=int(parts["COUNT"]), step=step))
    else:  # UNTIL is a UTC instant that bounds the rule inclusively
        until = datetime.strptime(parts["UNTIL"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        values = list(date_range(aware, until, step=step, inclusive=True))
    assert [value.date() for value in values] == expected
    assert {(value.hour, value.minute) for value in values} == {(start.hour, start.minute)}
