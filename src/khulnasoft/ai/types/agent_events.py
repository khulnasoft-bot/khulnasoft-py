"""Agent-layer event types.

Extends the model-streaming ``Event`` vocabulary from :mod:`khulnasoft.ai.types.events`
with events that originate in the agent runtime: tool-execution outcomes,
hook suspension points, run blocked/retry signals.
"""

from __future__ import annotations

import abc
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    Callable,
    Mapping,
    Sequence,
)
from typing import Annotated, Any, Literal, cast

import pydantic

from . import messages
from .events import (
    BaseEvent,
    BuiltinToolDelta,
    BuiltinToolEnd,
    BuiltinToolStart,
    Event,
    StreamEnd,
    StreamStart,
    ToolDelta,
    ToolEnd,
    ToolStart,
)


class Aggregator[Item, Result, ModelInput]:
    @abc.abstractmethod
    def feed(self, item: Item) -> None: ...

    @abc.abstractmethod
    def snapshot(self) -> Result: ...

    def get_model_input(self) -> ModelInput:
        """Return the model-facing value derived from this aggregator's state.

        Default implementation defers to :meth:`to_model_input`; subclasses
        with non-trivial state may override either or both.
        """
        return type(self).to_model_input(self.snapshot())

    @classmethod
    @abc.abstractmethod
    def to_model_input(cls, snapshot: Result) -> ModelInput:
        """Stateless conversion: snapshot -> model-facing value.

        Called on inbound (when a tool result round-trips back from the
        wire) and anywhere else a snapshot needs to be re-derived
        without a live aggregator instance.
        """
        ...


class PartialToolCallResult(BaseEvent):
    """Emitted when tool calls or other yield_from callers yield values."""

    tool_call_id: str | None = None
    tool_name: str | None = None
    label: object = None
    value: Any = None

    def key(self) -> object:
        return (self.tool_call_id, self.label)

    aggregator_factory: Callable[[], Aggregator[Any, Any, Any]] | None = pydantic.Field(
        default=None, exclude=True, repr=False
    )

    kind: Literal["partial_tool_call_result"] = "partial_tool_call_result"


class ToolCallResult(BaseEvent):
    """Emitted after tool calls execute — carries the result message.

    When the framework auto-catches an exception raised by the tool,
    ``exception`` carries the real ``BaseException`` (with traceback /
    ``__cause__`` intact) so loops can log it richly.  The wire-bound
    ``ToolResultPart.result`` still has ``str(exc)`` for the LLM.
    The ``exception`` field is excluded from serialization.
    """

    message: messages.Message
    results: Sequence[messages.ToolResultPart]
    exception: BaseException | None = pydantic.Field(default=None, exclude=True, repr=False)

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    kind: Literal["tool_call_result"] = "tool_call_result"


def _get(obj: Any, key: Any) -> Any | None:
    return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)


class HookEvent(BaseEvent):
    """Emitted when a hook suspends, resolves, or is cancelled.

    Every instance is one of the per-status subclasses —
    :class:`PendingHookEvent`, :class:`ResolvedHookEvent`, or
    :class:`CancelledHookEvent` — matching ``hook.status``.  Construct
    via :meth:`for_hook` (or a subclass directly); the base class
    cannot be instantiated, and validating against it dispatches to
    the matching subclass.
    """

    message: messages.Message
    hook: messages.HookPart[Any]

    kind: Literal["hook"] = "hook"

    def __init__(self, /, **data: Any) -> None:
        if type(self) is HookEvent:
            raise TypeError(
                "HookEvent cannot be instantiated directly; use "
                "HookEvent.for_hook() or a per-status subclass"
            )
        super().__init__(**data)

    @classmethod
    def for_hook(cls, message: messages.Message, hook: messages.HookPart[Any]) -> HookEvent:
        """Construct the per-status subclass matching ``hook.status``."""
        return _HOOK_EVENTS[hook.status](message=message, hook=hook)

    @pydantic.model_validator(mode="wrap")
    @classmethod
    def _dispatch_status(
        cls, value: Any, handler: pydantic.ValidatorFunctionWrapHandler
    ) -> HookEvent:
        if cls is not HookEvent or not isinstance(value, Mapping):
            return cast("HookEvent", handler(value))
        hook = _get(value, "hook")
        status = _get(hook, "status") if hook is not None else None
        # On an invalid status, we validate against PendingHookEvent, but
        # pydantic will report the missing fields.
        sub = _HOOK_EVENTS.get(status, PendingHookEvent)
        return sub.model_validate(value)

    @pydantic.model_validator(mode="after")
    def _check_status(self) -> HookEvent:
        if not isinstance(self, _HOOK_EVENTS[self.hook.status]):
            raise ValueError(f"{type(self).__name__} cannot carry a {self.hook.status!r} hook")
        return self


