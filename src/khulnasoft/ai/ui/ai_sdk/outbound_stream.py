"""Live event stream conversion for the AI SDK UI protocol.

Public entry points:

* :func:`to_stream` — convert internal ``AgentEvent``s to UI stream events
* :func:`to_sse` — convert to SSE strings
* :func:`serialize_event` — serialize a UI stream event to JSON
* :func:`format_sse` / :func:`format_done_sse` — SSE formatting helpers
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

import pydantic

from ...types import agent_events as agent_events_
from . import ui_events
from .outbound_state import _StreamState


def _to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _json_default(obj: Any) -> Any:
    if isinstance(obj, pydantic.BaseModel):
        return obj.model_dump(mode="json", by_alias=True)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def serialize_event(event: ui_events.UIMessageStreamEvent) -> str:
    """Serialize a stream event to JSON with camelCase keys."""
    d = dataclasses.asdict(event)
    if isinstance(event, ui_events.UIDataEvent):
        d["type"] = event.type
        del d["data_type"]
    camel_dict = {_to_camel_case(k): v for k, v in d.items() if v is not None}
    return json.dumps(camel_dict, default=_json_default)


def format_sse(event: ui_events.UIMessageStreamEvent) -> str:
    """Format a stream event as an SSE data line."""
    return f"data: {serialize_event(event)}\n\n"


def format_done_sse() -> str:
    """Format the AI SDK UI stream termination marker."""
    return "data: [DONE]\n\n"


async def to_stream(
    events: AsyncIterable[agent_events_.AgentEvent],
) -> AsyncGenerator[ui_events.UIMessageStreamEvent]:
    """Walk internal events once, emitting AI SDK UI stream events."""
    state = _StreamState()
    # The client drops a discarded step's tool parts on reset-step, so
    # any later output for those tool calls would make it error out.
    retry_filter = agent_events_._RetryFilter()

    async for event in events:
        if not retry_filter.feed(event):
            continue
        match event:
            case agent_events_.ToolCallResult():
                for ui_event in state.on_tool_result(event):
                    yield ui_event
            case agent_events_.PartialToolCallResult():
                for ui_event in state.on_partial_tool_result(event):
                    yield ui_event
            case agent_events_.HookEvent():
                for ui_event in state.on_hook(event):
                    yield ui_event
            case agent_events_.RunBlocked():
                # No AI SDK UI equivalent; hook parts already carry the
                # deferred-approval state the UI renders.
                pass
            case agent_events_.Retry():
                for ui_event in state.on_retry():
                    yield ui_event
            case _:
                for ui_event in state.on_event(event):
                    yield ui_event

    for ui_event in state.finish():
        yield ui_event


async def to_sse(
    events: AsyncIterable[agent_events_.AgentEvent],
) -> AsyncGenerator[str]:
    """Convert an internal event stream into SSE strings."""
    async for event in to_stream(events):
        yield format_sse(event)
    yield format_done_sse()
