# Repository Structure Analysis and Development Improvement Plan

Date: 2026-10-25
Supersedes: the 2026-10-24 gap analysis in this file.
Scope: repository layout, workspace organization, CI/release shape, developer workflow.
Method: inspected the git index and worktree, walked every package's build metadata,
read the task runner and workflows, and ran the canonical checks.

This document describes the plan and records its implementation status. Phase 0
does not change product behavior.

## Implementation status

Phase 0 completed on 2026-10-25:

- S1: the workspace migration is committed in a reviewable series, and the local
  KhulnaSoft CLI binding is ignored.
- S2: `uv run poe clean` removes caches, coverage files, and build artifacts.
- S17: `uv.lock` is tracked and `uv lock --check` passes.
- S15/S16: onboarding docs now point at the canonical workspace commands.
- The new-package version guard skips packages imported with prior release
  versions via `scripts/release-migrated-packages.txt`, avoiding a false
  positive on the migration.

Verified after Phase 0: `poe lint`, `poe typecheck`, the full `poe test` suite,
`poe check-news-fragments`, `poe check-new-package-versions`, `uv lock --check`,
and `zizmor --offline .`.

Phase 1 completed on 2026-10-25:

- S4: both workflows install with `uv sync --all-packages --frozen`; CI builds
  with `uv build --all-packages --no-sources`.
- S8: the pull-request lane runs `poe qa`, `poe check-news-fragments`, then the
  build. Pushes to `main` and the nightly schedule run the full test matrix.
- S14: pre-commit delegates lint and typecheck to the canonical Poe tasks; the
  remaining hooks check whitespace, YAML, TOML, and large files.
- S7: the matrix covers Python 3.10 through 3.14.
- Fixed a latent pydantic `TypeAdapter` typing error in the workflow tests that
  the canonical typecheck surfaced while validating the pre-commit hooks.

Verified after Phase 1: `poe qa`, `pre-commit run --all-files`,
`uv build --all-packages --no-sources`, `uv lock --check`, and
`zizmor --offline .`.

Phase 4 follow-up completed on 2026-10-26:

- Consolidated workspace discovery: `scripts/poe/workspace_poe_resolve.py` now
  imports `workspace_members()` from `scripts/workspace.py` instead of running
  its own `uv workspace list` parser.
- Added package-owned tests for `khulnasoft-headers` and
  `khulnasoft-internal-telemetry`; the header context test moved out of the meta
  package into its owner. Both packages no longer stub `poe test` with a no-op.
- Wired `khulnasoft-queue` into `poe test-examples` with a source/compile check,
  and made the root example harness compile nested example apps.
- De-duplicated the PR gate: CI now runs `poe lint`, `poe typecheck`, and
  `poe coverage` instead of running the full suite through both `poe qa` and
  `poe coverage`.
- Replaced the eleven duplicated `hatch_build.py` loader files with
  `_khulnasoft_hatch_build.py` symlinks to `scripts/hatch_build.py`; sdists still
  contain a real copy, and `uv build --all-packages --no-sources` rebuilds every
  wheel from its sdist.
- Added layout guards for owned tests, shared manifest boilerplate, and shared
  Hatch hook symlinks in `tests/unit/test_workspace_layout.py`.

Remaining from section 3: `khulnasoft._internal` vs `khulnasoft.internal`
naming (S10), broad-except ratcheting (S19), and live queue example execution
(static checks replace silent omission; they do not exercise delivery).

## 1. Repository at a glance

| Area | Location | Purpose |
| --- | --- | --- |
| Meta package | `src/khulnasoft/` | Blob, cron, deployments, functions, project routes, projects |
| Feature packages | `src/khulnasoft-*` (9) | cache, connect, headers, internal-core, internal-telemetry, oidc, queue, sandbox, workflow |
| Integrations | `integrations/khulnasoft-*` (4) | apscheduler, celery, django-tasks, dramatiq |
| Workspace tooling | `scripts/poe/` | PoE task graph, scope resolution, per-tool wrappers |
| Git hooks | `scripts/githooks/` | pre-commit and pre-push entry points |
| Workspace tests | `tests/` | Tooling, release, publish, vendoring, root example tests |
| Package tests | `src/*/tests/`, `integrations/*/tests/` | Owning package's unit/integration/live tests |
| Meta-package tests | `src/khulnasoft/tests/` | Blob, cron, projects, sync/async parity |
| Examples | `examples/`, `src/*/examples/`, `integrations/*/examples/` | Runnable documentation |
| Vendored test dep | `vendor/respx/` | respx ported to httpx2 |
| News fragments | `changes/<package>/*.md` | Changelog input for `scripts/release.py` |
| Generated config | `.khulnasoft/project.json` | Local project binding, not source |

