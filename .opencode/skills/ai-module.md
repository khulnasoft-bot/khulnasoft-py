# khulnasoft.ai Module Skill

This skill provides guidance for working on the `src/khulnasoft/ai/` module — AI agents, models, tools, streaming, and telemetry.

## When to use

Use this skill when modifying `src/khulnasoft/ai/` or its subpackages (agents, models, ops, providers, types, ui, experimental_telemetry, durable, errors, testing, util).

## Module structure

- `agents/` — Agent runtime: `Agent`, `AgentStream`, `Context`, tools (`tool()`, `AgentTool`, `ToolRunner`), streaming internals
- `types/` — Event and message types (`BaseEvent`, `ModelEvent`, `Event`, `Message`, `ToolResultPart`, builders)
- `providers/` — Provider implementations (OpenAI, Anthropic, AI Gateway, TypeSafe) + shared `_protocol_common.py`
- `experimental_telemetry/` — Spans, sinks, adapters, ambient clock
- `models/` — Model selection, params, inference requests
- `ops/` — Model operations (audio, embeddings, images, reranking, transcriptions, videos)
- `ui/` — AI SDK UI protocol adaptation (outbound_stream, outbound_messages, inbound_messages)
- `util.py` — Utilities (TaskGroup, MultiWaiter, merge, decouple)

## Key conventions

- Python 3.12+ required (PEP 695 syntax: `class X[T]`, `def f[T]`, `type X = ...`)
- Public API is exported via `src/khulnasoft/ai/__init__.py` — never remove or rename exports without updating `__all__`
- Provider protocols share conversion logic via `providers/_protocol_common.py`
- Characterization tests live in `src/khulnasoft/ai/tests/test_public_exports.py` (lock in `__all__`)

## Common tasks

### Splitting an oversized module
1. Add characterization tests (if not present)
2. Create new focused submodule(s)
3. Update `__init__.py` re-exports to preserve public API
4. Update imports in dependent modules
5. Run `uv run poe qa src/khulnasoft/ai`
6. Add news fragment in `changes/khulnasoft/`

### De-duplicating provider protocols
1. Extract shared utilities to `providers/_protocol_common.py`
2. Update provider protocol modules to import from common
3. Add protocol parity tests
4. Run `uv run poe qa src/khulnasoft/ai`

### Running checks
- `uv run --python 3.12 -m pytest src/khulnasoft/ai/tests`
- `uv run ruff check src/khulnasoft/ai`
- `uv run ruff format --check src/khulnasoft/ai`
- `uv run --python 3.12 -m mypy --config-file pyproject.toml src/khulnasoft/ai`
