# Key concepts

## Agents

An [`Agent`](src/khulnasoft/ai/agents/agent.py) bundles a model, tools, and a
control loop. It is a configuration object — the actual execution happens
inside `Agent.run()`.

```python
import khulnasoft.ai as ai

agent = ai.Agent(tools=[get_weather, get_population])

async with agent.run(model, messages) as stream:
    async for event in stream:
        # events are ModelEvent, ToolCallResult, HookEvent, ...
        ...
    print(stream.output)  # final assistant text or validated output
```

### Class-level tools

Subclasses can declare fixed tools via `TOOLS`:

```python
class WeatherAgent(ai.Agent):
    TOOLS = [get_weather, get_population]

# instance-level tools are appended to TOOLS
agent = WeatherAgent(tools=[get_forecast])
```

### AgentStream

`agent.run()` returns an async context manager whose value is an
`AgentStream`. It exposes `context` (the live `Context`), `messages`,
`output`, `blocked`, and `deferred_hooks`.

## Tools

`@ai.tool` converts an async function into an executable tool. The function
signature becomes the tool's parameter schema (via pydantic), and its docstring
becomes the description.

```python
@ai.tool
async def edit(path: str, content: str) -> EditResult:
    """Edit the file at ``path`` with ``content``."""
    ...
```

Tools return either:
- a plain value (normal tool), or
- an async generator (streaming tool)

Streaming tools must declare an aggregator, either via `aggregator=` or an
`Aggregate` marker in the return type:

```python
@ai.tool
async def research(topic: str) -> ai.StreamingStatusTool[str]:
    yield "connecting..."
    yield body  # final yield is the tool result
```

The aggregator's `snapshot()` becomes the value stored on
`ToolResultPart.result`; `get_model_input()` becomes what the model sees on
its next turn.

### Approval gating

Tools can require approval:

```python
@ai.tool(require_approval=True)
async def delete_file(path: str) -> None:
    ...
```

When such a tool is called, the run suspends with a
`PendingHookEvent`. Resolve it from outside with `ai.resolve_hook(...)`.

## Events

The framework communicates via typed events. The two vocabularies are:

### Model events (`types/events.py`)

Emitted out of model requests:

| Event | Meaning |
|-------|---------|
| `StreamStart` / `StreamEnd` | Start/end of a model response |
| `TextStart` / `TextDelta` / `TextEnd` | Streaming text |
| `ReasoningStart` / `ReasoningDelta` / `ReasoningEnd` | Reasoning content |
| `ToolStart` / `ToolDelta` / `ToolEnd` | Tool call |
| `BuiltinToolStart` / `BuiltinToolDelta` / `BuiltinToolEnd` / `BuiltinToolResult` | Built-in tool |
| `FileEvent` | Generated file |

### Agent events (`types/agent_events.py`)

Originating in the agent runtime:

| Event | Meaning |
|-------|---------|
| `ToolCallResult` | Tool execution outcome (carries the result message) |
| `HookEvent` (+ `PendingHookEvent`, `ResolvedHookEvent`, `CancelledHookEvent`) | Hook suspension / resolution / cancellation |
| `PartialToolCallResult` | Intermediate value from a streaming tool |
| `RunBlocked` | Run suspended on deferred hooks |
| `Retry` | In-progress response discarded, will be re-streamed |

All agent events carry a `kind` discriminator for pydantic validation.

## Hooks

Hooks are suspension points requiring external input:

```python
# Inside a run (e.g. inside a tool):
approval = await ai.hook(
    "approve_delete",
    payload=ai.types.tools.ToolApproval,
    metadata={"tool": "delete"},
)
if approval.granted:
    ...
```

```python
# From outside the loop:
await ai.resolve_hook("approve_delete", {"granted": True})
```

The `HookRegistry` tracks live suspensions and pre-registered resolutions.
`HookDeferredException` is raised when a hook defers; use
`ai.deferred_tool_result()` to emit a well-formed placeholder.

## Telemetry

`experimental_telemetry` emits spans for runs, turns, model calls, tool
executions, and hooks:

```python
import khulnasoft.ai.experimental_telemetry as telemetry

async with telemetry.span("retrieval") as sp:
    sp.set_attrs(query=q)
    docs = await search(q)
    sp.set_attrs(count=len(docs))
```

Spans are delivered to registered adapters:

```python
telemetry.register(my_adapter)
```

Or collected via a `DictSink` for deferred processing:

```python
from khulnasoft.ai.experimental_telemetry import DictSink, use_sink, push_all

sink = DictSink()
async with use_sink(sink):
    ...  # replayable / suspendable code
payload = [s.model_dump(mode="json") for s in sink.finished_spans]
await push_all(payload)
```

## Context

`Context` carries everything that goes into the LLM: model, messages, tools,
optional output type, and inference params. It is exposed via
`AgentStream.context` and mutated by the agent loop via `context.add(...)`.

Replay-flagged messages (from resume-after-approval) are skipped by
`context.add()` to avoid duplicate turns.
