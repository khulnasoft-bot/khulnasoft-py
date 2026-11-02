# `khulnasoft.ai` — AI Agents & Models

`khulnasoft.ai` provides agents, models, tools, streaming, and telemetry for
building LLM-powered applications in Python.

## Quick start

```python
import khulnasoft.ai as ai

agent = ai.Agent(tools=[...])

async with agent.run(model, messages) as stream:
    async for event in stream:
        ...
    print(stream.output)
```

Declare a tool with `@ai.tool`:

```python
@ai.tool
async def fetch(url: str) -> str:
    ...
```

Streaming tools use an `Aggregate` marker:

```python
@ai.tool
async def research(topic: str) -> ai.StreamingStatusTool[str]:
    yield "connecting..."
    yield body  # final yield becomes the tool result
```

## Package layout

```
src/khulnasoft/ai/
├── __init__.py          # Public API surface
├── agents/              # Agent runtime: Agent, AgentStream, Context, tools
│   ├── agent.py         # Core runtime (Agent, AgentStream, Context)
│   ├── agent_tools.py   # Tool system (tool(), AgentTool, ToolRunner, aggregators)
│   ├── agent_streaming.py  # Streaming internals (yield_from, _aggregate_from)
│   ├── hooks.py         # Hooks: suspension points requiring external input
│   ├── mcp/             # MCP client integration
│   └── runtime.py       # Event sink connecting producers to consumers
├── agents/hooks.py      # Hooks registry and resolution
├── types/               # Event and message type definitions
│   ├── events.py        # Base model-streaming events (ModelEvent, Event union)
│   ├── agent_events.py  # Agent-layer events (ToolCallResult, HookEvent, RunBlocked)
│   ├── message_hydrator.py  # Reconstruct messages from event streams
│   ├── messages.py      # Message, Part, ToolResultPart, etc.
│   ├── builders.py      # Message construction helpers (*_message, tool_result_part)
│   ├── media.py         # Media part types
│   ├── tools.py         # Tool declarations
│   └── usage.py         # Token usage tracking
├── models/              # Model selection, params, and inference requests
│   └── core/            # Core model API (stream, generate, params)
├── ops/                 # Model operations (audio, embeddings, images, ...)
├── providers/           # Provider implementations (OpenAI, Anthropic, Gateway, ...)
│   ├── _protocol_common.py  # Shared protocol conversion utilities
│   ├── openai/          # OpenAI-compatible provider
│   ├── anthropic/       # Anthropic-compatible provider
│   ├── ai_gateway/      # AI Gateway provider
│   └── typesafe/        # TypeSafe provider
├── experimental_telemetry/  # Spans, sinks, adapters, ambient clock
│   ├── span.py          # Span model, current-span context, create_span/span
│   ├── span_data.py     # Span data types (RunSpanData, AiStreamSpanData, ...)
│   ├── clock.py         # Ambient span clock (now_ns, use_time)
│   ├── sink.py          # Span sinks (DictSink, RegistrySink)
│   └── adapters.py      # Adapter registry (register, adapter decorator)
├── durable.py           # Durable execution helpers
├── testing.py           # Test utilities (FakeModel, scripted conversations)
├── util.py              # Utility functions (TaskGroup, MultiWaiter, merge)
├── errors.py            # Error hierarchy (AIError, ProviderError, ...)
├── type_utils.py        # Type variable binding and resolution helpers
└── ui/                  # AI SDK UI protocol adaptation
    └── ai_sdk/          # outbound_stream, outbound_messages, inbound_messages, ...
```

## Key concepts

### Agents

An [`Agent`](src/khulnasoft/ai/agents/agent.py) bundles a model, a set of
tools, and a control loop. `Agent.run(model, messages)` streams events,
executes tool calls, and repeats until the conversation is complete.

### Tools

`@ai.tool` turns an async function into an executable
[`Tool`](src/khulnasoft/ai/types/tools.py). Tools can return plain values
or async generators. Async-generator tools declare an
[`Aggregate`](src/khulnasoft/ai/agents/agent_tools.py) to combine yielded
values into a final result.

### Events

The framework communicates via typed events:
- [`ModelEvent`](src/khulnasoft/ai/types/events.py) — streamed model output
  (text deltas, tool calls, reasoning, files)
- [`ToolCallResult`](src/khulnasoft/ai/types/agent_events.py) — tool execution
  outcome
- [`HookEvent`](src/khulnasoft/ai/types/agent_events.py) — hook suspension /
  resolution / cancellation
- [`RunBlocked`](src/khulnasoft/ai/types/agent_events.py) — run suspended on
  a deferred hook

### Hooks

[`Hook`](src/khulnasoft/ai/agents/hooks.py) are suspension points that
require external input (e.g. tool approval) before the run can continue.
Use [`ai.hook()`](src/khulnasoft/ai/agents/hooks.py) inside a run and
[`ai.resolve_hook()`](src/khulnasoft/ai/agents/hooks.py) from outside.

### Telemetry

[`experimental_telemetry`](src/khulnasoft/ai/experimental_telemetry/) emits
spans for runs, turns, model calls, and tool executions. Spans can be routed
to adapters (OpenTelemetry, console, ...) or collected via a
[`DictSink`](src/khulnasoft/ai/experimental_telemetry/sink.py).

## Module structure

See [`docs/ai/modules.md`](modules.md) for a detailed breakdown of every
module and its responsibilities.

## Testing

The package includes 149 unit tests under `src/khulnasoft/ai/tests/`:

- `test_public_exports.py` — characterization tests locking in the public API
- `test_protocol_common.py` — shared provider protocol utilities
- `test_builders.py` — message builder helpers

Run them with:

```bash
uv run --python 3.12 -m pytest src/khulnasoft/ai/tests
```

## Requirements

`khulnasoft.ai` uses Python 3.12+ syntax (PEP 695 generic type
parameters). See [`pyproject.toml`](../pyproject.toml) for the full
dependency list.

## Related

- [`AI_REFACTORING_PLAN.md`](../AI_REFACTORING_PLAN.md) — refactoring plan
  and implementation status for this package
- [`examples/`](../examples/) — example applications
