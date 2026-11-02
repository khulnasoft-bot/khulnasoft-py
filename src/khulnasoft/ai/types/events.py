"""Base event types for model streaming.

Contains :class:`BaseEvent`, :class:`ModelEvent` and its subclasses
(``StreamStart``, ``TextDelta``, ``ToolEnd``, ...), the ``Event`` union,
and the pydantic serialization helpers used when events cross the
wire/durable-execution border.
"""

from __future__ import annotations

import contextvars
from typing import Annotated, Any, Literal

import pydantic

from . import messages, usage as usage_

# we're using pydantic because events are crossing
# serialization border in the case of durable execution

# Placeholder so ModelEvent.message is typed as Message (not Message | None).
# Stream.__anext__ stamps the real in-progress message before yielding,
# so consumers never see this value.
_DUMMY_MESSAGE = messages.Message(id="<unset>", role="assistant", parts=[])

# Pydantic doesn't let an Annotated serializer add to the serialization
# context, so OmitEventMessages uses a ContextVar instead.
_omit_event_messages: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "ai_omit_event_messages", default=False
)


class BaseEvent(pydantic.BaseModel):
    """Anything ``ai.stream`` or ``Agent.run`` yields.

    ``replay`` is set on synthetic events emitted when ``models.stream``
    short-circuits an existing assistant turn (resume-after-approval
    flows).  ``Agent.run`` drops replay-flagged events from the consumer-
    facing stream — the loop's tool dispatcher still consumes them
    internally.  Excluded from JSON: it's a control flag, not data.
    """

    replay: bool = pydantic.Field(default=False, exclude=True, repr=False)

    model_config = pydantic.ConfigDict(frozen=True)


def _serialize_omitting_event_messages(
    value: Any,
    handler: pydantic.SerializerFunctionWrapHandler,
) -> Any:
    token = _omit_event_messages.set(True)
    try:
        return handler(value)
    finally:
        _omit_event_messages.reset(token)


OmitEventMessages = Annotated[Any, pydantic.WrapSerializer(_serialize_omitting_event_messages)]


def _validate_event_message(value: Any) -> Any:
    if isinstance(value, dict) and set(value) == {"id"}:
        return {**value, "role": "assistant", "parts": []}
    return value


def _serialize_event_message(
    value: messages.Message,
    handler: pydantic.SerializerFunctionWrapHandler,
) -> Any:
    if _omit_event_messages.get():
        return {"id": value.id}
    return handler(value)


_EventMessage = Annotated[
    messages.Message,
    pydantic.BeforeValidator(_validate_event_message),
    pydantic.WrapSerializer(_serialize_event_message),
]


class ModelEvent(BaseEvent):
    """Streamed out of a model request (``ai.stream``).

    ``message`` carries the in-progress (or final) assistant message; the
    streaming layer aggregates parts into it as deltas arrive and stamps
    a reference onto each yielded event (``Stream.__anext__``). ``usage``
    carries the latest usage value reported by the provider (latest-wins
    across the stream).
    """

    message: _EventMessage = _DUMMY_MESSAGE
    usage: usage_.Usage | None = None
    provider_metadata: dict[str, Any] | None = None


class StreamStart(ModelEvent):
    kind: Literal["stream_start"] = "stream_start"


class StreamEnd(ModelEvent):
    """End of a model response.

    ``finish_reason`` is why the model stopped.  The framework adopts
    the OpenTelemetry gen_ai finish-reason vocabulary as its own:
    ``stop``, ``length``, ``content_filter``, ``tool_call``, ``error``,
    plus ``other`` as a catch-all.  Provider adapters normalize their
    native stop reasons into it; a provider value with no equivalent
    becomes ``other`` with the raw value kept in ``provider_metadata``.

    ``response_id``/``response_model`` identify the provider response —
    ``response_model`` can differ from the requested model under
    gateway routing or fallbacks.  All are ``None`` when the provider
    doesn't report them.
    """

    kind: Literal["stream_end"] = "stream_end"
    finish_reason: str | None = None
    response_id: str | None = None
    response_model: str | None = None


class TextStart(ModelEvent):
    block_id: str = ""

    kind: Literal["text_start"] = "text_start"


class TextDelta(ModelEvent):
    chunk: str
    block_id: str = ""

    kind: Literal["text_delta"] = "text_delta"


class TextEnd(ModelEvent):
    block_id: str = ""

    kind: Literal["text_end"] = "text_end"


class ReasoningStart(ModelEvent):
    block_id: str = ""

    kind: Literal["reasoning_start"] = "reasoning_start"


class ReasoningDelta(ModelEvent):
    chunk: str
    block_id: str = ""

    kind: Literal["reasoning_delta"] = "reasoning_delta"


class ReasoningEnd(ModelEvent):
    block_id: str = ""

    kind: Literal["reasoning_end"] = "reasoning_end"


class ToolStart(ModelEvent):
    tool_call_id: str = ""
    tool_name: str = ""

    kind: Literal["tool_start"] = "tool_start"


class ToolDelta(ModelEvent):
    chunk: str
    tool_call_id: str = ""

    kind: Literal["tool_delta"] = "tool_delta"


class ToolEnd(ModelEvent):
    tool_call: messages.ToolCallPart
    tool_call_id: str = ""

    kind: Literal["tool_end"] = "tool_end"


class BuiltinToolStart(ModelEvent):
    tool_call_id: str = ""
    tool_name: str = ""

    kind: Literal["builtin_tool_start"] = "builtin_tool_start"


class BuiltinToolDelta(ModelEvent):
    chunk: str
    tool_call_id: str = ""

    kind: Literal["builtin_tool_delta"] = "builtin_tool_delta"


class BuiltinToolEnd(ModelEvent):
    tool_call: messages.BuiltinToolCallPart
    tool_call_id: str = ""

    kind: Literal["builtin_tool_end"] = "builtin_tool_end"


class BuiltinToolResult(ModelEvent):
    """Provider returned a result for a built-in tool call."""

    result: messages.BuiltinToolReturnPart
    tool_call_id: str = ""

    kind: Literal["builtin_tool_result"] = "builtin_tool_result"


class FileEvent(ModelEvent):
    """A complete generated file from the LLM."""

    block_id: str = ""
    media_type: str
    data: str | bytes
    filename: str | None = None

    kind: Literal["file"] = "file"


Event = (
    StreamStart
    | StreamEnd
    | TextStart
    | TextDelta
    | TextEnd
    | ReasoningStart
    | ReasoningDelta
    | ReasoningEnd
    | ToolStart
    | ToolDelta
    | ToolEnd
    | BuiltinToolStart
    | BuiltinToolDelta
    | BuiltinToolEnd
    | BuiltinToolResult
    | FileEvent
)
