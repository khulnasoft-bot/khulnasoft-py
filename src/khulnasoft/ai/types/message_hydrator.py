"""Reconstruct messages from a sequential agent event stream.

Contains :class:`MessageHydrator` and :func:`_replay_message_events`.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from . import messages
from .agent_events import (
    BaseEvent,
    HookEvent,
    Retry,
    ToolCallResult,
    _RetryFilter,
)
from .events import (
    BuiltinToolDelta,
    BuiltinToolEnd,
    BuiltinToolResult,
    BuiltinToolStart,
    Event,
    FileEvent,
    ModelEvent,
    ReasoningDelta,
    ReasoningEnd,
    ReasoningStart,
    StreamEnd,
    StreamStart,
    TextDelta,
    TextEnd,
    TextStart,
    ToolDelta,
    ToolEnd,
    ToolStart,
)


class MessageHydrator:
    """Reconstruct messages from a sequential agent event stream."""

    def __init__(self, seed_message: messages.Message | None = None) -> None:
        self._seed_message = seed_message
        self.message = seed_message or messages.Message(role="assistant", parts=[])
        # messages/messages_by_id stay empty until events are
        # actually fed in
        self.messages: list[messages.Message] = []
        self.messages_by_id: dict[str, messages.Message] = {}
        self._parts_by_message_id: dict[str, dict[str, messages.Part]] = {}
        self._streaming_index: int | None = None
        self._retry_filter = _RetryFilter()
        self._message_selected = seed_message is not None
        self._seed_checked = False
        # A stream that exhausts without StreamEnd died mid-response.
        self.ended = False
        self.finish_reason: str | None = None
        self.response_id: str | None = None
        self.response_model: str | None = None

    def feed[T: BaseEvent](self, event: T) -> T:
        if not self._retry_filter.feed(event):
            return event
        # ToolCallResult and HookEvent always carry full messages, so we just
        # use them.
        if isinstance(event, ToolCallResult | HookEvent):
            self.message = event.message
            existing = self.messages_by_id.get(event.message.id)
            if existing is None:
                self.messages.append(event.message)
            elif existing is not event.message:
                self.messages[self.messages.index(existing)] = event.message
            self.messages_by_id[event.message.id] = event.message
            return event
        if isinstance(event, Retry):
            # Drop the in-progress model response and everything after
            # it (tool results, hook messages); the retried stream
            # rebuilds them, under the same or a new id.
            if self._streaming_index is None:
                return event
            stale = self.messages[self._streaming_index :]
            for msg in stale:
                del self.messages_by_id[msg.id]
                self._parts_by_message_id.pop(msg.id, None)
            del self.messages[self._streaming_index :]
            self._streaming_index = None
            self.message = messages.Message(id=stale[0].id, role="assistant", parts=[])
            self.ended = False
            self.finish_reason = None
            self.response_id = None
            self.response_model = None
            return event
        if not isinstance(event, ModelEvent):
            return event

        updates: dict[str, Any] = {}
        message_id = event.message.id
        if message_id != "<unset>":
            if self._seed_message is not None and not self._seed_checked:
                self._seed_checked = True
                if message_id != self.message.id:
                    raise ValueError(
                        "seed message id does not match event message id: "
                        f"{self.message.id!r} != {message_id!r}"
                    )
            if message_id != self.message.id:
                self.ended = False
                if not self._message_selected:
                    self.message.id = message_id
                    self._message_selected = True
                else:
                    self.message = self.messages_by_id.get(message_id) or messages.Message(
                        id=message_id, role="assistant", parts=[]
                    )
        if self.message.id not in self.messages_by_id:
            self.messages.append(self.message)
            self.messages_by_id[self.message.id] = self.message
            self._streaming_index = len(self.messages) - 1
        elif (
            self._streaming_index is None
            or self.messages[self._streaming_index] is not self.message
        ):
            self._streaming_index = self.messages.index(self.message)
        self._parts = self._parts_by_message_id.setdefault(self.message.id, {})

        # Replay events carry no new state — the seeded message already
        # has everything they would have produced.  A replayed turn is
        # complete by construction, so it also counts as ended.
        if event.replay:
            self.ended = True
            return event.model_copy(update={"message": self.message})

        # grab usage from any event that carries one
        if event.usage is not None:
            self.message.usage = event.usage

        match event:
            case TextStart(block_id=bid, provider_metadata=pm):
                tp = messages.TextPart(id=bid, text="", provider_metadata=pm)
                self.message.parts.append(tp)
                self._parts[bid] = tp
            case TextDelta(block_id=bid, chunk=c, provider_metadata=pm):
                existing_text = self._parts.get(bid)
                if isinstance(existing_text, messages.TextPart):
                    existing_text.text += c
                    if pm is not None:
                        existing_text.provider_metadata = pm
            case TextEnd(block_id=bid, provider_metadata=pm):
                existing_text = self._parts.get(bid)
                if isinstance(existing_text, messages.TextPart) and pm is not None:
                    existing_text.provider_metadata = pm
            case ReasoningStart(block_id=bid, provider_metadata=pm):
                rp = messages.ReasoningPart(id=bid, text="", provider_metadata=pm)
                self.message.parts.append(rp)
                self._parts[bid] = rp
            case ReasoningDelta(block_id=bid, chunk=c, provider_metadata=pm):
                existing_reasoning = self._parts.get(bid)
                if isinstance(existing_reasoning, messages.ReasoningPart):
                    existing_reasoning.text += c
                    if pm is not None:
                        existing_reasoning.provider_metadata = pm
            case ReasoningEnd(block_id=bid, provider_metadata=pm):
                existing_reasoning = self._parts.get(bid)
                if isinstance(existing_reasoning, messages.ReasoningPart) and pm is not None:
                    existing_reasoning.provider_metadata = pm
            case ToolStart(tool_call_id=tcid, tool_name=name, provider_metadata=pm):
                tcp = messages.ToolCallPart(
                    id=tcid,
                    tool_call_id=tcid,
                    tool_name=name,
                    tool_args="",
                    provider_metadata=pm,
                )
                self.message.parts.append(tcp)
                self._parts[tcid] = tcp
            case ToolDelta(tool_call_id=tcid, chunk=c, provider_metadata=pm):
                existing_tool = self._parts.get(tcid)
                if isinstance(existing_tool, messages.ToolCallPart):
                    existing_tool.tool_args += c
                    if pm is not None:
                        existing_tool.provider_metadata = pm

            case ToolEnd(tool_call_id=tcid, provider_metadata=pm):
                existing_tool = self._parts.get(tcid)
                if isinstance(existing_tool, messages.ToolCallPart):
                    updates["tool_call"] = existing_tool
                    if pm is not None:
                        existing_tool.provider_metadata = pm
            case BuiltinToolStart(
                tool_call_id=tcid,
                tool_name=name,
                provider_metadata=pm,
            ):
                btcp = messages.BuiltinToolCallPart(
                    id=tcid,
                    tool_call_id=tcid,
                    tool_name=name,
                    tool_args="",
                    provider_metadata=pm,
                )
                self.message.parts.append(btcp)
                self._parts[tcid] = btcp
            case BuiltinToolDelta(tool_call_id=tcid, chunk=c, provider_metadata=pm):
                existing_btc = self._parts.get(tcid)
                if isinstance(existing_btc, messages.BuiltinToolCallPart):
                    existing_btc.tool_args += c
                    if pm is not None:
                        existing_btc.provider_metadata = pm
            case BuiltinToolEnd(tool_call_id=tcid, provider_metadata=pm):
                existing_btc = self._parts.get(tcid)
                if isinstance(existing_btc, messages.BuiltinToolCallPart):
                    updates["tool_call"] = existing_btc
                    if pm is not None:
                        existing_btc.provider_metadata = pm
            case BuiltinToolResult(result=res, provider_metadata=pm):
                if pm is not None:
                    res = res.model_copy(update={"provider_metadata": pm})
                self.message.parts.append(res)
            case FileEvent(
                block_id=bid,
                media_type=mt,
                data=d,
                filename=fname,
                provider_metadata=pm,
            ):
                fp = messages.FilePart(
                    id=bid or messages.generate_id(),
                    data=d,
                    media_type=mt,
                    filename=fname,
                    provider_metadata=pm,
                )
                self.message.parts.append(fp)
                self._parts[fp.id] = fp

            case StreamEnd(
                provider_metadata=pm,
                finish_reason=finish,
                response_id=rid,
                response_model=rmodel,
            ):
                self.ended = True
                self.finish_reason = finish
                self.response_id = rid
                self.response_model = rmodel
                if pm is not None:
                    self.message.provider_metadata = pm
            case _:
                pass

        return event.model_copy(update={"message": self.message, **updates})


async def _replay_message_events(
    msg: messages.Message,
) -> AsyncGenerator[Event]:
    """Synthesize stream events for ``msg``."""
    # See Stream.replay_message
    yield StreamStart()
    for part in msg.parts:
        if isinstance(part, messages.TextPart):
            yield TextStart(block_id=part.id)
            if part.text:
                yield TextDelta(block_id=part.id, chunk=part.text)
            yield TextEnd(block_id=part.id, provider_metadata=part.provider_metadata)
        elif isinstance(part, messages.ReasoningPart):
            yield ReasoningStart(block_id=part.id)
            if part.text:
                yield ReasoningDelta(block_id=part.id, chunk=part.text)
            yield ReasoningEnd(
                block_id=part.id,
                provider_metadata=part.provider_metadata,
            )
        elif isinstance(part, messages.ToolCallPart):
            yield ToolStart(
                tool_call_id=part.tool_call_id,
                tool_name=part.tool_name,
            )
            if part.tool_args:
                yield ToolDelta(
                    tool_call_id=part.tool_call_id,
                    chunk=part.tool_args,
                )
            yield ToolEnd(
                tool_call_id=part.tool_call_id,
                tool_call=part,
                provider_metadata=part.provider_metadata,
            )
        elif isinstance(part, messages.BuiltinToolCallPart):
            yield BuiltinToolStart(
                tool_call_id=part.tool_call_id,
                tool_name=part.tool_name,
            )
            if part.tool_args:
                yield BuiltinToolDelta(
                    tool_call_id=part.tool_call_id,
                    chunk=part.tool_args,
                )
            yield BuiltinToolEnd(
                tool_call_id=part.tool_call_id,
                tool_call=part,
                provider_metadata=part.provider_metadata,
            )
        elif isinstance(part, messages.BuiltinToolReturnPart):
            yield BuiltinToolResult(tool_call_id=part.tool_call_id, result=part)
        elif isinstance(part, messages.FilePart):
            yield FileEvent(
                block_id=part.id,
                data=part.data,
                media_type=part.media_type,
                filename=part.filename,
                provider_metadata=part.provider_metadata,
            )
    yield StreamEnd(provider_metadata=msg.provider_metadata)
