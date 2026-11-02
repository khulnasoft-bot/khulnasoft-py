# Module structure

This page breaks down every module in `src/khulnasoft/ai/` and its
responsibilities.

## Package root

| Module | Purpose |
|--------|---------|
| [`__init__.py`](src/khulnasoft/ai/__init__.py) | Public API surface: re-exports agents, models, types, providers, ops, ui, util, durable, errors, experimental_telemetry, testing |
| [`errors.py`](src/khulnasoft/ai/errors.py) | Error hierarchy (`AIError`, `ProviderError`, `ConfigurationError`, ...) |
| [`type_utils.py`](src/khulnasoft/ai/type_utils.py) | Type variable binding, resolution, and replacement helpers |
| [`util.py`](src/khulnasoft/ai/util.py) | Utilities (`TaskGroup`, `MultiWaiter`, `merge`, `decouple`, `OrderedSet`) |
| [`durable.py`](src/khulnasoft/ai/durable.py) | Durable execution helpers (`DurableAgent`, `Streamer`) |
| [`testing.py`](src/khulnasoft/ai/testing.py) | Test utilities (`FakeModel`, scripted conversations) |

## `agents/` — Agent runtime

| Module | Purpose |
|--------|---------|
| [`agent.py`](src/khulnasoft/ai/agents/agent.py) | Core runtime: `Agent`, `AgentStream`, `Context`, `current_agent`, `current_tool_call` |
| [`agent_tools.py`](src/khulnasoft/ai/agents/agent_tools.py) | Tool system: `tool()`, `AgentTool`, `ToolResolver`, `ToolRunner`, `BoundToolCall`, `GatedToolCall`, aggregators (`SimpleAggregator`, `ConcatAggregator`, `LastAggregator`, `MessageAggregator`, `Aggregate`), streaming type aliases (`StreamingStatusTool`, `SubAgentTool`, `StreamingTextTool`), type-resolution helpers |
| [`agent_streaming.py`](src/khulnasoft/ai/agents/agent_streaming.py) | Streaming internals: `yield_from`, `_aggregate_from`, `_process_interrupted_hooks` |
| [`hooks.py`](src/khulnasoft/ai/agents/hooks.py) | Hooks registry and resolution: `HookRegistry`, `hook`, `resolve_hook`, `cancel_hook`, `defer_hook`, `get_hook_registry` |
| [`runtime.py`](src/khulnasoft/ai/agents/runtime.py) | Event sink connecting producer coroutines to the consumer |
| [`mcp/`](src/khulnasoft/ai/agents/mcp/) | MCP client integration |

## `types/` — Event and message definitions

| Module | Purpose |
|--------|---------|
| [`events.py`](src/khulnasoft/ai/types/events.py) | Base model-streaming events: `BaseEvent`, `ModelEvent`, `Event` union, serialization helpers (`OmitEventMessages`, `_EventMessage`) |
| [`agent_events.py`](src/khulnasoft/ai/types/agent_events.py) | Agent-layer events: `Aggregator`, `ToolCallResult`, `HookEvent` (+ `PendingHookEvent`, `ResolvedHookEvent`, `CancelledHookEvent`), `RunBlocked`, `Retry`, `AgentEvent` union, `_RetryFilter`, `drop_discarded`, `RunStateTracker` |
| [`message_hydrator.py`](src/khulnasoft/ai/types/message_hydrator.py) | `MessageHydrator` (reconstruct messages from event streams) and `_replay_message_events` |
| [`messages.py`](src/khulnasoft/ai/types/messages.py) | `Message`, `Part`, `TextPart`, `FilePart`, `ReasoningPart`, `ToolCallPart`, `ToolResultPart`, `ContentOutput`, `MessageBundle`, `HookPart`, `RandomSource` |
| [`builders.py`](src/khulnasoft/ai/types/builders.py) | Message construction helpers: `message`, `user_message`, `system_message`, `assistant_message`, `tool_message`, `text_part`, `file_part`, `content_output`, `tool_result_part`, `thinking` |
| [`media.py`](src/khulnasoft/ai/types/media.py) | Media part types |
| [`tools.py`](src/khulnasoft/ai/types/tools.py) | `Tool`, `ToolSpec`, `ToolApproval` declarations |
| [`usage.py`](src/khulnasoft/ai/types/usage.py) | Token usage tracking |

## `models/` — Model selection and inference

| Module | Purpose |
|--------|---------|
| [`models/core/api.py`](src/khulnasoft/ai/models/core/api.py) | Core model API: `stream`, `generate`, `probe`, `Stream` class |
| [`models/core/model.py`](src/khulnasoft/ai/models/core/model.py) | `Model` class and model resolution |
| [`models/core/params.py`](src/khulnasoft/ai/models/core/params.py) | Inference params: `InferenceRequestParams`, sampler params (`TemperatureSamplerParams`, `TopPSamplerParams`, ...), routing params |

## `ops/` — Model operations

| Module | Purpose |
|--------|---------|
| [`ops/audio.py`](src/khulnasoft/ai/ops/audio.py) | Audio generation |
| [`ops/embeddings.py`](src/khulnasoft/ai/ops/embeddings.py) | Embeddings |
| [`ops/images.py`](src/khulnasoft/ai/ops/images.py) | Image generation |
| [`ops/items.py`](src/khulnasoft/ai/ops/items.py) | `Item[T]` result container |
| [`ops/reranking.py`](src/khulnasoft/ai/ops/reranking.py) | Reranking |
| [`ops/transcriptions.py`](src/khulnasoft/ai/ops/transcriptions.py) | Transcription |
| [`ops/videos.py`](src/khulnasoft/ai/ops/videos.py) | Video generation |
| [`ops/experimental/evaluation.py`](src/khulnasoft/ai/ops/experimental/evaluation.py) | Typed evaluation (experimental) |

