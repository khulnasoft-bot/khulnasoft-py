"""Span model and current-span context.

Contains :class:`Span`, :class:`SpanEvent`, :class:`SpanError`, and the
ambient current-span context var (:func:`current_span`, :func:`use_span`).
"""

from __future__ import annotations

import contextlib
import contextvars
import logging
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Self,
    overload,
)

import pydantic

from ..types.messages import generate_id
from .clock import now_ns
from .span_data import (
    CustomSpanData,
    DataT,
    DataT_co,
    SpanData,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class SpanEvent(pydantic.BaseModel):
    """A named, timestamped milestone inside a span's lifetime.

    Lives in ``span.events``; the next push delivers it.
    :meth:`Span.add_event` is the shorthand for the common case::

        sp.add_event(FIRST_TOKEN)
        await sp.push()

    Ordering: events on one span are delivered in list order; there is
    no ordering guarantee across spans.
    """

    name: str
    time_ns: int
    attrs: dict[str, Any]


class SpanError(pydantic.BaseModel):
    """A serializable record of the failure that ended a span.

    Spans cross process boundaries, so the error they carry is plain
    data, not a live exception.
    """

    type: str
    message: str

    @classmethod
    def from_exception(cls, exc: BaseException) -> SpanError:
        return cls(type=type(exc).__name__, message=str(exc))


class Span[DataT_co](pydantic.BaseModel):
    """A serializable record of a unit of work.

    Generic in its data type: ``span(RetrievalSpanData(...))`` gives a
    ``Span[RetrievalSpanData]``, so late assignments to ``sp.data``
    fields are type checked.  A bare ``Span`` is ``Span[SpanData]``.

    Lifecycle is encoded in timestamp fields:

    - if ``started_at=None``, this span hasn't started,
    - if ``ended_at`` is set, the span is complete.

    Mutate fields, then :meth:`push` to report the new state. Nothing is
    reported except by pushing.

    A span round-trips through ``model_dump``/``model_validate`` like
    any pydantic model. Use ``Span[MyData].model_validate(...)`` to
    restore custom data types.

    ``replay=True`` marks work that is being replayed (resume,
    serverless re-entry) rather than performed live.

    A span created while telemetry was off (see :func:`is_enabled`) has
    an empty ``id`` and is a noop: :meth:`push` delivers nothing.

    ``set_as_current=False`` marks a span that does not set itself as
    current. This is used by ai.stream's span that stays open for the
    duration of a loop turn because of the context manager api.
    Adapters must not make those spans "current" either to avoid
    nesting discrepancies.

    ``trace_attrs`` is user data that propagates down from parent to
    child on creation.

    ``schema_version`` tracks the shape of spans and their data types.
    """

    name: str
    data: DataT_co
    id: str
    trace_id: str
    parent_id: str | None = None
    started_at: int | None = None  # ns since the epoch, see ``now_ns``
    ended_at: int | None = None
    error: SpanError | None = None
    replay: bool = False
    set_as_current: bool = True
    events: list[SpanEvent] = pydantic.Field(default_factory=list)
    trace_attrs: dict[str, Any] = pydantic.Field(default_factory=dict)

    schema_version: ClassVar[int] = 5

    def set_attrs(self, attrs: Mapping[str, Any] | None = None, /, **kwargs: Any) -> None:
        """Attach attributes to a span created with ``span("name")``.

        Attribute names that aren't valid Python keywords (viewers use
        dotted names like ``"output.value"``) go in the positional
        mapping; it merges with the keyword arguments::

            sp.set_attrs({"output.value": title}, model="haiku")
        """
        if not isinstance(self.data, CustomSpanData):
            raise TypeError(
                "set_attrs() only works on user spans; framework "
                "spans carry typed data, assign its fields directly"
            )
        self.data.attrs.update({**(attrs or {}), **kwargs})

    def add_event(
        self,
        name: str,
        attrs: Mapping[str, Any] | None = None,
        /,
        **kwargs: Any,
    ) -> SpanEvent:
        """Append a named event stamped with the ambient clock.

        Appends only; the event is delivered by the next :meth:`push`,
        or when exiting the ``span()`` context manager::

            sp.add_event(FIRST_TOKEN)
            await sp.push()

        Returns the appended event.
        """
        event = SpanEvent(
            name=name,
            # a noop span (telemetry off at creation) reads no clock
            time_ns=now_ns() if self.id else 0,
            attrs={**(attrs or {}), **kwargs},
        )
        self.events.append(event)
        return event

    def stamp_start(self) -> Self:
        """Set ``started_at`` from the ambient clock; return the span.

        Only writes the field; nothing is reported until :meth:`push`.
        Returns the span so minting reads as one expression::

            payload = create_span("turn").stamp_start().model_dump()
        """
        self.started_at = now_ns()
        return self

    def stamp_end(self, *, error: SpanError | BaseException | None = None) -> Self:
        """Set ``ended_at`` from the ambient clock; return the span.

        Also records ``error`` when one is given by converting an
        exception to a serializable :class:`SpanError`.  ``error=None``
        keeps any error already on the span.  Only writes fields; push
        to report::

            await sp.stamp_end(error=exc).push()
        """
        self.ended_at = now_ns()
        if isinstance(error, BaseException):
            self.error = SpanError.from_exception(error)
        elif error is not None:
            self.error = error
        return self

    async def push(self) -> None:
        """Deliver a frozen copy of this span to the current sink.

        The default sink drives the registered adapters (see
        :func:`register`); :func:`use_sink` reroutes pushes within a
        context.  Each push snapshots the whole span, so keep mutating
        and push again as the work progresses. The last push with
        ``ended_at`` set is the complete record.

        Telemetry never kills the run: a sink (or adapter) failure is
        logged and swallowed.
        """
        if not self.id:
            return  # noop: telemetry was off at creation
        # Lazy import to avoid a circular import: sink.py imports span.py.
        from .sink import _current_sink, _registry_sink

        sink = _current_sink.get() or _registry_sink
        try:
            await sink.on_push(self.model_copy(deep=True))
        except Exception:
            logger.exception("telemetry sink %r raised in on_push", sink)


# utilities for managing the current span

_current: contextvars.ContextVar[Span | None] = contextvars.ContextVar("current_span", default=None)


def current_span() -> Span | None:
    """Return the current span, or ``None`` when no span is open."""
    return _current.get()


@contextlib.asynccontextmanager
async def use_span(span_: Span | None) -> AsyncIterator[None]:
    """Make ``span_`` the current span within this context.

    Unlike :func:`span` this is pure context plumbing with no
    timestamps and no pushes.  Use it to continue a trace around
    existing work, e.g. parenting under a span restored from another
    process::

        turn_span = Span.model_validate(payload["turn_span"])
        async with ai.experimental_telemetry.use_span(turn_span):
            ...  # spans opened here parent under turn_span

    ``None`` is a no-op.
    """
    if span_ is None:
        yield
        return
    token = _current.set(span_)
    try:
        yield
    finally:
        _current.reset(token)


@overload
def create_span(
    name_or_data: str,
    /,
    *,
    parent: Span | None = None,
    replay: bool = False,
    set_as_current: bool = True,
) -> Span[CustomSpanData]: ...


@overload
def create_span(
    name_or_data: DataT,
    /,
    *,
    parent: Span | None = None,
    replay: bool = False,
    set_as_current: bool = True,
) -> Span[DataT]: ...


def create_span(
    name_or_data: str | SpanData,
    /,
    *,
    parent: Span | None = None,
    replay: bool = False,
    set_as_current: bool = True,
) -> Span[Any]:
    """Create a span: identity only, nothing is reported.

    Mints the span id, and takes trace id, parentage, and a copy of
    ``trace_attrs`` from ``parent`` (default: the current span; a fresh
    trace when there is none).  ``parent`` may be a span restored from
    JSON.

    The span has no timestamps yet: :meth:`Span.stamp_start` and
    :meth:`Span.push` when the work begins, or hand the whole lifecycle
    to the :func:`span` context manager.

    While telemetry is off (see :func:`is_enabled`) this returns a noop
    span instead.
    """
    # Lazy import to avoid circular import: sink.py imports span.py.
    from .sink import is_enabled as _is_enabled

    if isinstance(name_or_data, str):
        name = name_or_data
        data: SpanData = CustomSpanData(attrs={})
    else:
        name = name_or_data.kind
        data = name_or_data

    if not _is_enabled():
        return Span(
            name=name,
            data=data,
            id="",
            trace_id="",
            parent_id=None,
            replay=replay,
            set_as_current=False,
        )
    if parent is None:
        parent = _current.get()
    if parent is None:
        trace_id, parent_id = generate_id("trace"), None
        trace_attrs: dict[str, Any] = {}
    else:
        trace_id, parent_id = parent.trace_id, parent.id
        trace_attrs = dict(parent.trace_attrs)
    return Span(
        name=name,
        data=data,
        id=generate_id("span"),
        trace_id=trace_id,
        parent_id=parent_id,
        replay=replay,
        set_as_current=set_as_current,
        trace_attrs=trace_attrs,
    )


@overload
def span(
    name_or_data: str,
    /,
    *,
    parent: Span | None = None,
    replay: bool = False,
    set_as_current: bool = True,
) -> contextlib.AbstractAsyncContextManager[Span[CustomSpanData]]: ...


@overload
def span(
    name_or_data: DataT,
    /,
    *,
    parent: Span | None = None,
    replay: bool = False,
    set_as_current: bool = True,
) -> contextlib.AbstractAsyncContextManager[Span[DataT]]: ...


def span(
    name_or_data: str | SpanData,
    /,
    *,
    parent: Span | None = None,
    replay: bool = False,
    set_as_current: bool = True,
) -> contextlib.AbstractAsyncContextManager[Span[Any]]:
    """Open a span; it sets itself as current inside the block.

    Sugar over the data api: creates the span, stamps ``started_at``
    and pushes on enter; stamps ``ended_at`` (and ``error``, if the
    block raised) and pushes on exit.

    Pass a name for a user span (set attributes on it with
    :meth:`Span.set_attrs`), or a :class:`SpanData` instance for a
    typed one. Exceptions are recorded on the span and re-raised.

    ``parent`` overrides the ambient parent for this span: a live
    :class:`Span`, or one restored from another process to continue its
    trace here.  The default parents under the current span.

    ``set_as_current=False`` keeps the span from becoming current:
    work done while it is open parents to *its* parent instead. Used by
    ai.stream because of the context manager api.
    """
    # type checkers can't apply asynccontextmanager
    # to an overloaded function directly.
    return _span_impl(
        name_or_data,
        parent=parent,
        replay=replay,
        set_as_current=set_as_current,
    )


@contextlib.asynccontextmanager
async def _span_impl(
    name_or_data: str | SpanData,
    /,
    *,
    parent: Span | None,
    replay: bool,
    set_as_current: bool,
) -> AsyncIterator[Span[Any]]:
    sp: Span[Any] = create_span(
        name_or_data,
        parent=parent,
        replay=replay,
        set_as_current=set_as_current,
    )
    if not sp.id:
        # noop: no timestamps, no pushes, never current
        yield sp
        return
    sp.stamp_start()
    await sp.push()
    token = _current.set(sp) if set_as_current else None
    try:
        yield sp
    except BaseException as exc:
        # GeneratorExit is how a consumer closes a stream early.
        if not isinstance(exc, GeneratorExit) and sp.error is None:
            sp.error = SpanError.from_exception(exc)
        raise
    finally:
        # a span that set itself as current must be closed while it is
        # still current, in the task that opened it.
        misordered = False
        if token is not None:
            if _current.get() is not sp:
                misordered = True
            else:
                try:
                    _current.reset(token)
                except ValueError:
                    # token from a different task's context.
                    misordered = True
        sp.ended_at = now_ns()
        await sp.push()
        if misordered:
            raise RuntimeError(
                f"span {sp.name!r} closed out of order: it is not the "
                "current span at close, or was closed in a different "
                "task than it was opened in. A span that sets itself "
                "as current must be closed innermost-first in the "
                "opening task; open overlapping spans with "
                "set_as_current=False."
            )
