# Contributing

Please follow the [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Report security
vulnerabilities as described in [`SECURITY.md`](SECURITY.md).

## Setup

Install dependencies and local Git hooks:

```sh
uv sync --all-packages
uv run poe setup
```

`uv run poe setup` runs `uv run poe sync-githooks`, which registers repo-local
Git hook config for scripts named `scripts/githooks/<event>.<name>.<ext>`. Each
hook is installed as `hook.<event>-<name>` and marked as managed by this repo;
unmarked user hook config is not overwritten. Pre-commit hooks are installed
with `WORKSPACE_POE_GIT_SCOPE=staged` so they run against the staged index, and
pre-push hooks are installed with `WORKSPACE_POE_GIT_SCOPE=commit` so they run
against the commit tree being pushed instead of unrelated dirty worktree
changes.

The `pre-commit.checks` hook runs `uv run poe pre-commit`, which runs lint and
typecheck in parallel with buffered output. The `pre-push.checks` hook runs
`uv run poe pre-push`, which runs new-package version, news-fragment, lint,
typecheck, and test checks in parallel with buffered output. New packages must
start at the unpublished `0.0.0` sentinel; the release workflow assigns their
first publishable version. Unpublished packages are exempt from news-fragment
enforcement until a fragment is added deliberately to request their first
release. Git hooks are local clone state, so each checkout needs this once.

## Development Commands

Run the standard checks before opening a PR:

```sh
uv run poe qa
```

Measure coverage with `uv run poe coverage`. It runs the workspace tests with
xdist workers, enforces the floor in `scripts/coverage.py`, and writes
`coverage.xml` for the CI artifact.

`uv run poe type-ignores` ratchets `# type: ignore` comments against
`scripts/type-ignore-baseline.json`; run `python scripts/check_type_ignores.py
--update` when you remove an ignore.

`qa` runs lint, typecheck, and tests. It accepts package and file scopes, plus
`-q`/`--quiet` and `-v`/`--verbose`; because it is an aggregate task, it does
not accept tool-specific arguments after `--`. It is fail-fast, so later checks
do not run after an earlier check fails.

The individual checks are also available as top-level Poe tasks:

```sh
uv run poe lint
uv run poe typecheck
uv run poe test
```

For focused work, pass scopes before `--` and tool arguments after `--`:

```sh
uv run poe qa tests/unit/test_release_system.py
uv run poe test tests/unit/test_time.py -- -k coerce_duration
uv run poe test khulnasoft-oidc
uv run poe typecheck khulnasoft-queue
```

### Test Layout

Tests live in three tiers:

- `tests/` at the repository root covers workspace tooling: the task runner,
  release and publishing scripts, and repository layout guards.
- `src/khulnasoft/tests/` covers the `khulnasoft` meta package.
- `<package>/tests/` covers that package. Tests that need live credentials live
  under `tests/live/` and carry the `live` marker.

Every package that defines a `live` marker or has a `tests/live/` directory must
also add `-m 'not live'` to its pytest `addopts`, so the default run never
reaches the network. A dedicated task may override the marker explicitly; see
the Sandbox `test-live` task. `tests/unit/test_workspace_layout.py` enforces the
default exclusion.

Example tests are an opt-in workspace aggregate. Run all declared example
tasks, or scope to one package and pass pytest arguments after `--`:

```sh
uv run poe test-examples
uv run poe test-examples khulnasoft-sandbox
uv run poe test-examples khulnasoft-sandbox -- -k sessions_and_resume
```

Each participating package owns its executable-example discovery, pytest
runner and configuration, credential checks, setup, and cleanup. Packages opt
in with a local `[tool.poe.tasks.test-examples]` declaration; packages without
one are skipped by the unscoped aggregate and are rejected if explicitly
requested. Cross-package examples belong in the root `examples/` directory;
package-specific examples belong in `<package>/examples/`. Root examples are run
by the root package's internal `test-examples-root` task.

The canonical task does not acquire credentials automatically. For local
Sandbox runs, supply an OIDC token explicitly when needed:

```sh
KHULNASOFT_OIDC_TOKEN="$(vc project token)" uv run poe test-examples khulnasoft-sandbox
```

CI supplies `BLOB_READ_WRITE_TOKEN`, `KHULNASOFT_TOKEN`, `KHULNASOFT_PROJECT_ID`, and
`KHULNASOFT_TEAM_ID`; package-owned checks skip live examples safely when those
secrets are unavailable.

Pull requests run the Python 3.12 gate (`poe lint`, `poe typecheck`,
`poe coverage`, the news-fragment check, and
`uv build --all-packages --no-sources`) plus the pre-commit workflow. Pushes to
`main` and the nightly schedule also run the test suite on Python 3.10 through
3.14, and run `poe test-examples` as a post-merge signal. The nightly schedule
also audits the locked environment with `pip-audit` and uploads a CycloneDX
SBOM.

Auto-fix formatting and simple lint issues with:

```sh
uv run poe fix
```

Remove local caches, coverage files, and build artifacts with:

```sh
uv run poe clean
```

Pass `--dry-run` to preview or `--venv` to include the virtual environment:

```sh
uv run python scripts/clean.py --dry-run
```

The workspace task system is documented in `scripts/poe/README.md`.

## News Fragments

User-visible package changes need a news fragment:

```text
changes/<package>/<id>.<type>.md
```

Valid types are `breaking`, `feature`, `bugfix`, `docs`, and `internal`.
News fragment content should be concise changelog text; the release script adds
the leading bullet marker when needed.

Example:

```text
changes/khulnasoft-cache/123.bugfix.md
```

Use `uv run poe lint-towncrier` to validate existing news fragments. The Git
`pre-push.news-fragments` hook enforces that changed package code has a
news fragment, except while a package remains at the unpublished `0.0.0`
sentinel. Add its first fragment when the package is ready for its initial
`0.1.0` release. Packages imported from a previous release stream are listed in
`scripts/release-migrated-packages.txt`; the check skips them so their existing
versions are preserved. Keep that list limited to the migration and remove it
after the migration release. The hook does not replace the full
lint/test/typecheck suite.

Release PR mechanics, version bump rules, dependency cascades, and publishing
are documented in `RELEASING.md`.

## Package Builds

Build all workspace packages with:

```sh
uv build --all-packages --no-sources
```

For a focused package build, use `uv build` directly:

```sh
uv build --package khulnasoft-cache --no-sources
```

`--no-sources` is important for publishability checks because it verifies the
wheel metadata without local workspace source overrides.

## Commit Messages

Keep commit messages short and specific. Use a title line of 50 characters or
fewer, wrap body lines at 72 characters, and explain what changed and why. Do
not include `Co-authored-by:` lines.
