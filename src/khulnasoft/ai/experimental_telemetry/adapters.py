"""Adapter registry: register, unregister, and dispatch spans to adapters.

An adapter processes spans and decides what to do with them. Adapters
dispatch on the type of ``span.data``. An adapter that crashes is
logged and skipped — it never kills the run.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast, overload, runtime_checkable

from typing_extensions import TypeVar as BackportTypeVar

from .span import Span
from .span_data import DataT_co, SpanData, _FrameworkData

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # ``typing.TypeVar`` lacks the ``default=`` kwarg on Python <3.13.
    # Use the typing_extensions backport so this works on 3.12 too.
    DataT_co = BackportTypeVar("DataT_co", bound=SpanData, default=SpanData, covariant=True)
else:
    # try to deserialize to _FrameworkData and fallback to Any
    DataT_co = BackportTypeVar("DataT_co", default=_FrameworkData | Any)
# covariant type can't be used for a function's input parameter, and we need
# to type span()
DataT = BackportTypeVar("DataT", bound=SpanData)


@runtime_checkable
class AdapterProtocol(Protocol):
    """The async callbacks implemented by a telemetry adapter."""

    async def on_span_start(self, span: Span, /) -> None: ...

    async def on_span_event(self, span: Span, event: Any, /) -> None: ...

    async def on_span_end(self, span: Span, /) -> None: ...


class AdapterCallable:
    """The ``__call__`` shape the :func:`adapter` decorator accepts.

    Static-typing companion to :class:`AdapterProtocol`: checkers don't
    see the callbacks :func:`adapter` mixes into a decorated class, so
    :func:`register` accepts this shape as well.
    """

    def __call__(self, span: Span, /) -> AsyncGenerator[None, Any] | None: ...


_adapters: list[AdapterProtocol] = []


def register(adapter: AdapterProtocol | AdapterCallable) -> None:
    """Add an adapter.  Multiple adapters coexist independently."""
    if not isinstance(adapter, AdapterProtocol):
        raise TypeError(
            f"{adapter!r} does not implement the adapter callbacks; "
            "an adapter class must be decorated with @adapter"
        )
    _adapters.append(adapter)


def unregister(adapter: AdapterProtocol | AdapterCallable) -> None:
    """Remove a previously registered adapter."""
    assert isinstance(adapter, AdapterProtocol)  # register() enforced it
    _adapters.remove(adapter)


def is_enabled() -> bool:
    """Whether anything is listening for spans.

    True when a sink is routed with :func:`use_sink` or at least one
    adapter is registered.
    """
    # Lazy import to avoid circular import: sink.py imports adapters.py.
    from .sink import _current_sink

    return _current_sink.get() is not None or bool(_adapters)


async def _dispatch(
    call: Callable[[AdapterProtocol], Awaitable[None]],
) -> None:
    for adapter in list(_adapters):
        try:
            await call(adapter)
        except Exception:
            logger.exception("telemetry adapter %r raised", adapter)


class AdapterMixin:
    """The driver :func:`adapter` mixes into a decorated class.

    Implements the adapter callbacks. Don't subclass it directly. Put
    :func:`adapter` over a class with ``__call__`` async generator
    method.
    """

    # Name-mangled so the driver's bookkeeping can never collide with
    # an attribute of the class it is mixed into; created lazily so
    # that class keeps its ``__init__`` entirely to itself.
    __live: dict[str, AsyncGenerator[None, Any]] | None = None

    # Positional-only params on all overridable methods, so overrides
    # are free to pick their own names.
    def __call__(self, span: Span, /) -> AsyncGenerator[None, Any] | None:
        """Return the generator frame for one span, or ``None``.

        The decorated class's ``__call__`` overrides this.
        """
        return None

    async def on_span_start(self, span: Span, /) -> None:
        gen = self(span)
        if gen is None:
            return
        try:
            await anext(gen)
        except StopAsyncIteration:
            return  # returned before yielding: opted out of this span
        if self.__live is None:
            self.__live = {}
        self.__live[span.id] = gen

    async def on_span_event(self, span: Span, event: Any, /) -> None:
        live = self.__live
        gen = live.get(span.id) if live is not None else None
        if live is None or gen is None:
            return  # opted out, span already ended, or start raised
        try:
            await gen.asend(event)
        except StopAsyncIteration:
            # Finished mid-span: opted out of the rest of this span,
            # including its end.
            del live[span.id]
        except BaseException:
            # The generator frame is dead, don't resume it again at
            # span end.  The error itself is logged by _dispatch.
            del live[span.id]
            raise

    async def on_span_end(self, span: Span, /) -> None:
        gen = self.__live.pop(span.id, None) if self.__live else None
        if gen is None:  # opted out, or start raised (and was logged)
            return
        try:
            await anext(gen)
        except StopAsyncIteration:
            return
        await gen.aclose()
        raise RuntimeError("adapter generator yielded again after span end")


class _AdapterFn(AdapterMixin):
    """Adapter built by :func:`adapter` from a function."""

    def __init__(self, fn: Callable[[Span], AsyncGenerator[None, Any]]) -> None:
        self._fn = fn

    def __repr__(self) -> str:
        return f"adapter({getattr(self._fn, '__qualname__', self._fn)!r})"

    def __call__(self, span: Span, /) -> AsyncGenerator[None, Any]:
        return self._fn(span)


_AdapterCallableT = TypeVar("_AdapterCallableT", bound=AdapterCallable)


@overload
def adapter(target: type[_AdapterCallableT]) -> type[_AdapterCallableT]: ...  # noqa: UP047


@overload
def adapter(  # noqa: UP047
    target: Callable[[Span], AsyncGenerator[None, Any]],
) -> AdapterMixin: ...  # noqa: UP047


def adapter(  # noqa: UP047
    target: type[_AdapterCallableT] | Callable[[Span], AsyncGenerator[None, Any]],
) -> type[_AdapterCallableT] | AdapterMixin:
    """Build an adapter from an async generator function or class.

    Decorating a free-standing async generator function returns a
    ready-to-register adapter.

    Decorating a class whose ``__call__`` is an async generator method
    returns that class with the adapter machinery (:class:`AdapterMixin`)
    mixed in::

        @adapter
        class Vendor:
            def __init__(self, *, api_key):
                self._client = sdk.Client(api_key)

            async def __call__(self, span):
                ...  # same yield loop as the function form

        ai.experimental_telemetry.register(Vendor(api_key="..."))

    How to use to bridge a vendor SDKs:
    write the vendor's ``with``/``async with`` around one yield loop.
    Code before the loop runs at span start; each span event resumes the
    yield with the :class:`SpanEvent`, live; span end resumes it with
    ``None``, and the code after the loop runs with ``span.data``
    fully populated and ``ended_at`` set::

        @adapter
        async def vendor(span):
            with sdk.start_span(span.name) as v:
                while (ev := (yield)) is not None:   # each event, live
                    v.log_event(ev.name, timestamp=ev.time_ns)
                v.update(output=span.data)           # span end

        ai.experimental_telemetry.register(vendor)

    - A failed span ends the loop normally, like any other; read
      ``span.error`` (a serializable :class:`SpanError`, never a live
      exception — the span may have failed in another process) after
      the loop to report it.
    - A span that lived elsewhere and arrives complete is replayed to
      the generator as start, events, end, back to back — write the
      bridge against the span's fields and it handles both live and
      after-the-fact delivery.
    - Returning before the first ``yield`` skips that span — cheap
      filtering by span type.  Returning mid-span, from inside the
      loop, opts out of the rest of that span, including its end.
    - Don't make a bare ``yield`` that ignores the sent value, because
      it runs the code after it on the first event, not at span
      end.  Always loop until the yield returns ``None``.
    - Like any adapter, a generator that raises is logged and skipped;
      it never kills the run.
    """
    if inspect.isclass(target):
        if issubclass(target, AdapterMixin):
            raise TypeError(f"{target.__name__} is already an adapter")
        call = inspect.getattr_static(target, "__call__", None)
        if not inspect.isasyncgenfunction(call):
            raise TypeError(
                "@adapter on a class requires __call__ to be an async "
                "generator method (`async def` containing a `yield` loop)"
            )
        mixed = type(
            target.__name__,
            (target, AdapterMixin),
            {
                "__module__": target.__module__,
                "__qualname__": target.__qualname__,
                "__doc__": target.__doc__,
            },
        )
        return cast("type[_AdapterCallableT]", mixed)
    if not inspect.isasyncgenfunction(target):
        raise TypeError(
            "@adapter requires an async generator function (`async def` containing a `yield` loop)"
        )
    return _AdapterFn(target)