Current size: 10 workspace packages under `src/`, 4 integrations, 527 Python files
in the worktree, and 196 package-owned test files.

### How the pieces compose

- `[tool.uv.workspace] members = ["src/*", "integrations/*"]` makes this a single
  uv workspace (`pyproject.toml:44-45`).
- Every package ships into the shared `khulnasoft.*` namespace. There is no
  top-level `src/khulnasoft/__init__.py`; composition relies on PEP 420 implicit
  namespace packages. `src/khulnasoft/internal/README.md` documents that
  `khulnasoft.internal` is reserved for standalone internal packages.
- The root `khulnasoft` package is a meta package: it declares workspace
  dependencies on cache, headers, internal-core, internal-telemetry, oidc, queue,
  sandbox, and workflow (`src/khulnasoft/pyproject.toml:20-48`).
- The root `pyproject.toml` is intentionally not publishable: it has no
  `[project]`, and `scripts/no_root_build.py` raises a message directing callers to
  `uv build --all-packages --no-sources`.
- Developer commands go through PoE into `scripts/poe/workspace_poe.py`, which
  applies scopes and dispatches package-local tasks. Each package includes
  `scripts/poe/poe.toml`.
- Releases are driven by news fragments plus `scripts/release.py`,
  `scripts/bundle_release.py`, and three publishing workflows.

## 2. Verified baseline

Run on 2026-10-25 in this worktree:

| Command | Result |
| --- | --- |
| `uv run poe lint` | Pass |
| `uv run poe typecheck` | Pass |
| `uv run poe test` (full workspace) | Pass |
| `uv run poe test tests/unit` | Pass |

Not re-run during this analysis: `poe test-examples`, `poe check-news-fragments`,
`poe check-new-package-versions`, `zizmor --offline .`.

The code is healthy. The risk is organizational: most of the repository is not
in version control, and CI/release automation still describes a single-package
layout.

## 3. Structural findings

Severity: P0 blocks reliable delivery; P1 causes drift or rework; P2 is polish.

### A. Version control and workflow

| ID | Sev | Finding | Evidence | Impact |
| --- | --- | --- | --- | --- |
| S1 | P0 | The workspace migration is uncommitted. None of the split packages, `integrations/`, `vendor/`, `scripts/poe/`, or `.github/scripts/` are tracked. | `git ls-files src/khulnasoft-oidc` = 0; 58 untracked paths; 91 modified/deleted tracked files; 10,193 deletions; 114 tracked files vs 527 Python files | CI and reviewers see a different repository than the one that passes locally. One `git clean` would destroy the refactor. History is lost if moves are committed as unrelated adds/deletes. |
| S2 | P1 | Local developer artifacts sit inside the tree next to source. | `.pytest_cache/`, `.hypothesis/`, `__pycache__/` under `src/` and `integrations/`; `.khulnasoft/project.json`; `.venv/` | Noise in search and file pickers, accidental commits, slower `git status`. |
| S3 | P2 | The repository lacks `SECURITY.md` and `CODE_OF_CONDUCT.md`. | root listing; `README.md` links neither | Reporting paths for vulnerabilities or conduct issues are not discoverable. |

### B. CI and release shape

| ID | Sev | Finding | Evidence | Impact |
| --- | --- | --- | --- | --- |
| S4 | P0 | CI installs the workspace root as a package. The root has no `[project]` and its build backend raises by design. | `.github/workflows/ci.yml:36` (`uv pip install -e .[dev]`), `ci.yml:48` (`python -m build`); `pyproject.toml:1-4`; `scripts/no_root_build.py:3-6` | CI cannot reach the lint/typecheck/test steps. The same mistake is in `.github/workflows/pre-commit.yml:34`. |
| S5 | P0 | Publish and redistribute still assume exactly one package. | `publish.yml:20-40` checks only `pypi.org/pypi/khulnasoft`; `publish.yml:78` builds the root; `redistribute.yml:27-40` builds the root sdist and runs `pip install -e .` | Any of the 10 feature packages or 4 integrations cannot be released through the documented path. The root build fails by design. |
| S6 | P1 | Publishing has no concurrency guard and triggers on every push to `main`. | `publish.yml:2-5`, no `concurrency:` block | Two pushes can race tag creation and PyPI uploads. |
| S7 | P1 | CI runs one Python version while tox declares five. | `ci.yml` uses 3.12 only; `pyproject.toml:73-83` lists `py310`–`py314` | Version-specific breakage reaches release; the declared support matrix is not exercised. |
| S8 | P1 | CI runs a hand-written subset instead of the canonical gate. | `ci.yml:39-45` runs lint/typecheck/test but not `check-news-fragments`; `qa` is documented as the gate in `AGENTS.md` | A PR can merge while failing a check that local `poe qa` enforces. |
| S9 | P2 | Actions pins are inconsistent across workflows. | `zizmor.yml` uses `actions/checkout@… # v6.0.2`; every other workflow uses `# v7.0.1` | Mixed upgrade states and Dependabot noise. |

