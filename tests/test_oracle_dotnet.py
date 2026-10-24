"""Cross-check against .NET System.DateTime, a calendar implementation independent of this one.

``tests/data/dotnet_calendar.csv`` is real program output: ``scripts/dotnet_oracle.ps1`` run
with PowerShell 7 on .NET 10.0.12 on 2026-10-23 (the first line of the file says so). Its
AddMonths and AddYears move a day a shorter month lacks to that month's last day, which is
the library's default ``invalid="clamp"`` convention. When PowerShell 7 is installed the
script is run again here and its output must match the committed file.
"""

from __future__ import annotations

import csv
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from stepdates import date_range, shift

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "data" / "dotnet_calendar.csv"


def _rows() -> list[dict[str, str]]:
    lines = DATA.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("# Produced by scripts/dotnet_oracle.ps1 with .NET ")
    return list(csv.DictReader(lines[1:]))


def test_the_fixture_covers_month_ends_both_directions_and_the_edges() -> None:
    rows = _rows()
    assert len(rows) == 3000
    months = [r for r in rows if r["unit"] != "days"]
    assert sum(r["start"].endswith(("-29", "-30", "-31")) for r in months) > 500
    assert any(int(r["amount"]) < 0 for r in months)
    assert sum(r["result"] == "out of range" for r in rows) > 50
    clamped = [
        r for r in months if r["result"] != "out of range" and r["start"][8:] != r["result"][8:]
    ]
    assert len(clamped) > 60
    assert any(r["start"].endswith("-02-29") and r["result"].endswith("-02-28") for r in clamped)


def test_shift_agrees_with_dotnet_on_every_row() -> None:
    for row in _rows():
        start, step = date.fromisoformat(row["start"]), f"{row['amount']} {row['unit']}"
        if row["result"] == "out of range":
            with pytest.raises(OverflowError):
                shift(start, step)
        else:
            assert shift(start, step) == date.fromisoformat(row["result"]), row


def test_anchored_month_ranges_agree_with_one_dotnet_jump() -> None:
    # .NET jumps n months at once; the range takes n / k steps of k months, each measured from
    # the start, so both must land on the same day however short the months in between.
    checked = 0
    for row in _rows():
        amount = int(row["amount"])
        if row["unit"] != "months" or row["result"] == "out of range" or abs(amount) < 2:
            continue
        start = date.fromisoformat(row["start"])
        for size in (d for d in (1, 2, 3, 4, 6, 12) if amount % d == 0 and abs(amount) > d):
            steps = abs(amount) // size
            values = date_range(start, count=steps + 1, step=f"{amount // steps} months")
            assert list(values)[-1] == date.fromisoformat(row["result"]), (row, size)
            checked += 1
    assert checked > 1000


def test_the_fixture_is_what_dotnet_prints_today(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.skip("PowerShell 7 is not installed")
    copy = tmp_path / "scripts"
    copy.mkdir()
    shutil.copy(ROOT / "scripts" / "dotnet_oracle.ps1", copy)
    (tmp_path / "tests" / "data").mkdir(parents=True)
    script = copy / "dotnet_oracle.ps1"
    subprocess.run([pwsh, "-NoProfile", "-File", str(script)], check=True, timeout=240)
    fresh = (tmp_path / "tests" / "data" / "dotnet_calendar.csv").read_text(encoding="utf-8")
    assert fresh.splitlines()[1:] == DATA.read_text(encoding="utf-8").splitlines()[1:]
