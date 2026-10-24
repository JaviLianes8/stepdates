"""quote() and scrub() on hostile input: odd str subclasses and runs of quote characters."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import date

import pytest

from stepdates import date_range, shift
from stepdates._quote import quote, scrub


class Masked(str):
    """A wrapper whose slices stay wrapped and whose repr never gets shorter."""

    def __getitem__(self, key: object) -> Masked:
        return Masked(str.__getitem__(self, key))  # type: ignore[index]

    def __repr__(self) -> str:
        return "<Masked value hidden: " + "*" * 70 + ">"

    def __len__(self) -> int:
        return 3


@pytest.mark.timeout(30)
def test_quote_reads_a_str_subclass_as_its_plain_text() -> None:
    assert quote(Masked("sk-live-0123")) == repr("sk-live-0123")
    assert quote(Masked("x" * 100)) == repr("x" * 80) + "... (100 characters)"


@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    "call",
    [
        lambda: date_range(date(2026, 1, 1), count=1, step=Masked("nope")),
        lambda: date_range(date(2026, 1, 1), count=1, invalid=Masked("nope")),  # type: ignore[arg-type]
        lambda: shift(date(2026, 1, 1), step=Masked("nope")),
    ],
    ids=["date_range step", "date_range invalid", "shift step"],
)
def test_a_str_subclass_is_refused_at_once(call: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match="'nope'"):
        call()


class Shown(str):
    """A subclass whose own text is something the caller never passed."""

    def __str__(self) -> str:
        return "z" * 1_000_000


class Broken(str):
    """A subclass that cannot be turned into text its own way."""

    def __str__(self) -> str:
        raise RuntimeError("no text")


@pytest.mark.timeout(30)
@pytest.mark.parametrize("kind", [Shown, Broken], ids=["other text", "raises"])
def test_quote_ignores_the_str_of_a_subclass(kind: type[str]) -> None:
    assert quote(kind("nope")) == "'nope'"


@pytest.mark.timeout(30)
@pytest.mark.parametrize("kind", [Shown, Broken], ids=["other text", "raises"])
@pytest.mark.parametrize(
    "call",
    [
        lambda v: date_range(date(2026, 1, 1), count=1, step=v),
        lambda v: date_range(date(2026, 1, 1), count=1, invalid=v),
        lambda v: shift(date(2026, 1, 1), step=v),
    ],
    ids=["date_range step", "date_range invalid", "shift step"],
)
def test_errors_quote_a_subclass_as_its_plain_text(
    call: Callable[[str], object], kind: type[str]
) -> None:
    with pytest.raises(ValueError, match="'nope'") as caught:
        call(kind("nope"))
    assert "zzz" not in str(caught.value)


SHAPES: dict[str, Callable[[int], str]] = {
    "escaped double quotes": lambda n: '"' + '\\"' * n,
    "escaped single quotes": lambda n: "'\\" * n,
    "alternating quotes": lambda n: "'\"" * n,
    "unclosed openings": lambda n: "'x" * n,
    "backslash runs": lambda n: "'" + "\\" * n,
}


def _seconds(text: str) -> float:
    best = float("inf")
    for _ in range(3):  # the best of three ignores a scheduler hiccup
        began = time.perf_counter()
        scrub(text)
        best = min(best, time.perf_counter() - began)
    return best


@pytest.mark.parametrize("shape", list(SHAPES))
def test_scrub_is_linear_on_runs_of_quotes(shape: str) -> None:
    small, large = _seconds(SHAPES[shape](5_000)), _seconds(SHAPES[shape](20_000))
    # Four times the input may take at most about four times as long (plus a floor for noise).
    assert large < 10 * small + 0.05, (shape, small, large)


def test_scrub_leaves_an_unclosed_quote_as_it_is() -> None:
    assert scrub("ambiguous option: --s=it's could match --step") == (
        "ambiguous option: --s=it's could match --step"
    )
    assert scrub("x '" + "y" * 100) == "x '" + "y" * 100
