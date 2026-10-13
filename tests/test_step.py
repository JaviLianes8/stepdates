"""The step grammar: unit words, ISO 8601 durations and timedeltas."""

from __future__ import annotations

from datetime import timedelta

import pytest

from stepdates._step import Step, parse_step


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("day", Step(0, 1)),
        ("days", Step(0, 1)),
        ("3 days", Step(0, 3)),
        ("+3 days", Step(0, 3)),
        (" -2 Weeks ", Step(0, -14)),
        ("week", Step(0, 7)),
        ("month", Step(1, 0)),
        ("-1 month", Step(-1, 0)),
        ("quarter", Step(3, 0)),
        ("2 quarters", Step(6, 0)),
        ("year", Step(12, 0)),
        ("10 YEARS", Step(120, 0)),
        ("7days", Step(0, 7)),
    ],
)
def test_unit_words(text: str, expected: Step) -> None:
    assert parse_step(text) == expected


# Shapes from the RFC 3339 Appendix A grammar (date part), signed as in RFC 5545 3.3.6:
# https://www.rfc-editor.org/rfc/rfc3339.txt and https://www.rfc-editor.org/rfc/rfc5545.txt
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("P1D", Step(0, 1)),
        ("P15D", Step(0, 15)),
        ("P2W", Step(0, 14)),
        ("-P2W", Step(0, -14)),
        ("+P1W", Step(0, 7)),
        ("P1M", Step(1, 0)),
        ("P18M", Step(18, 0)),
        ("P1Y", Step(12, 0)),
        ("P1Y6M", Step(18, 0)),
        ("-P1Y6M", Step(-18, 0)),
        ("p3m", Step(3, 0)),
        ("P0Y3D", Step(0, 3)),
    ],
)
def test_iso_8601_durations(text: str, expected: Step) -> None:
    assert parse_step(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "P", "PT1H", "P1DT1H", "P1W2D", "P1D1M", "P1M1Y", "1M", "P-1M", "P1.5M", "fortnight"],
)
def test_malformed_steps_are_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="invalid step"):
        parse_step(text)


@pytest.mark.parametrize("text", ["P1M2D", "P1Y1D", "-P1Y2M3D"])
def test_durations_mixing_months_and_days_are_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="no single order"):
        parse_step(text)


@pytest.mark.parametrize("text", ["0 days", "P0D", "P0Y0M", "-0 weeks"])
def test_zero_steps_are_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="zero"):
        parse_step(text)


def test_whole_day_timedeltas() -> None:
    assert parse_step(timedelta(days=3)) == Step(0, 3)
    assert parse_step(timedelta(weeks=-1)) == Step(0, -7)


@pytest.mark.parametrize("step", [timedelta(hours=36), timedelta(days=-1, seconds=1)])
def test_partial_day_timedeltas_are_rejected(step: timedelta) -> None:
    with pytest.raises(ValueError, match="whole days"):
        parse_step(step)


def test_zero_timedelta_is_rejected() -> None:
    with pytest.raises(ValueError, match="zero"):
        parse_step(timedelta(0))


@pytest.mark.parametrize("step", [1, None, b"day", 2.0])
def test_other_types_are_rejected(step: object) -> None:
    with pytest.raises(TypeError, match="step must be"):
        parse_step(step)  # type: ignore[arg-type]


def test_direction() -> None:
    assert Step(1, 0).forward and Step(0, 1).forward
    assert not Step(-1, 0).forward and not Step(0, -1).forward
