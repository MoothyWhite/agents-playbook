---
name: python-toolchain
description: >
  Guide for the Astral Python toolchain: uv (package and project manager),
  ruff (linter and formatter), and ty (type checker). Use when working with
  Python projects — managing dependencies or environments, linting or
  formatting Python code, or type checking. Invocations, configuration, and
  migration from pip, Poetry, Black, Flake8, isort, mypy, Pyright, pyenv, pipx.
---

# Python toolchain

uv runs the project, ruff lints and formats, ty checks types. Three tools, one
workflow; together they replace pip, Poetry, Black, Flake8, isort, mypy,
Pyright, pyenv, pipx, and more.

## Which tool when

| Task | Tool | Details |
|---|---|---|
| Dependencies, environments, running scripts and tools | uv | [references/uv.md](./references/uv.md) |
| Linting and formatting | ruff | [references/ruff.md](./references/ruff.md) |
| Type checking | ty | [references/ty.md](./references/ty.md) |

Recognition signals: `uv.lock` or uv headers in requirements files → uv
project; `[tool.ruff]` or `ruff.toml` → ruff; `[tool.ty]` or `ty.toml` → ty.
Poetry (`poetry.lock`) and PDM (`pdm.lock`) projects are not uv projects —
don't run uv there.

## Unified invocation

- `uv run <tool> ...` — the tool is a project dependency; uses the pinned version
- `uvx <tool> ...` — the tool is not a project dependency, or a one-off check
- `<tool> ...` — installed globally

Never use pip or a bare `python` inside uv projects. See
[references/uv.md](./references/uv.md).

## Pipeline after editing Python code

Run in this order — lint fixes can restructure code, formatting cleans up
after, type errors are cheapest to read on clean code, and coverage gaps are
cheapest to judge on passing tests:

```bash
uv run ruff check --fix .
uv run ruff format .
uv run ty check
```

Then run tests and judge which coverage gaps are worth closing →
pytest-coverage skill.
