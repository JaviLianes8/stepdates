"""The public API is typed: mypy infers results and rejects bad calls."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

api = pytest.importorskip("mypy.api")

SRC = Path(__file__).resolve().parents[1] / "src"

SNIPPET = """
import datetime as dt
import stepdates as s
reveal_type(s.date_range(dt.date(2026, 1, 1), count=2))
reveal_type(s.date_range(dt.datetime(2026, 1, 1), dt.datetime(2026, 2, 1)))
reveal_type(s.shift(dt.date(2026, 1, 31), "month"))
reveal_type(s.shift(dt.datetime(2026, 1, 31), dt.timedelta(days=1)))
s.date_range("2026-01-01", count=2)
s.date_range(dt.date(2026, 1, 1), count=2, invalid="roll")
s.date_range(dt.date(2026, 1, 1), count=2, step=3)
s.date_range(dt.date(2026, 1, 1), 5)
s.shift(dt.date(2026, 1, 1))
p: s.InvalidPolicy = "skip"
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    out, err, _ = api.run(
        ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    )
    return str(out) + str(err)


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (4, r"typing\.Iterator\[datetime\.date\]"),
        (5, r"typing\.Iterator\[datetime\.datetime\]"),
        (6, r"datetime\.date"),
        (7, r"datetime\.datetime"),
    ],
)
def test_results_keep_the_type_of_start(mypy_output: str, line: int, expected: str) -> None:
    assert re.search(rf'snippet\.py:{line}: note: Revealed type is "{expected}"', mypy_output), (
        mypy_output
    )


@pytest.mark.parametrize(
    ("line", "code"),
    [(8, "type-var"), (9, "arg-type"), (10, "arg-type"), (11, "arg-type"), (12, "call-arg")],
)
def test_wrong_calls_are_rejected(mypy_output: str, line: int, code: str) -> None:
    assert re.search(rf"snippet\.py:{line}: error: .*\[{code}\]", mypy_output), mypy_output


def test_the_policy_alias_accepts_its_values(mypy_output: str) -> None:
    assert not re.search(r"snippet\.py:13: error", mypy_output), mypy_output