class PendingHookEvent(HookEvent):
    """The hook suspended; the run needs its resolution to proceed."""


class ResolvedHookEvent(HookEvent):
    """The hook resolved; ``hook.resolution`` carries the value."""


class CancelledHookEvent(HookEvent):
    """The hook was cancelled without a resolution."""


_HOOK_EVENTS: dict[object, type[HookEvent]] = {
    "pending": PendingHookEvent,
    "resolved": ResolvedHookEvent,
    "cancelled": CancelledHookEvent,
}


class RunBlocked(BaseEvent):
    """The run is blocked on hooks.

    Emitted when the run stops being able to make progress without
    external input: at least one hook is deferred, no model stream is
    producing events, and every in-flight tool call is suspended
    awaiting a hook.  Streaming consumers can use this to surface
    "waiting for approval" state without reconstructing it from
    tool/hook events.

    ``hooks`` is a snapshot of the deferred hooks the run is blocked on.

    There is no mirror "unblocked" event because it would be redundant:
    a blocked run can only resume via a hook resolution (or
    cancellation), so the next :class:`ResolvedHookEvent` or
    :class:`CancelledHookEvent` *is* the unblock signal.  Note the
    converse does not hold — a ``ToolCallResult`` carrying an
    ``is_hook_deferred`` placeholder (serverless abort) arrives while
    the run stays blocked, and the run then ends still blocked.
    """

    hooks: tuple[messages.HookPart[Any], ...] = ()

    kind: Literal["run_blocked"] = "run_blocked"


class Retry(BaseEvent):
    """The in-progress model response is discarded and will be re-streamed.

    Everything since the most recent ``StreamStart`` -- the in-progress
    assistant message and any tool results for it -- is invalidated; a
    fresh ``StreamStart`` follows.

    Nothing in the library emits this yet.  It is for custom loops that
    retry a model call after it already produced events (e.g. a durable
    step that failed mid-stream); ``MessageHydrator``, ``RunStateTracker``
    and the AI SDK UI adapter all handle it.  Loops emitting it should
    call ``ToolRunner.discard_all()`` to cancel tools scheduled for the
    discarded response.
    """

    kind: Literal["retry"] = "retry"


AgentEvent = Annotated[
    Event | ToolCallResult | HookEvent | PartialToolCallResult | RunBlocked | Retry,
    pydantic.Field(discriminator="kind"),
]


class _RetryFilter:
    """Spot tool output for tool calls that a :class:`Retry` discarded.

    In a distributed setup, a tool scheduled for a response that later
    gets retried can still deliver its result (or a partial result, or
    a hook event) after the ``Retry``.  Feed every event in order;
    :meth:`feed` returns False for such leftovers.  A tool call id that
    the retried response reuses counts as live again.
    """

    def __init__(self) -> None:
        self._response: set[str] = set()
        self._discarded: set[str] = set()

    def feed(self, event: BaseEvent) -> bool:
        match event:
            case StreamStart():
                self._response = set()
            case (
                ToolStart(tool_call_id=id)
                | ToolDelta(tool_call_id=id)
                | ToolEnd(tool_call_id=id)
                | BuiltinToolStart(tool_call_id=id)
                | BuiltinToolDelta(tool_call_id=id)
                | BuiltinToolEnd(tool_call_id=id)
            ):
                self._response.add(id)
                self._discarded.discard(id)
            case StreamEnd():
                ids = {tc.tool_call_id for tc in event.message.tool_calls}
                self._response |= ids
                self._discarded -= ids
            case Retry():
                self._discarded |= self._response
                self._response = set()
            case ToolCallResult():
                return not event.results or not all(
                    r.tool_call_id in self._discarded for r in event.results
                )
            case PartialToolCallResult():
                return event.tool_call_id not in self._discarded
            case HookEvent():
                return event.hook.tool_call_id not in self._discarded
        return True


