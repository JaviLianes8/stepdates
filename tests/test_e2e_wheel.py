"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with STEPDATES_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULES = sorted(p.name for p in (ROOT / "src" / "stepdates").glob("*.py"))

pytestmark = pytest.mark.skipif(
    os.environ.get("STEPDATES_E2E") != "1", reason="set STEPDATES_E2E=1 to build"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources
from datetime import date, datetime, timedelta, timezone
import stepdates as s

assert "site-packages" in s.__file__, s.__file__
assert importlib.metadata.version("stepdates") == s.__version__
assert importlib.resources.files("stepdates").joinpath("py.typed").is_file()
assert sorted(s.__all__) == ["InvalidPolicy", "date_range", "shift"]
assert s.__version__ == "1.0.0"

d = date
assert list(s.date_range(d(2026, 1, 31), count=3, step="month")) == [
    d(2026, 1, 31), d(2026, 2, 28), d(2026, 3, 31)]
assert list(s.date_range(d(2026, 1, 31), count=3, step="P1M", invalid="skip")) == [
    d(2026, 1, 31), d(2026, 3, 31), d(2026, 5, 31)]
assert list(s.date_range(d(2026, 4, 30), d(2026, 7, 1), step="month", end_of_month=True)) == [
    d(2026, 4, 30), d(2026, 5, 31), d(2026, 6, 30)]
assert list(s.date_range(d(9999, 12, 30), d.max, step="week", inclusive=True)) == [
    d(9999, 12, 30)]
assert s.shift(d(2024, 2, 29), "-1 year") == d(2023, 2, 28)
assert s.shift(d(2026, 1, 1), timedelta(days=-1)) == d(2025, 12, 31)
start = datetime(2026, 1, 31, 9, tzinfo=timezone.utc)
assert s.shift(start, "quarter") == datetime(2026, 4, 30, 9, tzinfo=timezone.utc)
for bad in (dict(step="fortnight"), dict(invalid="roll"), dict(count=2, inclusive=True)):
    try:
        list(s.date_range(d(2026, 1, 1), **{"count": 2, **bad}))
    except ValueError:
        pass
    else:
        raise AssertionError(bad)
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> bytes:
    result = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    (wheel,) = dist.glob("stepdates-*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    assert not [name for name in names if "vectors" in name or name.startswith("tests/")]
    package = {name for name in names if name.startswith("stepdates/")}
    assert package == {f"stepdates/{n}" for n in MODULES} | {"stepdates/py.typed"}
    assert any(name.endswith(".dist-info/licenses/LICENSE") for name in names)

    _run(sys.executable, "-m", "build", "--sdist", "--outdir", dist, ROOT)
    (sdist,) = dist.glob("stepdates-*.tar.gz")
    with tarfile.open(sdist) as archive:
        members = archive.getnames()
    data = [name for name in members if "/tests/vectors/" in name]
    assert data == [name for name in data if name.endswith("/MANIFEST.txt")]
    top = {name.split("/", 1)[1] for name in members if name.count("/") == 1}
    assert top == {"README.md", "GUIDE.md", "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE",
                   "PKG-INFO", "pyproject.toml", "requirements-dev.txt", ".gitignore"}  # fmt: skip
    assert not [name for name in members if "__pycache__" in name or name.endswith(".pyc")]

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    _run(python, "-m", "pip", "install", "-q", wheel)

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    assert _run(python, "-I", "-c", PROGRAM, cwd=work).decode().splitlines() == ["e2e ok"]

    script = bindir / ("stepdates.exe" if sys.platform == "win32" else "stepdates")
    out = _run(script, "2026-01-31", "-n", "3", "-s", "1 month", cwd=work).decode()
    assert out.split() == ["2026-01-31", "2026-02-28", "2026-03-31"]
    out = _run(python, "-I", "-m", "stepdates", "2026-01-31", "-n", "2", "--skip-invalid",
               "-s", "month", cwd=work).decode()  # fmt: skip
    assert out.split() == ["2026-01-31", "2026-03-31"]
    assert _run(script, "--version", cwd=work).decode().split() == ["stepdates", "1.0.0"]
    back = _run(script, "2026-01-05", "2026-01-01", "-s", "-P2D", "--inclusive", cwd=work)
    assert back.decode().split() == ["2026-01-05", "2026-01-03", "2026-01-01"]
    bad = subprocess.run([str(script), "2026-01-01"], cwd=work, capture_output=True, check=False)
    assert bad.returncode == 2
    assert b"exactly one of stop or count" in bad.stderr