### C. Package layout and consistency

| ID | Sev | Finding | Evidence | Impact |
| --- | --- | --- | --- | --- |
| S10 | P1 | Namespace composition is implicit and unguarded. Two packages could ship the same module path without any check. Internal naming is also inconsistent. | `src/khulnasoft-internal-core/.../khulnasoft/_internal/core/` vs `src/khulnasoft-internal-telemetry/.../khulnasoft/internal/telemetry/`; no conformance test | Silent module shadowing that only appears in an installed environment, not in a workspace checkout. |
| S11 | P1 | Test topology is undocumented and live-test filtering is inconsistent. | Root `tests/` (10 files), `src/khulnasoft/tests/` (21 files), 196 package tests; only connect, oidc, and sandbox add `-m 'not live'` to `addopts` | Contributors guess where a test belongs; packages with a live marker can accidentally hit the network. |
| S12 | P1 | Root examples and package examples overlap, and examples are not exercised in CI. | `examples/` holds blob, projects, and runtime cache demos while `src/khulnasoft-sandbox/examples/` and `src/khulnasoft-queue/examples/` hold their own; no example job in `.github/workflows/` | Two homes for the same kind of artifact; examples rot silently. |
| S13 | P2 | Orphan/placeholder directories exist. | `src/khulnasoft/internal/README.md` is documentation only and is not included in the wheel `only-include` list | Confusing structure; readers cannot tell whether the directory is shipped. |

### D. Tooling and documentation

| ID | Sev | Finding | Evidence | Impact |
| --- | --- | --- | --- | --- |
| S14 | P1 | Pre-commit drifts from the project tool pins and dependencies. | `.pre-commit-config.yaml:3` ruff `v0.17.2` vs `pyproject.toml:8` `0.15.20`; `.pre-commit-config.yaml:10` mypy `v1.11.0` vs `pyproject.toml:19` `>=1.20.2`; hook deps pin `httpx`, not `httpx2` | Local hooks disagree with CI; mypy may not resolve the same imports. |
| S15 | P1 | Documentation references a task that does not exist. | `CONTRIBUTING.md:127` says `uv run poe build-packages`; no such task in `pyproject.toml` or `scripts/poe/` | Copy-pasted onboarding fails. |
| S16 | P2 | README development commands bypass the canonical workflow. | `README.md:343-349` uses `uv run mypy src` and `uv run pytest -v` instead of `uv run poe qa` | Two competing definitions of "run the checks". |
| S17 | P1 | `uv.lock` is ignored although the workspace relies on reproducible resolution. | `.gitignore` last line `uv.lock`; the file exists but is untracked | Fresh resolves differ from the tested environment; `--frozen` is impossible. |

### E. Quality gates retained from the previous plan

| ID | Sev | Finding | Impact |
| --- | --- | --- | --- |
| S18 | P1 | No coverage measurement or threshold. | Regressions ship without visibility. |
| S19 | P1 | Broad exception and type-ignore debt remains (prior audit: 86 bare `except Exception:`, roughly 397 `type: ignore`). | Hidden failures and weakened typing. |
| S20 | P2 | No dependency vulnerability scan or SBOM. | Supply-chain findings surface late. |

## 4. Improvement plan

### Phase 0 — Capture the migration (P0, do first)

**S1 — Put the refactor under version control.**
- Confirm the intended move set: `src/khulnasoft/{cache,headers,oidc,sandbox,_telemetry}` move to
  `src/khulnasoft-*`; tests move to the owning package.
- Stage with rename detection so history follows the files
  (`git add -A`, then verify `git status` shows renames rather than add/delete pairs).
