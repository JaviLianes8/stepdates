"""Seeded random command lines: the tool ends with a status, never with a traceback."""

from __future__ import annotations

import contextlib
import io
import random

import pytest

from stepdates._cli import main

SEEDS = [11, 2026, 90210]

# The far dates only start a command line, so a random stop never asks for millions of lines.
STARTS = [["2026-01-31"], ["9999-12-31"], ["9999-11-30"], ["0001-02-01", "-n", "40"],
          ["2026-03-08T02:30"], ["x"], ["-n"]]  # fmt: skip
TOKENS = ["2026-01-31", "2024-02-29", "2026-12-31", "2026-03-08T02:30", "x",
          "-n", "3", "-1", "999", "--count", "-s", "--step", "month", "-P1M", "P2W", "2 days",
          "0 days", "--inclusive", "--skip-invalid", "--end-of-month", "-f", "%Y", "%d/%m",
          "--format", "", "--", "--bogus"]  # fmt: skip


@pytest.mark.parametrize("seed", SEEDS)
def test_random_command_lines_end_with_a_status_never_a_traceback(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(1_500):
        argv = rng.choice(STARTS) + [rng.choice(TOKENS) for _ in range(rng.randint(0, 6))]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code: object = main(argv)
            except SystemExit as exit:
                code = exit.code
        assert code in (0, 1, 2), (argv, code)
        assert "Traceback" not in err.getvalue()
        if code == 1:
            assert "years 1 to 9999" in err.getvalue()
