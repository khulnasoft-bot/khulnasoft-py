"""Agent, Context, StreamResult, and the stream() function."""

from __future__ import annotations

import contextlib
import contextvars
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Sequence,
)
from contextlib import AbstractAsyncContextManager
from typing import (
    Any,
    ClassVar,
    Generic,
    Self,
    cast,
    overload,
)

import pydantic
from typing_extensions import TypeVar

from .. import experimental_telemetry as telemetry, models, types, util
from ..types import agent_events as agent_events_, events as events_
from . import hooks as hooks_, runtime
from .agent_streaming import _process_interrupted_hooks, yield_from
from .agent_tools import (
    AgentTool,
    Tool,
    ToolCall,
    ToolCallCallable,
    ToolResolver,
    ToolRunner,
    _populate_model_inputs,
    current_tool_call,
)

# Re-export the public surface from this module so existing
# ``from khulnasoft.ai.agents.agent import X`` imports keep working.
__all__ = [
    "Agent",
    "AgentOutputT",
    "AgentStream",
    "Context",
    "Tool",
    "ToolCall",
    "ToolCallCallable",
    "ToolResolver",
    "ToolRunner",
    "current_agent",
    "current_tool_call",
    "yield_from",
]

_current_agent: contextvars.ContextVar[Agent] = contextvars.ContextVar("current_agent")


AgentOutputT = TypeVar("AgentOutputT", default=str)


class AgentStream(Generic[AgentOutputT]):
    """Async-iterable wrapper around an agent run's event stream.

    Exposes the run's :class:`Context` via :attr:`context` so callers can
    inspect (or use) the live messages/tools without threading them
    through their own bookkeeping::

        async with agent.run(model, messages) as stream:
            async for event in stream:
                ...
            print(stream.context.messages)

    Structurally satisfies the ``AsyncGenerator`` protocol by delegating
    to the underlying generator, so it can be passed directly to
    :func:`yield_from` and other APIs that expect an async generator.
    """

    def __init__(
        self,
        gen: AsyncGenerator[agent_events_.AgentEvent],
        context: Context,
        hook_registry: hooks_.HookRegistry,
    ) -> None:
        self._gen = gen
        self._context = context
        self._hook_registry = hook_registry
        self._blocked = False
        self._deferred_hooks: dict[str, types.messages.HookPart[Any]] = {}

    def _track(self, event: agent_events_.AgentEvent) -> agent_events_.AgentEvent:
        # Fold delivered events into the exposed run state, so that the
        # properties below are always consistent with the events the
        # consumer has seen so far.
        if isinstance(event, agent_events_.RunBlocked):
            self._blocked = True
        elif isinstance(event, events_.PendingHookEvent):
            self._deferred_hooks[event.hook.hook_id] = event.hook
        elif isinstance(event, agent_events_.HookEvent):
            # A blocked run can only resume via a hook resolution
            # or cancellation (see RunBlocked), so this is also the
            # unblock signal.
            self._deferred_hooks.pop(event.hook.hook_id, None)
            self._blocked = False
        return event

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> agent_events_.AgentEvent:
        return self._track(await self._gen.__anext__())

    async def asend(self, value: Any) -> agent_events_.AgentEvent:
        return self._track(await self._gen.asend(value))

    async def athrow(self, *args: Any, **kwargs: Any) -> agent_events_.AgentEvent:
        return self._track(await self._gen.athrow(*args, **kwargs))

    async def aclose(self) -> None:
        await self._gen.aclose()

    @property
    def context(self) -> Context:
        return self._context

    @property
    def hook_registry(self) -> hooks_.HookRegistry:
        """The run's :class:`~ai.agents.hooks.HookRegistry`.

        Inside the ``agent.run()`` block the registry is already
        current, so hook operations find it implicitly.  Pass this
        explicitly (``resolve_hook(..., registry=...)``) when resolving
        from a different task -- a UI callback, a server endpoint.
        """
        return self._hook_registry

    @property
    def blocked(self) -> bool:
        """Whether the run is blocked awaiting external hook resolution.

        Set by a delivered :class:`~ai.types.events.RunBlocked` event,
        cleared by the hook resolution that follows.  True means
        nothing in the run can make progress until a deferred hook (see
        :attr:`deferred_hooks`) is resolved — e.g. a tool approval.
        After the run ends this keeps its final value, so serverless
        drivers can distinguish "turn complete" from "turn suspended
        awaiting input".
        """
        return self._blocked

    @property
    def deferred_hooks(self) -> list[types.messages.HookPart[Any]]:
        """Hooks that are deferred as of the last delivered event."""
        return list(self._deferred_hooks.values())

    @property
    def messages(self) -> list[types.messages.Message]:
        return self._context.messages

    @property
    def output(self) -> AgentOutputT:
        """Return the run's output.

        Defaults to the final assistant message's concatenated text.
        When an ``output_type`` was passed, the assistant message's text
        is validated as JSON against that type and the parsed instance
        is returned.
        """
        last = self._context.messages[-1]
        return cast("AgentOutputT", last.get_output(self._context.output_type))