async def drop_discarded[E: BaseEvent](
    events: AsyncIterable[E],
) -> AsyncGenerator[E]:
    """Yield ``events`` minus late tool output for calls a ``Retry`` discarded.

    In a distributed setup, a tool scheduled for a response that later
    gets retried can still deliver its result (or a partial result, or
    a hook event) after the ``Retry``.  A tool call id that the retried
    response reuses counts as live again.
    """
    retry_filter = _RetryFilter()
    async for event in events:
        if retry_filter.feed(event):
            yield event


class RunStateTracker:
    """Fold an agent event stream into run state (blocked-on-hooks).

    A pure function of the event stream: feed every event in order and
    :meth:`feed` returns a :class:`RunBlocked` event whenever the run
    becomes blocked, else None (:attr:`blocked` flips back silently —
    see :class:`RunBlocked` for why no mirror event exists).  Works
    identically over a live run or a serialized replay of one.

    The fold reads three things:

    * hook state from :class:`HookEvent` (:class:`PendingHookEvent`
      adds, :class:`ResolvedHookEvent` / :class:`CancelledHookEvent`
      remove);
    * model-stream activity from :class:`StreamStart` / :class:`StreamEnd`;
    * in-flight tool calls from the assistant message on
      :class:`StreamEnd` (scheduled) and :class:`ToolCallResult`
      (settled), matched by ``tool_call_id``.

    The run is blocked when at least one hook is deferred, a model stream
    has ended, no stream is producing, and every in-flight tool call is
    accounted for by a deferred hook's ``tool_call_id``.  Consequently the
    signal is only as good as the stream: loops must yield their
    ``StreamEnd`` (with the assistant message) for tool calls to be
    counted, and custom gating must pass ``tool_call_id=`` to
    ``ai.hook()`` — an unattributed hook while tools are in flight reads
    as "still busy" and suppresses the signal.
    """

    def __init__(self) -> None:
        self._deferred: dict[str, messages.HookPart[Any]] = {}
        self._in_flight: set[str] = set()
        self._last_scheduled: set[str] = set()
        self._streaming = 0
        self._stream_ended = False
        self._blocked = False
        self._retry_filter = _RetryFilter()

    @property
    def blocked(self) -> bool:
        return self._blocked

    @property
    def deferred_hooks(self) -> list[messages.HookPart[Any]]:
        return list(self._deferred.values())

    def feed(self, event: AgentEvent) -> RunBlocked | None:
        if not self._retry_filter.feed(event):
            return None
        match event:
            case StreamStart():
                self._streaming += 1
                self._stream_ended = False
                self._last_scheduled = set()
            case StreamEnd():
                # Loops may emit a bare StreamEnd without a StreamStart
                # (e.g. when the model was streamed out-of-band), so
                # clamp at zero.
                self._streaming = max(0, self._streaming - 1)
                self._stream_ended = True
                self._last_scheduled = {tc.tool_call_id for tc in event.message.tool_calls}
                self._in_flight |= self._last_scheduled
            case Retry():
                # Undo the discarded response's StreamStart and any tool
                # calls its StreamEnd scheduled (none once a new stream
                # has started).
                self._streaming = max(0, self._streaming - 1)
                self._stream_ended = False
                self._in_flight -= self._last_scheduled
                self._last_scheduled = set()
            case ToolCallResult():
                self._in_flight.difference_update(r.tool_call_id for r in event.results)
            case PendingHookEvent():
                self._deferred[event.hook.hook_id] = event.hook
            case HookEvent():
                self._deferred.pop(event.hook.hook_id, None)
            case _:
                return None

        attributed = {h.tool_call_id for h in self._deferred.values() if h.tool_call_id is not None}
        now = (
            self._stream_ended
            and bool(self._deferred)
            and not self._streaming
            and self._in_flight <= attributed
        )
        if now == self._blocked:
            return None
        self._blocked = now
        if not now:
            return None
        return RunBlocked(hooks=tuple(self._deferred.values()))
