# Python SDK Development Skill

This skill provides guidance for developing and refactoring Python packages in the KhulnaSoft SDK monorepo.

## When to use

Use this skill when working on any Python package under `src/` (e.g., `khulnasoft`, `khulnasoft-ai`, `khulnasoft-blob`, `khulnasoft-cache`, etc.).

## Guidelines

### Code style
- Follow the existing module conventions: `from __future__ import annotations` at the top
- Use `pyproject.toml` with `ruff` line-length = 100, `target-version = "py312"` (or `py310` for packages that support it)
- Run `uv run poe lint` and `uv run poe typecheck` before committing
- Run `uv run poe fix` to auto-fix lint issues

### Testing
- Tests live under `src/<package>/tests/`
- Run `uv run poe test <package>` to run package tests
- Run `uv run poe test-examples <package>` for example tests

### Refactoring
- Preserve public API stability via `__init__.py` re-exports
- Add characterization tests before refactoring (lock in `__all__`, imports, callables)
- Split oversized modules (>500 LOC) into focused submodules
- Update `AI_REFACTORING_PLAN.md` and `AI_REFACTORING_PLAN.md` progress
- Add news fragments in `changes/<package>/` with `uv run poe changelog`

### Common commands
- `uv run poe qa src/khulnasoft/ai` — lint, typecheck, and tests
- `uv run poe lint src/khulnasoft/ai` — lint checks
- `uv run poe typecheck src/khulnasoft/ai` — type checks
- `uv run poe test src/khulnasoft/ai` — run tests
- `uv run poe fix src/khulnasoft/ai` — auto-fix and reformat
- `uv run poe check-news-fragments` — verify news fragments