class Context(pydantic.BaseModel):
    """Everything that goes into the LLM."""

    model: models.Model
    messages: list[types.messages.Message]
    tools: list[Tool]
    output_type: type[pydantic.BaseModel] | None = pydantic.Field(
        default=None, exclude=True, repr=False
    )
    params: models.InferenceRequestParams | None = pydantic.Field(
        default=None, exclude=True, repr=False
    )

    _tool_resolver: ToolResolver = pydantic.PrivateAttr(default_factory=lambda: ToolResolver([]))

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    def keep_running(self) -> bool:
        """Call at top of an agent loop to see whether to keep running."""
        if not self.messages:
            return False

        last_message = self.messages[-1]
        # Bail out if any tool result in the last message is a
        # deferred-hook placeholder. There's nothing we can do until
        # those are resolved and we get called again.
        if any(r.is_hook_deferred for r in last_message.tool_results):
            return False
        return last_message.replay or last_message.role not in (
            "assistant",
            "internal",
        )

    @overload
    def resolve(self, tool_part: types.messages.ToolCallPart) -> ToolCall: ...
    @overload
    def resolve(self, tool_part: Sequence[types.messages.ToolCallPart]) -> list[ToolCall]: ...

    def resolve(
        self,
        tool_part: types.messages.ToolCallPart | Sequence[types.messages.ToolCallPart],
    ) -> ToolCall | list[ToolCall]:
        """Resolve ToolCallPart(s) into callable ToolCall object(s).

        Deprecated: use :meth:`Agent.resolve` instead.
        """
        return self._tool_resolver.resolve(tool_part)

    def add(
        self,
        message: types.messages.Message | Sequence[types.messages.Message] | None,
    ) -> None:
        """Append message(s) to the context, skipping any flagged ``replay``.

        Replay-flagged messages come from ``models.stream`` short-
        circuiting an existing assistant turn (resume-after-approval).
        The default loop calls ``context.add(stream.message)`` after
        every stream — the flag lets that be a no-op on replay rather
        than producing a duplicate turn.
        """
        if message is None:
            return
        msgs = [message] if isinstance(message, types.messages.Message) else list(message)
        for msg in msgs:
            if msg.replay:
                continue
            self.messages.append(msg)


