---
name: pytest-coverage
description: 'Run pytest tests with coverage and discover lines missing coverage, so the user can decide which gaps are worth closing.'
---

The goal is to find which lines are not covered by tests. 100% coverage is a ceiling, not the default target — which gaps are worth closing is the user's call (AGENTS.md: simple one-liners don't need tests).

Generate a coverage report with:

pytest --cov --cov-report=annotate:cov_annotate

If you are checking for coverage of a specific module, you can specify it like this:

pytest --cov=your_module_name --cov-report=annotate:cov_annotate

You can also specify specific tests to run, for example:

pytest tests/test_your_module.py --cov=your_module_name --cov-report=annotate:cov_annotate

Open the cov_annotate directory to view the annotated source code.
There will be one file per source file. If a file has 100% source coverage, it means all lines are covered by tests, so you do not need to open the file.

For each file that has less than 100% test coverage, find the matching file in cov_annotate and review the file.

If a line starts with a ! (exclamation mark), it means that the line is not covered by tests.
Add tests to cover the missing lines.

Report the uncovered lines, then add tests for the ones the user wants covered — not automatically for all of them.
