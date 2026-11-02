# `src/khulnasoft/ai` Refactoring Plan

Scope: `src/khulnasoft/ai/` (22.9k LOC). Goal: reduce module size/coupling, improve testability, preserve public API.

## Findings

- Oversized modules: `providers/openai/protocol.py` (1930), `agents/agent.py` (1697), `experimental_telemetry/span.py` (1215), `types/events.py` (916), `ui/ai_sdk/outbound_stream.py` (677).
- Provider protocols duplicate conversion logic across OpenAI/Anthropic/AI Gateway/v3/v4.
- No dedicated tests under `src/khulnasoft/ai`; behavior covered only indirectly.
- `ui/ai_sdk` mixes parsing, streaming, and event mapping in large files.
- Telemetry span construction is monolithic.

## Plan

### Phase 0 — Baseline (no behavior change) — COMPLETE

- Added characterization tests: `src/khulnasoft/ai/tests/test_public_exports.py` — 119 passed, locking in every name in `ai.__all__`, all provider modules, `get_provider`, and submodule exposure.
- Fixed pre-existing import blockers: truncated `create_contextual` in `providers/ai_gateway/client/errors.py`, truncated `_gateway_auth` in `providers/ai_gateway/provider.py`, installed missing `modelsdotdev` dep.
- Migrated to Python 3.12+ (PEP 695 syntax `class X[T]`, `def f[T]`, `type X = ...` used throughout). Updated `pyproject.toml` `target-version` from `py310` → `py312`.
- Remaining ruff errors are all pre-existing (F401, BLE001, UP047, I001); none introduced by this work.

### Phase 1 — Split oversized modules — COMPLETE

**agent.py** (1,697 LOC) → `agent.py` + `agent_tools.py` + `agent_streaming.py`
**types/events.py** (916 LOC) → `events.py` + `agent_events.py` + `message_hydrator.py`
**experimental_telemetry/span.py** (1,215 LOC) → `span.py` + `span_data.py` + `clock.py` + `sink.py` + `adapters.py`
**ui/ai_sdk/outbound_stream.py** (677 LOC) → `outbound_stream.py` + `outbound_state.py`

All public APIs preserved via `__init__.py` re-exports. All 119 characterization tests pass. No new lint issues. All files `ruff format`-clean.

New files created (8):
- `src/khulnasoft/ai/agents/agent_tools.py`
- `src/khulnasoft/ai/agents/agent_streaming.py`
- `src/khulnasoft/ai/types/agent_events.py`
- `src/khulnasoft/ai/types/message_hydrator.py`
- `src/khulnasoft/ai/experimental_telemetry/span_data.py`
- `src/khulnasoft/ai/experimental_telemetry/clock.py`
- `src/khulnasoft/ai/experimental_telemetry/sink.py`
- `src/khulnasoft/ai/experimental_telemetry/adapters.py`
- `src/khulnasoft/ai/ui/ai_sdk/outbound_state.py`

### Phase 2 — De-duplicate provider protocols — DONE (shared utilities)

Created `src/khulnasoft/ai/providers/_protocol_common.py` with shared utilities
that were verbatim duplicated across OpenAI and Anthropic protocol modules:

- `is_default()` / `not_default()` — `ModelProviderDefault` sentinel checks
- `seed_value()` — seed coercion to int or None
- `filter_extra_headers()` — drop `Unset` header values
- `tool_ref_name()` — normalize tool ref to string name

Updated `providers/openai/protocol.py` and `providers/anthropic/protocol.py`
to import from `_protocol_common` instead of defining local copies. Removed
~60 lines of duplicated code across the two files (~30 each).

Provider-specific conversion logic (`_tools_to_openai`, `_custom_tools_to_anthropic`,
`_file_part_to_*`, `_messages_to_*`, `_apply_sampling` variants) stays in each
provider's module since wire formats differ.

Remaining duplication candidates (lower priority):
- `_apply_sampling` — similar structure, provider-specific error messages
- File part conversion — different wire formats per provider
- Tool conversion — different OpenAI vs Anthropic schemas

### Phase 3 — Test coverage — DONE

Added `src/khulnasoft/ai/tests/` with unit tests:

- `test_public_exports.py` — 119 characterization tests for the public API surface (every name in `ai.__all__`, all provider modules, `get_provider`, submodule exposure)
- `test_protocol_common.py` — 21 tests for shared provider utilities (`is_default`, `not_default`, `seed_value`, `filter_extra_headers`, `tool_ref_name`)
- `test_builders.py` — 15 tests for message builders (`message`, `user_message`, `system_message`, `assistant_message`, `tool_message`, `text_part`, `file_part`, `content_output`, `tool_result_part`, `thinking`)

Total: 149 tests passing.

### Phase 4 — Cleanup — DONE

- Updated imports across 10 files that referenced moved event types (`AgentEvent`, `ToolCallResult`, `HookEvent`, `PartialToolCallResult`, `RunBlocked`, `Retry`, `_RetryFilter`, `Aggregator`, `_replay_message_events`, `MessageHydrator`) to import from their new submodules (`agent_events`, `message_hydrator`) for mypy compatibility.
- Added news fragment: `changes/khulnasoft/20261102000000.internal.md`
- All 149 tests pass, lint clean (only pre-existing BLE001), format clean.

All phases complete.

## Risks

- Public API stability: keep `__init__` exports unchanged.
- Provider protocol changes can affect streaming; require golden tests.

## Verification

- `uv run poe lint src/khulnasoft/ai`
- `uv run poe typecheck`
- `uv run poe test`
- `uv run poe check-news-fragments`
