# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/stepdates/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Unit tests stay pure: no clock, network or files.
  Some tests reach further on purpose. The command line tests start Python in a subprocess;
  the wheel test builds the package and installs it in a fresh venv, and runs only with
  `STEPDATES_E2E=1`; the .NET test runs PowerShell 7 and skips without it; the RFC tests read
  texts that `scripts/fetch_vectors.py` downloads and skip until they are fetched.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
