"""The ISO 8601 duration grammar, compiled from the ABNF of the fetched RFC texts.

The rules are read from RFC 3339 Appendix A (https://www.rfc-editor.org/rfc/rfc3339.txt) and
the sign from RFC 5545 3.3.6 (https://www.rfc-editor.org/rfc/rfc5545.txt), both fetched by
``scripts/fetch_vectors.py`` and checked against the sha256 in the manifest (last fetched
2026-10-23). A small ABNF translator turns them into a regular expression, so the expected
answer comes from the RFC text and not from the library. The library reads the date part
only: ``dur-time`` is replaced by a rule that matches nothing.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

import pytest

from stepdates._step import Step, parse_step

VECTORS = Path(__file__).resolve().parent / "vectors" / "rfc"
TOKEN = re.compile(r'\s*(1\*DIGIT|"[^"]*"|[A-Za-z][A-Za-z0-9-]*|[\[\]()/])')


def _text(name: str) -> str:
    path = VECTORS / name
    if not path.is_file():
        pytest.skip("RFC texts not fetched; run python scripts/fetch_vectors.py")
    return path.read_text(encoding="utf-8")


def _rules(text: str, names: str) -> dict[str, str]:
    found = re.findall(rf"^\s+({names})\s+=\s+(.+?)\s*$", text, flags=re.MULTILINE)
    return dict(found)


def _translate(body: str, rules: dict[str, str]) -> str:
    tokens = TOKEN.findall(body)
    assert "".join(tokens) == re.sub(r"\s+", "", body), body  # nothing was left unread

    def sequence(stop: str) -> str:
        options, current = [], ""
        while tokens and tokens[0] != stop:
            token = tokens.pop(0)
            if token == "/":
                options.append(current)
                current = ""
            elif token in "([":
                inner = sequence(")" if token == "(" else "]")
                tokens.pop(0)
                current += f"(?:{inner})" + ("?" if token == "[" else "")
            elif token == "1*DIGIT":
                current += "[0-9]+"
            elif token.startswith('"'):
                current += re.escape(token[1:-1])
            else:
                current += f"(?:{_translate(rules[token], rules)})"
        return "|".join([*options, current])

    return sequence("")


@pytest.fixture(scope="module")
def grammar() -> re.Pattern[str]:
    rules = _rules(_text("rfc3339.txt"), r"dur-[a-z]+|duration")
    assert {"dur-day", "dur-week", "dur-month", "dur-year", "dur-date", "duration"} <= set(rules)
    rules["dur-time"] = '"T" "never"'  # the date part only (matches no generated string)
    sign = _rules(_text("rfc5545.txt"), "dur-value")["dur-value"]
    assert sign.startswith('(["+"] / "-") "P"')
    expression = _translate('(["+"] / "-") ' + rules["duration"], rules)
    return re.compile(expression, re.IGNORECASE)  # RFC 5234 2.3: quoted text ignores case


def _value(text: str) -> Step:
    numbers = dict((u, int(n)) for n, u in re.findall(r"([0-9]+)([WYMD])", text.upper()))
    sign = -1 if text.startswith("-") else 1
    months = 12 * numbers.get("Y", 0) + numbers.get("M", 0)
    return Step(sign * months, sign * (numbers.get("D", 0) + 7 * numbers.get("W", 0)))


def test_every_short_string_is_read_as_the_rfc_grammar_says(grammar: re.Pattern[str]) -> None:
    alphabet = "+-P10WYMDTHS"
    accepted = 0
    for length in range(1, 6):
        for chars in itertools.product(alphabet, repeat=length):
            text = "".join(chars)
            valid = grammar.fullmatch(text) is not None
            expected = _value(text) if valid else None
            if expected is None or expected == Step(0, 0) or (expected.months and expected.days):
                with pytest.raises(ValueError):
                    parse_step(text)
            else:
                assert parse_step(text) == expected, text
                assert parse_step(text.lower()) == expected, text
                accepted += 1
    assert accepted == 81  # every non-zero date-part duration of up to five characters


@pytest.mark.parametrize(
    ("text", "valid"),
    [("P1W", True), ("P1Y2M3D", True), ("P1D", True), ("-P2W", True), ("P1Y1D", False),
     ("P1W1D", False), ("P", False), ("PT1H", False), ("P1M1Y", False), ("1M", False)],
)  # fmt: skip
def test_the_translated_grammar_reads_known_shapes(
    grammar: re.Pattern[str], text: str, valid: bool
) -> None:
    assert (grammar.fullmatch(text) is not None) is valid
