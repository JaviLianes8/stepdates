"""Run the command line tool with ``python -m stepdates``."""

from __future__ import annotations

import sys

from stepdates._cli import main

if __name__ == "__main__":
    sys.exit(main())