class Agent:
    """Bag of configuration: model + tools + loop."""

    TOOLS: ClassVar[list[AgentTool]] = []
    """Class-level default tools.

    Subclasses can declare a fixed tool set here::

        class WeatherAgent(ai.Agent):
            TOOLS = [get_weather, get_population]

    Tools passed to ``__init__`` are appended to ``TOOLS``, so callers can
    extend the class-level set per instance.
    """

    LOOP_BUFFER: ClassVar[int | None] = None
    """How many events ``loop`` may run ahead of the consumer of ``run``.

    ``None`` (the default) is unbounded: the loop keeps going while the
    consumer is between reads. ``0`` runs the loop in lockstep, so it is
    only advanced when the consumer asks for an event; loops that
    sequence side effects against consumer code depend on this.
    """

    def __init__(
        self,
        *,
        tools: Sequence[AgentTool | Tool] | None = None,
    ) -> None:
        self._tools: list[AgentTool] = []
        self._provider_tools: list[Tool] = []
        for t in [*self.TOOLS, *(tools or [])]:
            if isinstance(t, AgentTool):
                self._tools.append(t)
            else:
                self._provider_tools.append(t)
        self._tool_resolver = ToolResolver(self._tools)

    @property
    def tools(self) -> list[AgentTool]:
        """The agent's registered tools (read-only copy)."""
        return list(self._tools)

    @overload
    def resolve(self, tool_part: types.messages.ToolCallPart) -> ToolCall: ...
    @overload
    def resolve(self, tool_part: Sequence[types.messages.ToolCallPart]) -> list[ToolCall]: ...

    def resolve(
        self,
        tool_part: types.messages.ToolCallPart | Sequence[types.messages.ToolCallPart],
    ) -> ToolCall | list[ToolCall]:
        """Resolve ToolCallPart(s) into callable ToolCall object(s)."""
        return self._tool_resolver.resolve(tool_part)

    async def loop(self, context: Context) -> AsyncGenerator[agent_events_.AgentEvent]:
        """Stream, execute tools, repeat.

        Override in a subclass to customise the agent's control flow.
        (A custom loop keeps run/model/tool/hook spans — those live in
        the layers it calls — but loses per-step grouping unless it
        opens its own ``telemetry.span`` blocks.)
        """
        while context.keep_running():
            async with (
                telemetry.span(telemetry.LoopTurnSpanData()),
                models.stream(context=context) as stream,
                ToolRunner() as tr,
                util.merge(stream, tr.events()) as events,
            ):
                async for event in events:
                    yield event

                    if isinstance(event, types.events.ToolEnd):
                        tool = self.resolve(event.tool_call)
                        tr.schedule(tool)

                context.add(stream.message)
                # This adds the tool message to the history, which
                # also has the effect of causing another turn through
                # the loop.
                context.add(tr.get_tool_message())

    @overload
    def run(
        self,
        model: models.Model,
        messages: list[types.messages.Message],
        *,
        params: models.InferenceRequestParams | None = None,
        hook_registry: hooks_.HookRegistry | None = None,
    ) -> AbstractAsyncContextManager[AgentStream[str]]: ...
    @overload
    def run[T: pydantic.BaseModel](
        self,
        model: models.Model,
        messages: list[types.messages.Message],
        *,
        output_type: type[T],
        params: models.InferenceRequestParams | None = None,
        hook_registry: hooks_.HookRegistry | None = None,
    ) -> AbstractAsyncContextManager[AgentStream[T]]: ...

    def run(
        self,
        model: models.Model,
        messages: list[types.messages.Message],
        *,
        output_type: type[pydantic.BaseModel] | None = None,
        params: models.InferenceRequestParams | None = None,
        hook_registry: hooks_.HookRegistry | None = None,
    ) -> AbstractAsyncContextManager[AgentStream[Any]]:
        """Run the agent loop, yielding events to the consumer.

        Used as an async context manager whose value the event stream,
        extended with the `context` and `messages` of the stream::

            async with agent.run(model, messages) as stream:
                async for event in stream:
                    ...
                print(stream.messages)

        Args:
            model: The model to use for LLM calls.
            messages: Initial conversation messages.
            output_type: Optional Pydantic model the model's output must
                conform to.  When set, ``stream.output`` validates the
                final assistant message's text against it.
            hook_registry: The :class:`~ai.agents.hooks.HookRegistry`
                for this run's hooks.  Defaults to the current registry
                (so a nested run joins the enclosing run's hooks), or a
                fresh one at the top level.  Pass a registry you own to
                resolve hooks from outside the run's context.

        To attribute a sub-agent's events to a branch, wrap the run in
        ``yield_from(..., label=...)`` — the label flows via
        ``PartialToolCallResult`` rather than on individual messages.

        """
        return self._run(
            model,
            messages,
            output_type=output_type,
            params=params,
            hook_registry=hook_registry,
        )

    @contextlib.asynccontextmanager
    async def _run(
        self,
        model: models.Model,
        messages: list[types.messages.Message],
        *,
        output_type: type[pydantic.BaseModel] | None,
        params: models.InferenceRequestParams | None,
        hook_registry: hooks_.HookRegistry | None,
    ) -> AsyncIterator[AgentStream[Any]]:
        context = Context(
            model=model,
            messages=list(messages),
            tools=[
                *[t.tool for t in self._tools],
                *self._provider_tools,
            ],
            output_type=output_type,
            params=params,
        )
        context._tool_resolver = self._tool_resolver
        _populate_model_inputs(context.messages, self._tool_resolver)
        _process_interrupted_hooks(context.messages)

        registry = hook_registry
        if registry is None:
            # Join the current registry when there is one (a nested run
            # shares the enclosing run's hooks); otherwise start fresh.
            registry = hooks_._hook_registry.get(None) or hooks_.HookRegistry()

        async def _events() -> AsyncGenerator[agent_events_.AgentEvent]:
            tracker = events_.RunStateTracker()
            retry_filter = agent_events_._RetryFilter()
            source = self.loop(context)
            async with contextlib.aclosing(runtime.run(source)) as events:
                async for event in events:
                    if not retry_filter.feed(event):
                        continue
                    # Feed the tracker before the replay filter: replayed
                    # StreamEnds carry the tool calls the dispatcher is
                    # about to re-run, which the fold must count.
                    transition = tracker.feed(event)
                    # Drop replay-flagged events: they're a control-flow
                    # signal for the loop's tool dispatcher (which already
                    # ran by the time we see the event here), not user-
                    # facing output.
                    if not event.replay:
                        yield event
                    if transition is not None:
                        yield transition

        async def _stream() -> AsyncGenerator[agent_events_.AgentEvent]:
            async with telemetry.span(
                telemetry.RunSpanData(
                    agent=type(self).__name__,
                    model=model.id,
                    messages=list(messages),
                    provider=model.provider.name,
                    tool_names=[t.name for t in context.tools],
                    output_type=(output_type.__name__ if output_type is not None else None),
                    params=params,
                )
            ) as sp:
                initial_count = len(context.messages)
                agent_token = _current_agent.set(self)
                try:
                    async with contextlib.aclosing(
                        util.decouple(_events(), buffer=self.LOOP_BUFFER)
                    ) as events:
                        async for event in events:
                            # a blocked run can only resume via a hook
                            # resolution or cancellation, so a non-pending
                            # HookEvent is also the unblock signal.
                            if isinstance(event, agent_events_.RunBlocked):
                                sp.data.blocked = True
                            elif (
                                isinstance(event, agent_events_.HookEvent)
                                and event.hook.status != "pending"
                            ):
                                sp.data.blocked = False
                            yield event
                finally:
                    _current_agent.reset(agent_token)
                    # Record whatever got produced, even on error or
                    # early close.
                    sp.data.final_message = next(
                        (msg for msg in reversed(context.messages) if msg.role == "assistant"),
                        None,
                    )
                    total: types.usage.Usage | None = None
                    for msg in context.messages[initial_count:]:
                        if msg.usage is not None:
                            total = msg.usage if total is None else total + msg.usage
                    sp.data.usage = total

        async with (
            hooks_.use_hook_registry(registry),
            contextlib.aclosing(AgentStream(_stream(), context, registry)) as astream,
        ):
            yield astream


@overload
def current_agent() -> Agent: ...


@overload
def current_agent[T: Agent](*, type: type[T]) -> T: ...


def current_agent(*, type: type[Agent] = Agent) -> Agent:
    """Return the agent whose stream is executing in this context.

    Pass ``type=`` to validate and narrow the returned agent type. Calling
    this outside an agent stream raises :class:`LookupError`.
    """
    agent = _current_agent.get()
    if not isinstance(agent, type):
        raise LookupError(f"current agent is {agent.__class__.__name__}, not {type.__name__}")
    return agent
