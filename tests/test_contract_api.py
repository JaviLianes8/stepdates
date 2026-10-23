"""The 1.0.0 promise: signatures, documented errors and documented examples stay as they are."""

from __future__ import annotations

import ast
import doctest
import inspect
import typing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

import stepdates
from stepdates import _range, date_range, shift

P = inspect.Parameter


def _shape(func: object) -> list[tuple[str, object, object]]:
    sig = inspect.signature(func)  # type: ignore[arg-type]
    return [(p.name, p.kind, p.default) for p in sig.parameters.values()]


def test_date_range_signature_is_pinned() -> None:
    assert _shape(date_range) == [
        ("start", P.POSITIONAL_OR_KEYWORD, P.empty),
        ("stop", P.POSITIONAL_OR_KEYWORD, None),
        ("step", P.KEYWORD_ONLY, "day"),
        ("count", P.KEYWORD_ONLY, None),
        ("inclusive", P.KEYWORD_ONLY, False),
        ("invalid", P.KEYWORD_ONLY, "clamp"),
        ("end_of_month", P.KEYWORD_ONLY, False),
    ]


def test_shift_signature_is_pinned() -> None:
    assert _shape(shift) == [
        ("value", P.POSITIONAL_OR_KEYWORD, P.empty),
        ("step", P.POSITIONAL_OR_KEYWORD, P.empty),
        ("end_of_month", P.KEYWORD_ONLY, False),
    ]


def test_invalid_policy_is_the_literal_of_the_two_conventions() -> None:
    assert typing.get_origin(stepdates.InvalidPolicy) is typing.Literal
    assert typing.get_args(stepdates.InvalidPolicy) == ("clamp", "skip")


@pytest.mark.parametrize("name", ["date_range", "shift"])
def test_every_public_function_documents_errors_and_an_example(name: str) -> None:
    doc = inspect.getdoc(getattr(stepdates, name)) or ""
    assert ">>> " in doc
    for error in ("TypeError", "ValueError", "OverflowError"):
        assert f"{error}:" in doc, error


def test_the_package_docstring_documents_the_policy_alias() -> None:
    assert "InvalidPolicy" in (stepdates.__doc__ or "")
    assert ">>> " in (stepdates.__doc__ or "")


def test_the_policy_alias_has_an_attribute_docstring_with_a_running_example() -> None:
    # typing caches Literal["clamp", "skip"], so __doc__ cannot be set on the alias without
    # changing every identical literal in the process; the docstring sits under the assignment.
    tree = ast.parse(Path(_range.__file__).read_text(encoding="utf-8"))
    body = tree.body
    (index,) = [
        i
        for i, node in enumerate(body)
        if isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) == "InvalidPolicy"
    ]
    after = body[index + 1]
    assert isinstance(after, ast.Expr) and isinstance(after.value, ast.Constant)
    doc = after.value.value
    assert isinstance(doc, str)
    test = doctest.DocTestParser().get_doctest(doc, dict(vars(_range)), "InvalidPolicy", None, 0)
    runner = doctest.DocTestRunner()
    runner.run(test)
    assert runner.summarize(verbose=False) == (0, len(test.examples))
    assert len(test.examples) >= 2


D = date(2026, 1, 31)

# (arguments, error type, words that must appear in the message)
DATE_RANGE_ERRORS: list[tuple[dict[str, object], type[Exception], str]] = [
    ({"start": "2026-01-01", "count": 1}, TypeError, "start must be a date"),
    ({"start": D, "stop": "2026-02-01"}, TypeError, "stop must be a date"),
    ({"start": D, "stop": datetime(2026, 2, 1)}, TypeError, "both be dates"),
    (
        {"start": datetime(2026, 1, 1), "stop": datetime(2026, 2, 1, tzinfo=timezone.utc)},
        TypeError,
        "naive or both be aware",
    ),
    ({"start": D, "count": 1, "step": 1}, TypeError, "str or a timedelta"),
    ({"start": D, "count": 1.0}, TypeError, "count must be an int"),
    ({"start": D, "count": True}, TypeError, "count must be an int"),
    ({"start": D, "count": 1, "invalid": 1}, TypeError, "invalid must be a str"),
    ({"start": D, "stop": D, "inclusive": 1}, TypeError, "inclusive must be a bool"),
    ({"start": D, "count": 1, "end_of_month": None}, TypeError, "end_of_month must be a bool"),
    ({"start": D}, ValueError, "exactly one of stop or count"),
    ({"start": D, "stop": D, "count": 1}, ValueError, "exactly one of stop or count"),
    ({"start": D, "count": -1}, ValueError, "must not be negative"),
    ({"start": D, "count": 1, "inclusive": True}, ValueError, "inclusive only applies"),
    ({"start": D, "count": 0, "inclusive": True}, ValueError, "inclusive only applies"),
    ({"start": D, "count": 1, "step": "fortnight"}, ValueError, "invalid step"),
    ({"start": D, "count": 1, "step": "0 days"}, ValueError, "must not be zero"),
    ({"start": D, "count": 1, "step": timedelta(hours=1)}, ValueError, "whole days"),
    ({"start": D, "count": 1, "step": "P1M1D"}, ValueError, "mixes months"),
    ({"start": D, "count": 1, "invalid": "roll"}, ValueError, "invalid must be one of"),
    ({"start": D, "count": 1, "end_of_month": True}, ValueError, "month, quarter or year"),
    (
        {"start": date(2026, 1, 30), "count": 1, "step": "month", "end_of_month": True},
        ValueError,
        "last day of its month",
    ),
]


@pytest.mark.parametrize(("kwargs", "error", "words"), DATE_RANGE_ERRORS)
def test_date_range_raises_the_documented_error_at_call_time(
    kwargs: dict[str, object], error: type[Exception], words: str
) -> None:
    with pytest.raises(error, match=words) as caught:
        typing.cast(typing.Any, date_range)(**kwargs)
    assert type(caught.value) is error  # not a subclass that a caller would not expect


def test_count_overflow_is_raised_lazily_after_the_values_that_fit() -> None:
    values = date_range(date(9999, 11, 30), count=3, step="month")
    assert next(values) == date(9999, 11, 30)
    assert next(values) == date(9999, 12, 30)
    with pytest.raises(OverflowError, match="after 2 values"):
        next(values)


@pytest.mark.parametrize(
    ("args", "kwargs", "error"),
    [
        (("2026-01-31", "month"), {}, TypeError),
        ((D, 1), {}, TypeError),
        ((D, "month"), {"end_of_month": "yes"}, TypeError),
        ((D, "fortnight"), {}, ValueError),
        ((D, "-0 months"), {}, ValueError),
        ((D, "day"), {"end_of_month": True}, ValueError),
        ((date(9999, 12, 31), "day"), {}, OverflowError),
        ((date(1, 1, 1), "-P1M"), {}, OverflowError),
    ],
)
def test_shift_raises_the_documented_error(
    args: tuple[object, ...], kwargs: dict[str, object], error: type[Exception]
) -> None:
    with pytest.raises(error) as caught:
        typing.cast(typing.Any, shift)(*args, **kwargs)
    assert type(caught.value) is error


def test_results_are_plain_values_of_the_start_type() -> None:
    assert type(shift(D, "day")) is date
    aware = datetime(2026, 1, 31, 9, tzinfo=timezone.utc)
    assert [type(v) for v in date_range(aware, count=2, step="month")] == [datetime, datetime]
