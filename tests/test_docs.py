"""The README examples run and print what they say; metadata agrees with the code."""

from __future__ import annotations

import itertools
import re
import shlex
from pathlib import Path

import pytest

import stepdates
from stepdates._cli import main

ROOT = Path(__file__).resolve().parents[1]


def _readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def _blocks() -> list[str]:
    return re.findall(r"```python\n(.*?)```", _readme(), flags=re.DOTALL)


def test_the_readme_has_its_three_examples() -> None:
    assert len(_blocks()) == 3


@pytest.mark.parametrize("index", range(3))
def test_each_example_prints_what_its_comments_say(
    index: int, capsys: pytest.CaptureFixture[str]
) -> None:
    block = _blocks()[index]
    if "ZoneInfo" in block:
        zoneinfo = pytest.importorskip("zoneinfo")
        try:
            zoneinfo.ZoneInfo("America/New_York")
        except zoneinfo.ZoneInfoNotFoundError:  # pragma: no cover
            pytest.skip("no time zone database")
    exec(compile(block, "README.md", "exec"), {"__name__": "readme"})
    lines = block.splitlines()
    # A comment right under a line of code is the output of that code.
    results = [
        line[2:]
        for above, line in itertools.pairwise(lines)
        if line.startswith("# ") and above and not above.startswith("#")
    ]
    printed = capsys.readouterr().out.splitlines()
    assert printed == results
    assert len(printed) >= 2


def test_the_command_line_examples_match_the_tool(capsys: pytest.CaptureFixture[str]) -> None:
    session = re.search(r"```\n(\$ stepdates .*?)```", _readme(), flags=re.DOTALL)
    assert session is not None
    transcript: list[str] = []
    for line in session.group(1).splitlines():
        if line.startswith("$ stepdates "):
            assert main(shlex.split(line[len("$ stepdates ") :])) == 0
            transcript += [line, *capsys.readouterr().out.splitlines()]
    assert transcript == session.group(1).splitlines()
    assert len(transcript) == 8


def test_every_public_name_appears_in_the_readme() -> None:
    for name in stepdates.__all__:
        assert f"`{name}" in _readme(), name


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == stepdates.__version__


def test_changelog_has_an_entry_for_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{stepdates.__version__}]" in text


def _shipped() -> list[Path]:
    return [
        *ROOT.glob("*.md"),
        *ROOT.glob("*.toml"),
        *ROOT.glob("src/**/*.py"),
        *ROOT.glob("tests/*.py"),
        *ROOT.glob("scripts/*"),
        ROOT / "tests" / "vectors" / "rfc" / "MANIFEST.txt",
    ]


def test_no_em_dash_in_any_shipped_text() -> None:
    for path in _shipped():
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_every_source_file_stays_under_two_hundred_lines() -> None:
    for path in _shipped():
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 200, path


def test_sources_are_ascii() -> None:
    for path in [*ROOT.glob("src/**/*.py"), *ROOT.glob("tests/*.py"), *ROOT.glob("scripts/*")]:
        assert path.read_text(encoding="utf-8").isascii(), path
