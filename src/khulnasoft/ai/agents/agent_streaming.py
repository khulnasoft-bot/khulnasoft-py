"""Streaming helpers for the agent run loop.

Contains :func:`yield_from` and :func:`_aggregate_from`, plus the
interrupted-hook processing used when resuming a run after a deferred
hook.
"""

from __future__ import annotations

from collections.abc import AsyncIterable, Callable
from typing import TypeVar

from .. import util
from ..types import agent_events as agent_events_, events as events_
from ..types.messages import Part
from . import runtime

T = TypeVar("T")
S = TypeVar("S")
R = TypeVar("R")


def _process_interrupted_hooks(messages: list[events_.Message]) -> None:
    """Detect an interrupted hook tail and mangle ``messages`` in place.

    This prepares the next agent run to resume correctly.

    Two shapes are recognised:

    1. **Trailing assistant turn with tool calls** (single-tool gating
       or no-tool-results-yet bail-out): mark the assistant message
       ``replay=True`` so ``models.stream`` short-circuits and the
       loop's tool dispatcher re-runs the calls.

    2. **Trailing tool message containing ``is_hook_deferred=True``
       results** (concurrent gating: some tools completed, others
       were suspended on a hook): fold the completed (non-deferred)
       tool results onto the matching ``ToolCallPart.cached_result``
       of the preceding assistant turn, drop the tool message, and
       mark the assistant message ``replay=True``.  On replay, the
       completed calls short-circuit to the cached value; the
       suspended calls re-run (and pick up the pre-registered hook
       resolution).
    """
    if not messages:
        return

    last = messages[-1]

    # Case 1: trailing assistant turn with tool calls.
    if last.role == "assistant" and last.tool_calls:
        messages[-1] = last.model_copy(update={"replay": True})
        return

    # Case 2: trailing tool message with at least one deferred-hook result.
    if (
        len(messages) >= 2
        and last.role == "tool"
        and last.tool_results
        and any(r.is_hook_deferred for r in last.tool_results)
    ):
        prev = messages[-2]
        if prev.role != "assistant" or not prev.tool_calls:
            return

        completed_by_id = {r.tool_call_id: r for r in last.tool_results if not r.is_hook_deferred}

        new_parts: list[Part] = []
        for part in prev.parts:
            if isinstance(part, events_.ToolCallPart) and part.tool_call_id in completed_by_id:
                part = part.model_copy(update={"cached_result": completed_by_id[part.tool_call_id]})
            new_parts.append(part)

        messages[-2] = prev.model_copy(update={"parts": new_parts, "replay": True})
        messages.pop()


async def _aggregate_from[T, S, R](
    source: AsyncIterable[T],
    *,
    aggregator: Callable[[], agent_events_.Aggregator[T, S, R]],
    tool_name: str | None = None,
    tool_call_id: str | None = None,
    label: object = None,
) -> agent_events_.Aggregator[T, S, R]:
    """Drain *source* into a fresh aggregator, forwarding partial events.

    Returns the live aggregator so callers can consume both the snapshot
    (the rich shape stored on ``ToolResultPart.result``) and the
    model-facing value (set via ``ToolResultPart.set_model_input``)
    without re-aggregating.
    """
    agg = aggregator()

    rt = runtime.get_runtime()
    async with util.maybe_aclosing(source):
        async for item in source:
            agg.feed(item)
            await rt.put_event(
                agent_events_.PartialToolCallResult(
                    tool_call_id=tool_call_id,
                    tool_name=tool_name,
                    label=label,
                    value=item,
                    aggregator_factory=aggregator,
                )
            )
    return agg


async def yield_from[T, S, R](
    source: AsyncIterable[T],
    *,
    aggregator: Callable[[], agent_events_.Aggregator[T, S, R]],
    # TODO: is this what we really want for labelling?
    tool_name: str | None = None,
    tool_call_id: str | None = None,
    label: object = None,
) -> R:
    """Drain *source*, forwarding each event to the current runtime.

    Use inside a custom loop to stream messages from a sub-agent to the
    consumer without adding them to the parent agent's message history::

        async with sub.run(model, msgs) as stream:
            result = await yield_from(stream, label="researcher")

    Works with :func:`asyncio.gather` for concurrent fan-out::

        async with a.run(model, m1) as sa, b.run(model, m2) as sb:
            r1, r2 = await asyncio.gather(
                yield_from(sa, label="a"),
                yield_from(sb, label="b"),
            )

    Each forwarded event is wrapped in a :class:`PartialToolCallResult`
    carrying ``label`` (and optionally ``tool_call_id`` / ``tool_name``)
    so the consumer can route by source.

    Returns the final message's text (empty string if no messages).
    """
    agg = await _aggregate_from(
        source,
        aggregator=aggregator,
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        label=label,
    )
    return agg.get_model_input()
