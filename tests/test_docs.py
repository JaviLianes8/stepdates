"""The README and GUIDE examples run and print what they say; metadata agrees with the code."""

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


def _blocks(name: str) -> list[str]:
    text = (ROOT / name).read_text(encoding="utf-8")
    return re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)


EXAMPLES = [("README.md", 3), ("GUIDE.md", 2)]


@pytest.mark.parametrize(("name", "expected"), EXAMPLES)
def test_the_documents_have_their_examples(name: str, expected: int) -> None:
    assert len(_blocks(name)) == expected


@pytest.mark.parametrize(
    ("name", "index"), [(name, index) for name, count in EXAMPLES for index in range(count)]
)
def test_each_example_prints_what_its_comments_say(
    name: str, index: int, capsys: pytest.CaptureFixture[str]
) -> None:
    block = _blocks(name)[index]
    if "ZoneInfo" in block:
        zoneinfo = pytest.importorskip("zoneinfo")
        try:
            zoneinfo.ZoneInfo("America/New_York")
        except zoneinfo.ZoneInfoNotFoundError:  # pragma: no cover
            pytest.skip("no time zone database")
    exec(compile(block, name, "exec"), {"__name__": "docs"})
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


@pytest.mark.parametrize("name", ["README.md", "GUIDE.md"])
def test_the_zone_examples_say_they_need_a_time_zone_database(name: str) -> None:
    (block,) = [block for block in _blocks(name) if "ZoneInfo" in block]
    text = (ROOT / name).read_text(encoding="utf-8")
    before = text[: text.index(block)]
    assert "pip install tzdata" in before[before.rindex("\n## ") :]


def test_readme_links_are_absolute_and_reach_the_guide_and_changelog() -> None:
    links = re.findall(r"\]\(([^)]+)\)", _readme())
    assert links and all(link.startswith("https://") for link in links), links
    base = "https://github.com/JaviLianes8/stepdates/blob/main/"
    for target in ("GUIDE.md", "CHANGELOG.md", "LICENSE"):
        assert base + target in links, target
        assert (ROOT / target).is_file()


def test_readme_carries_the_certified_badge() -> None:
    assert _readme().startswith(
        "# stepdates\n\n[![Lianes8 Certified]"
        "(https://lianes8studio.com/certified/lianes8-certified-badge.svg)]"
        "(https://lianes8studio.com/certified)\n"
    )


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


def test_every_public_name_appears_in_the_readme_and_guide() -> None:
    guide = (ROOT / "GUIDE.md").read_text(encoding="utf-8")
    for name in stepdates.__all__:
        assert f"`{name}" in _readme(), name
        assert f"`{name}" in guide, name


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
