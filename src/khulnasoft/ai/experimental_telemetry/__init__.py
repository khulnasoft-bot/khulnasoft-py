"""Telemetry: spans, sinks, adapters, and the ambient current span.

Experimental: not part of the stable API, may change or be removed.

See :mod:`.span` for the full story.
"""

from .adapters import (
    AdapterCallable,
    AdapterMixin,
    AdapterProtocol,
    adapter,
    is_enabled,
    register,
    unregister,
)
from .clock import now_ns, use_time
from .sink import DictSink, Sink, push_all, use_sink
from .span import (
    Span,
    SpanData,
    SpanError,
    SpanEvent,
    create_span,
    current_span,
    span,
    use_span,
)
from .span_data import (
    FIRST_TOKEN,
    HOOK_CANCELLED,
    HOOK_DEFERRED,
    HOOK_RESOLVED,
    RESPONSE_COMPLETE,
    AiGenerateSpanData,
    AiStreamSpanData,
    CustomSpanData,
    EmbedSpanData,
    EvaluateSpanData,
    GenerateAudioSpanData,
    GenerateImageSpanData,
    GenerateVideoSpanData,
    HookSpanData,
    LoopTurnSpanData,
    RerankSpanData,
    RunSpanData,
    ToolExecutionSpanData,
    TranscribeSpanData,
)

__all__ = [
    "FIRST_TOKEN",
    "HOOK_CANCELLED",
    "HOOK_DEFERRED",
    "HOOK_RESOLVED",
    "RESPONSE_COMPLETE",
    "AdapterCallable",
    "AdapterMixin",
    "AdapterProtocol",
    "AiGenerateSpanData",
    "AiStreamSpanData",
    "CustomSpanData",
    "DictSink",
    "EmbedSpanData",
    "EvaluateSpanData",
    "GenerateAudioSpanData",
    "GenerateImageSpanData",
    "GenerateVideoSpanData",
    "HookSpanData",
    "LoopTurnSpanData",
    "RerankSpanData",
    "RunSpanData",
    "Sink",
    "Span",
    "SpanData",
    "SpanEvent",
    "SpanError",
    "ToolExecutionSpanData",
    "TranscribeSpanData",
    "adapter",
    "create_span",
    "current_span",
    "is_enabled",
    "now_ns",
    "push_all",
    "register",
    "span",
    "unregister",
    "use_sink",
    "use_span",
    "use_time",
]