## `providers/` — Provider implementations

| Module | Purpose |
|--------|---------|
| [`providers/base.py`](src/khulnasoft/ai/providers/base.py) | `Provider`, `ProviderProtocol`, `get_provider` |
| [`providers/_protocol_common.py`](src/khulnasoft/ai/providers/_protocol_common.py) | Shared protocol conversion utilities (`is_default`, `not_default`, `seed_value`, `filter_extra_headers`, `tool_ref_name`) |
| [`providers/history_utils.py`](src/khulnasoft/ai/providers/history_utils.py) | History normalization utilities |
| [`providers/openai/`](src/khulnasoft/ai/providers/openai/) | OpenAI-compatible provider |
| [`providers/anthropic/`](src/khulnasoft/ai/providers/anthropic/) | Anthropic-compatible provider |
| [`providers/ai_gateway/`](src/khulnasoft/ai/providers/ai_gateway/) | AI Gateway provider (v3, v4 protocols) |
| [`providers/typesafe/`](src/khulnasoft/ai/providers/typesafe/) | TypeSafe provider |

## `experimental_telemetry/` — Spans, sinks, adapters

| Module | Purpose |
|--------|---------|
| [`span.py`](src/khulnasoft/ai/experimental_telemetry/span.py) | `Span`, `SpanEvent`, `SpanError`, `current_span`, `use_span`, `create_span`, `span` context manager |
| [`span_data.py`](src/khulnasoft/ai/experimental_telemetry/span_data.py) | Span data types (`RunSpanData`, `AiStreamSpanData`, `AiGenerateSpanData`, `ToolExecutionSpanData`, `HookSpanData`, `CustomSpanData`, ...), span event name constants |
| [`clock.py`](src/khulnasoft/ai/experimental_telemetry/clock.py) | Ambient span clock (`now_ns`, `use_time`) |
| [`sink.py`](src/khulnasoft/ai/experimental_telemetry/sink.py) | Span sinks (`Sink`, `DictSink`, `RegistrySink`, `use_sink`, `push_all`) |
| [`adapters.py`](src/khulnasoft/ai/experimental_telemetry/adapters.py) | Adapter registry (`register`, `unregister`, `is_enabled`, `AdapterProtocol`, `AdapterMixin`, `adapter` decorator) |
| [`otel.py`](src/khulnasoft/ai/experimental_telemetry/otel.py) | OpenTelemetry adapter |
| [`utils/`](src/khulnasoft/ai/experimental_telemetry/utils/) | Console adapter, span viewer |

## `ui/` — AI SDK UI protocol adaptation

| Module | Purpose |
|--------|---------|
| [`ui/ai_sdk/outbound_stream.py`](src/khulnasoft/ai/ui/ai_sdk/outbound_stream.py) | Public entry points: `to_stream`, `to_sse`, `serialize_event`, `format_sse`, `format_done_sse` |
| [`ui/ai_sdk/outbound_state.py`](src/khulnasoft/ai/ui/ai_sdk/outbound_state.py) | `_StreamState`: single-pass state machine converting internal events to AI SDK UI stream events |
| [`ui/ai_sdk/outbound_messages.py`](src/khulnasoft/ai/ui/ai_sdk/outbound_messages.py) | `to_ui_messages`, `bundle_to_wire_output` |
| [`ui/ai_sdk/inbound_messages.py`](src/khulnasoft/ai/ui/ai_sdk/inbound_messages.py) | `to_messages` (inbound UI messages → internal messages) |
| [`ui/ai_sdk/approvals.py`](src/khulnasoft/ai/ui/ai_sdk/approvals.py) | Approval hook helpers |
| [`ui/ai_sdk/ui_events.py`](src/khulnasoft/ai/ui/ai_sdk/ui_events.py) | UI stream event types (`UIMessageStreamEvent`, `UITextStartEvent`, `UIToolOutputAvailableEvent`, ...) |
| [`ui/ai_sdk/ui_messages.py`](src/khulnasoft/ai/ui/ai_sdk/ui_messages.py) | `UIMessage` |
| [`ui/ai_sdk/id_utils.py`](src/khulnasoft/ai/ui/ai_sdk/id_utils.py) | ID generation utilities |
| [`ui/ai_sdk/tool_utils.py`](src/khulnasoft/ai/ui/ai_sdk/tool_utils.py) | `normalize_tool_input` |

## Directory sizes

The refactor split the largest modules:

| Before | LOC | After (combined) | LOC |
|--------|-----|------------------|-----|
| `agents/agent.py` | 1,697 | `agent.py` + `agent_tools.py` + `agent_streaming.py` | ~1,790 |
| `types/events.py` | 916 | `events.py` + `agent_events.py` + `message_hydrator.py` | ~1,000 |
| `experimental_telemetry/span.py` | 1,215 | `span.py` + `span_data.py` + `clock.py` + `sink.py` + `adapters.py` | ~1,380 |
| `ui/ai_sdk/outbound_stream.py` | 677 | `outbound_stream.py` + `outbound_state.py` | ~680 |

Line counts grow slightly because docstrings and type annotations are
preserved across the split; the benefit is separation of concerns, not
line reduction.
