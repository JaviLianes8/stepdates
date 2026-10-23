# stepdates 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to stepdates. Nothing is on PyPI yet
(`https://pypi.org/pypi/stepdates/json` answered 404 on 2026-10-23), so 1.0.0 is the first
release and there is no upgrade path to check; every change against `main` (a3d2e3c, 0.2.0)
is still listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (a3d2e3c, 0.2.0)
- [ ] Baseline gates on 0.2.0
- [ ] API review and 1.0.0 changes (item 1)
- [ ] Errors, typing, docstrings and doctests (items 2 to 5)
- [ ] Ground truth: specifications fetched live, reference implementations (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [ ] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [ ] Gates (item 15)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)
- [ ] PR and trace guard CLEAN (item 17); merge and publish left to the maintainer
