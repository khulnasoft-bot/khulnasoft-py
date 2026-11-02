"""Span sinks: route span snapshots to adapters or defer them.

A :class:`Sink` sits before the adapters and routes span snapshots. The
default sink is the adapter registry; :func:`use_sink` reroutes pushes
within a context (e.g. to a :class:`DictSink` inside a durable
workflow).
"""

from __future__ import annotations

import contextlib
import contextvars
from collections.abc import AsyncIterator, Iterable, Mapping
from typing import Any

from .adapters import _dispatch
from .span import Span


class Sink:
    """Anything that accepts pushed span snapshots."""

    async def on_push(self, span: Span, /) -> None: ...


_current_sink: contextvars.ContextVar[Sink | None] = contextvars.ContextVar(
    "current_sink", default=None
)


@contextlib.asynccontextmanager
async def use_sink(sink: Sink | None) -> AsyncIterator[None]:
    """Route span pushes to ``sink`` within this context.

    The default (outside any ``use_sink``) is the adapter registry.
    Inside a durable workflow body where side effects are not allowed,
    you can route to a :class:`DictSink` instead and re-push the
    collected spans from a step / activity::

        sink = DictSink()
        async with use_sink(sink):
            ...  # replayed / suspendable code
        payload = [s.model_dump(mode="json") for s in sink.finished_spans]

    ``None`` is a no-op.
    """
    if sink is None:
        yield
        return
    token = _current_sink.set(sink)
    try:
        yield
    finally:
        _current_sink.reset(token)


class DictSink:
    """A sink that keeps the latest snapshot of every span pushed to it.

    ``spans`` maps span id to the most recent snapshot, in first-push
    order.  Scoop the complete ones out as data (:attr:`finished_spans`)
    and re-push them where the real sink is available::

        sink = DictSink()
        async with use_sink(sink):
            ...  # replayed / suspendable code
        payload = [s.model_dump(mode="json") for s in sink.finished_spans]

        # elsewhere (a workflow step, another process):
        await push_all(payload)
    """

    def __init__(self) -> None:
        self.spans: dict[str, Span] = {}

    async def on_push(self, span: Span, /) -> None:
        self.spans[span.id] = span

    @property
    def finished_spans(self) -> list[Span]:
        """The collected spans that have ended, in first-push order."""
        return [s for s in self.spans.values() if s.ended_at is not None]


async def push_all(spans: Iterable[Span | Mapping[str, Any]]) -> None:
    """Push each span, in order; dumped spans are validated first.

    This is a utility that can be used with :class:`DictSink` to push
    a bunch of collected spans all at once::

        await push_all(payload)
    """
    for item in spans:
        span = item if isinstance(item, Span) else Span.model_validate(item)
        await span.push()


class _RegistrySink:
    """The default sink: drives registered adapters.

    Translates a stream of span snapshots into
    ``on_span_start`` / ``on_span_event`` / ``on_span_end`` callbacks.

    Rules:

    - a snapshot with ``started_at=None`` reports nothing (the span
      hasn't started);
    - the first snapshot of an id fires ``on_span_start``, then
      ``on_span_event`` per event, then ``on_span_end`` if the snapshot
      is already complete; so a span that lived elsewhere and arrives
      finished is delivered whole;
    - later snapshots fire ``on_span_event`` for events not seen
      before, and ``on_span_end`` once ``ended_at`` appears;
    - after the end the id is forgotten: pushing a completed span again
      re-delivers it in full.
    """

    def __init__(self) -> None:
        self._views: dict[str, Span] = {}

    async def on_push(self, span: Span, /) -> None:
        if span.started_at is None:
            return
        view = self._views.get(span.id)
        if view is None:
            view = span
            self._views[view.id] = view
            await _dispatch(lambda a: a.on_span_start(view))
            fresh = list(view.events)
        else:
            seen = len(view.events)
            # we need to preserve the view's identity
            # but update all of the fields
            view.__dict__.update(span.__dict__)
            fresh = view.events[seen:]
        for event in fresh:
            # the default binds `event` now; a plain lambda would trip B023
            def call(a: Any, ev: Any = event) -> Any:
                return a.on_span_event(view, ev)

            await _dispatch(call)
        if view.ended_at is not None:
            del self._views[view.id]
            await _dispatch(lambda a: a.on_span_end(view))


_registry_sink = _RegistrySink()
