"""Ambient clock for span timestamps.

The wall clock is used by default; :func:`use_time` lets you plug in a
deterministic clock (e.g. inside a durable workflow body).
"""

from __future__ import annotations

import contextlib
import contextvars
import time
from collections.abc import AsyncIterator, Callable

_span_clock: contextvars.ContextVar[Callable[[], int] | None] = contextvars.ContextVar(
    "span_clock", default=None
)


def now_ns() -> int:
    """Nanoseconds since the epoch, from the ambient span clock.

    The wall clock by default; whatever :func:`use_time` installed
    otherwise.
    """
    clock = _span_clock.get()
    return clock() if clock is not None else time.time_ns()


@contextlib.asynccontextmanager
async def use_time(now_ns_fn: Callable[[], int]) -> AsyncIterator[None]:
    """Read span timestamps from ``now_ns_fn`` within this context.

    Framework's observability creates timestamps. This API can be
    used to plug an approved clock function in durable execution
    settings::

        async with ai.experimental_telemetry.use_time(workflow.time_ns):
            ...  # spans opened here read time from workflow.time_ns

    This can also be used as a decorator on async functions::

        @ai.experimental_telemetry.use_time(clock.time_ns)
        async def run(...):
            ...
    """
    token = _span_clock.set(now_ns_fn)
    try:
        yield
    finally:
        _span_clock.reset(token)