- Exclude local artifacts: `.khulnasoft/`, `.env.*`, caches, `.venv/`, and
  `vendor/**/__pycache__/`.
- Commit in reviewable slices: (1) workspace build and task runner, (2) package
  moves, (3) integrations, (4) vendored respx, (5) workflows/scripts, (6) docs.
- Add a news fragment only for user-visible package changes; this migration is
  mostly `internal`.
- Acceptance: `git status --porcelain` is clean; `git ls-files` includes all 14
  packages, `vendor/`, `scripts/poe/`, and `.github/scripts/`; lint, typecheck, and
  tests pass from a fresh clone.

**S2 — Add a cleanup entry point.**
- Add `poe clean` to remove caches, `dist/`, `build/`, and `*.egg-info`, and run it
  in onboarding docs. Do not delete `.khulnasoft/project.json` or `.env.*`.
- Acceptance: one command restores a quiet `git status` without touching source.

**S17 — Commit `uv.lock`.**
- Remove `uv.lock` from `.gitignore` and commit it.
- Acceptance: CI can run `uv sync --frozen`; a lock-only dependency bump is a
  reviewable diff.

### Phase 1 — One authoritative developer workflow (P0/P1, completed)

**S4 — Fix CI installation and build.**
- Replace `uv venv` + `uv pip install -e .[dev]` with
  `uv sync --all-packages --frozen` in both `ci.yml` and `pre-commit.yml`.
- Replace root `python -m build` with
  `uv build --all-packages --no-sources` (or per-package builds in a matrix).
- Acceptance: CI reaches lint/typecheck/test and produces all package artifacts.

**S8 — Make the canonical workspace checks the CI gate.**
- Run lint, typecheck, coverage, the news-fragment check, then build. Coverage
  owns the test execution so the suite does not run twice.
- Keep a fast single-version PR lane and a full matrix on `main`/nightly.
- Acceptance: a change rejected by local `poe qa` cannot merge.

**S15/S16 — Make the docs match the tasks.**
- Either add a `build-packages` PoE task wrapping
  `uv build --all-packages --no-sources`, or update `CONTRIBUTING.md:127`.
- Rewrite `README.md:343-349` to point at `uv sync`, `uv sync --all-packages`, and
  `uv run poe qa`.
- Acceptance: every command in onboarding docs exists and runs.

**S14 — Align pre-commit with project pins.**
- Preferred: make the hooks call the canonical commands (`uv run poe lint`,
  `uv run poe typecheck`) so there is one definition of each check.
- Otherwise pin exactly `ruff==0.15.20` and `mypy>=1.20.2,<2`, pass
  `--config-file=pyproject.toml`, and install `httpx2`, `pydantic`, `django-stubs`,
  `anyio`, and typing extras.
- Acceptance: `pre-commit run --all-files` matches `poe lint` and `poe typecheck`.

**S7 — Exercise supported Python versions.**
- Add a 3.10–3.14 matrix using `./scripts/test-python-matrix.sh` (or tox), with a
  single 3.12 PR lane to keep feedback fast.
- Acceptance: every declared version runs at least the unit suites.

### Phase 2 — Structure cleanup and consistency (P1)
S5/S6, S10, S11, S12, S13 complete: publishing/redistribute rewritten, namespace
wheel-include guard added, live-test default exclusion added and enforced, examples
README added, placeholder `internal/` deleted, and `poe test-examples` runs post-merge.

**S5/S6 — Redesign publishing for a monorepo.**
- Decide the release model before coding:
  - per-package publish matrix driven by `changes/` and version sentinels, or
  - a meta-package release that publishes `khulnasoft` plus any changed packages.
- Add a `concurrency` group with `cancel-in-progress: false` to `publish.yml`.
- Make `redistribute.yml` test the artifacts CI actually builds; install the dev
  group or call `poe test` instead of a partial pytest list.
- Acceptance: a dry run publishes or verifies every changed package exactly once.

**S10 — Guard namespace composition.**
- Add a workspace test that walks every package's `wheel.only-include` /
  module tree and fails if two packages claim the same module path.
- Standardize internal naming (`khulnasoft._internal.*` or `khulnasoft.internal.*`,
  not both) or document why each exists.
- Acceptance: installing all packages cannot silently shadow a module.

**S11 — Document and enforce test topology.**
- Document the three tiers in `CONTRIBUTING.md`:
  `tests/` = workspace tooling, `src/khulnasoft/tests/` = meta package,
  `<package>/tests/` = package-owned.
- Adopt one live-test policy: every package that defines a `live` marker must add
  `-m 'not live'` to `addopts`; add a test that enforces the rule.
- Acceptance: a contributor can place a new test without asking; no default run
  reaches the network.

**S12 — Give examples one owner and a signal.**
- Keep cross-package examples in root `examples/`; keep package-specific examples
  inside the package. Document the boundary.
- Add a nightly or post-merge `poe test-examples` job; make it required once stable.
- Acceptance: examples have a visible pass/fail signal.

**S13 — Resolve placeholder directories.**
- Either ship `khulnasoft/internal/README.md` deliberately (add it to the wheel
  include list) or move the note into package docs and delete the directory.
- Acceptance: no directory exists only as a comment.

**S18/S19/S20 — Quality gates** — complete.
- `scripts/coverage.py` runs the workspace tests with xdist workers, enforces an
  86% baseline floor via `poe coverage`, and writes `coverage.xml`; CI uploads it as
  an artifact and runs it on PRs.
- `scripts/check_type_ignores.py` ratchets `# type: ignore` counts against
  `scripts/type-ignore-baseline.json` (210 initial) via `poe type-ignores`.
- `BLE001` is enabled with per-file ignores for current hot spots; new source files
  cannot add broad `except`.
- `.github/workflows/ci.yml` has a scheduled/workflow_dispatch `audit` job running
  `pip-audit` and uploading a CycloneDX SBOM from `uv export`.

### Phase 3 — Governance and polish (P2)

**S3 — Add `SECURITY.md` and `CODE_OF_CONDUCT.md`.**
- Link both from `README.md` and `CONTRIBUTING.md`.
- Acceptance: reporting paths are discoverable.

**S9 — Normalize action pins.**
- Bring `zizmor.yml` to the same action versions as the other workflows and let
  Dependabot own upgrades.
- Acceptance: one version per action across `.github/workflows/`.

## 5. Target layout

```text
.
├── .github/
│   ├── scripts/                  # CI helpers (tracked)
│   └── workflows/
├── changes/<package>/            # news fragments
├── examples/                     # cross-package examples only
├── integrations/
│   └── khulnasoft-<name>/
│       ├── khulnasoft/integrations/<name>/
│       ├── tests/
│       └── examples/
├── scripts/
│   ├── githooks/
│   └── poe/                      # task graph and tool wrappers
├── src/
│   ├── khulnasoft/               # meta package
│   │   ├── blob/ cron/ deployments/ functions/ project_routes/ projects/
│   │   └── tests/
│   └── khulnasoft-<feature>/     # feature package
│       ├── khulnasoft/<feature>/
│       ├── tests/
│       └── examples/
├── tests/                        # workspace tooling tests
├── vendor/respx/
├── AGENTS.md CONTRIBUTING.md README.md RELEASING.md
├── SECURITY.md CODE_OF_CONDUCT.md
├── pyproject.toml
└── uv.lock
```

## 6. Ordering and gates

1. S1, S2, S17 — freeze the migration and lock dependencies.
2. S4, S8, S15, S16 — CI and docs use one workflow.
3. S14, S7 — local tools and version coverage match CI.
4. S5, S6 — publishing matches the monorepo.
5. S10, S11, S12, S13 — layout and test consistency.
6. S18, S19, S20 — measurable quality.
7. S3, S9 — governance and pin hygiene.

Do not start Phase 1 before Phase 0. Without a committed baseline, CI cannot
validate any later change.

## 7. Verification checklist

```sh
uv sync --all-packages
uv run poe clean
uv run poe lint
uv run poe typecheck
uv run poe test
uv run poe test-examples
uv run poe check-news-fragments
uv run poe check-new-package-versions
uv run zizmor --offline .
uv run poe qa
uv build --all-packages --no-sources
```

From a fresh clone, repeat the same commands before merging Phase 1.

## 8. Open decisions

- Release model: per-package publishing vs one meta-package release per cycle.
- Whether root `examples/` should remain or move into package-owned directories.
- Whether `khulnasoft.internal` and `khulnasoft._internal` are intentionally
  distinct or should be unified.
- Coverage floor and whether the full 3.10–3.14 matrix is required for every PR or
  only on `main`.
- Whether `vendor/respx` is a permanent fork or a temporary migration shim.
- When to remove `scripts/release-migrated-packages.txt` after the migration
  release.
