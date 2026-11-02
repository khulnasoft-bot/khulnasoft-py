"""Span data types.

The ``kind`` field on each class is what travels with serialized data.
Restore typed data with ``Span[MyData].model_validate(...)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal

import pydantic
from typing_extensions import TypeVar

from ..types import messages as messages_, usage as usage_

if TYPE_CHECKING:
    # RunSpanData.params is typed as InferenceRequestParams, whose
    # sampling field uses ModelProviderDefault — a plain sentinel that
    # makes pydantic freak out when building a schema.  Import it only
    # under TYPE_CHECKING to avoid a circular import in models/core/api.py.
    from ..models.core import params as params_

    _InferenceParams = params_.InferenceRequestParams
else:
    _InferenceParams = Any


class SpanData:
    """Anything with a ``kind`` is span data.

    Implement it with a pydantic model to make your own typed spans::

        class RetrievalSpanData(pydantic.BaseModel):
            kind: Literal["retrieval"] = "retrieval"
            query: str
            count: int | None = None

        data = RetrievalSpanData(query=q)
        async with ai.experimental_telemetry.span(data) as sp:
            docs = await search(q)
            sp.data.count = len(docs)  # typed

    ``kind`` is what travels with the serialized data. Restore with
    ``Span[RetrievalSpanData].model_validate(...)`` to get it typed,
    otherwise you'll get a plain dict.
    """

    @property
    def kind(self) -> str: ...


class RunSpanData(pydantic.BaseModel):
    """One ``Agent.run``: the whole loop.

    ``blocked``/``final_message``/``usage`` are set at span end:
    ``blocked`` is True when the run ended suspended on an unresolved
    hook (see ``AgentStream.blocked``), ``final_message`` is the last
    assistant message produced, if any, ``usage`` is the sum of usage
    across the messages the run produced.
    """

    kind: Literal["run"] = "run"
    agent: str
    model: str
    messages: list[messages_.Message]
    provider: str | None = None
    tool_names: list[str] | None = None
    output_type: str | None = None
    params: _InferenceParams | None = None
    blocked: bool = False
    final_message: messages_.Message | None = None
    usage: usage_.Usage | None = None


class LoopTurnSpanData(pydantic.BaseModel):
    """One turn of the default agent loop.

    Carries no fields — it exists so adapters can group a turn's model
    and tool spans.  Turn order is given by ``started_at``/``parent_id``.
    """

    kind: Literal["loop_turn"] = "loop_turn"


class AiStreamSpanData(pydantic.BaseModel):
    """One streaming LLM call."""

    kind: Literal["ai_stream"] = "ai_stream"
    model: str
    messages: list[messages_.Message]
    params: _InferenceParams | None = None
    provider: str | None = None
    tool_names: list[str] | None = None
    output_type: str | None = None
    message: messages_.Message | None = None
    usage: usage_.Usage | None = None
    finish_reason: str | None = None
    response_id: str | None = None
    response_model: str | None = None


class AiGenerateSpanData(pydantic.BaseModel):
    """One buffered (non-streaming) LLM call.

    ``message``/``usage`` and the response identity fields are set at
    span end.
    """

    kind: Literal["ai_generate"] = "ai_generate"
    model: str
    messages: list[messages_.Message]
    params: _InferenceParams | None = None
    provider: str | None = None
    tool_names: list[str] | None = None
    output_type: str | None = None
    message: messages_.Message | None = None
    usage: usage_.Usage | None = None
    finish_reason: str | None = None
    response_id: str | None = None
    response_model: str | None = None


class EvaluateSpanData(pydantic.BaseModel):
    """One typed evaluation operation."""

    kind: Literal["evaluate"] = "evaluate"
    model: str
    provider: str | None = None
    question_count: int
    usage: usage_.Usage | None = None
    answer_count: int | None = None
    warnings: list[dict[str, Any]] | None = None


class EmbedSpanData(pydantic.BaseModel):
    """One embedding operation."""

    kind: Literal["embed"] = "embed"
    model: str
    provider: str | None = None
    input_count: int
    usage: usage_.Usage | None = None
    output_count: int | None = None
    dimensions: int | None = None
    warnings: list[dict[str, Any]] | None = None


class GenerateAudioSpanData(pydantic.BaseModel):
    """One audio generation operation."""

    kind: Literal["generate_audio"] = "generate_audio"
    model: str
    provider: str | None = None
    usage: usage_.Usage | None = None
    output_count: int | None = None
    warnings: list[dict[str, Any]] | None = None


class GenerateImageSpanData(pydantic.BaseModel):
    """One image generation operation."""

    kind: Literal["generate_image"] = "generate_image"
    model: str
    provider: str | None = None
    usage: usage_.Usage | None = None
    output_count: int | None = None
    warnings: list[dict[str, Any]] | None = None


class GenerateVideoSpanData(pydantic.BaseModel):
    """One video generation operation."""

    kind: Literal["generate_video"] = "generate_video"
    model: str
    provider: str | None = None
    usage: usage_.Usage | None = None
    output_count: int | None = None
    warnings: list[dict[str, Any]] | None = None


class RerankSpanData(pydantic.BaseModel):
    """One reranking operation."""

    kind: Literal["rerank"] = "rerank"
    model: str
    provider: str | None = None
    input_count: int
    top_n: int | None = None
    usage: usage_.Usage | None = None
    output_count: int | None = None
    warnings: list[dict[str, Any]] | None = None


class TranscribeSpanData(pydantic.BaseModel):
    """One transcription operation."""

    kind: Literal["transcribe"] = "transcribe"
    model: str
    provider: str | None = None
    usage: usage_.Usage | None = None
    duration_seconds: float | None = None
    warnings: list[dict[str, Any]] | None = None


class ToolExecutionSpanData(pydantic.BaseModel):
    """One tool execution, from dispatch to result.

    ``model_input`` is the value the LLM sees on its next turn, set
    only when it differs from ``result`` (aggregator-backed tools).
    ``tool_description`` is the tool's model-facing description,
    stamped at dispatch.
    """

    kind: Literal["tool_execution"] = "tool_execution"
    tool_name: str
    tool_call_id: str
    tool_description: str | None = None
    args: dict[str, Any] | None = None
    result: Any = None
    model_input: Any = None
    is_error: bool = False


class HookSpanData(pydantic.BaseModel):
    """One hook suspension, from deferred until resolved or cancelled.

    ``tool_call_id`` links the hook to the tool call it suspends, if
    any (e.g. approval gating).  ``resolution`` carries the resolution
    data when the hook resolves.
    """

    kind: Literal["hook"] = "hook"
    label: str
    hook_type: str
    metadata: dict[str, Any]
    tool_call_id: str | None = None
    status: Literal["pending", "resolved", "cancelled"] = "pending"
    resolution: dict[str, Any] | None = None


class CustomSpanData(pydantic.BaseModel):
    """A user span made with ``span("name")``.

    Attributes are set with :meth:`Span.set_attrs`.
    """

    kind: Literal["custom"] = "custom"
    attrs: dict[str, Any]


# names for span events shared between producers,
# adapters, and tests
FIRST_TOKEN = "first_token"
RESPONSE_COMPLETE = "response_complete"
HOOK_DEFERRED = "hook_deferred"
HOOK_RESOLVED = "hook_resolved"
HOOK_CANCELLED = "hook_cancelled"


_FrameworkData = Annotated[
    RunSpanData
    | LoopTurnSpanData
    | AiStreamSpanData
    | AiGenerateSpanData
    | EvaluateSpanData
    | EmbedSpanData
    | GenerateAudioSpanData
    | GenerateImageSpanData
    | GenerateVideoSpanData
    | RerankSpanData
    | TranscribeSpanData
    | ToolExecutionSpanData
    | HookSpanData
    | CustomSpanData,
    pydantic.Field(discriminator="kind"),
]

# adapters only read the data, they don't swap it out, so it's safe to make it
# covariant.
if TYPE_CHECKING:
    DataT_co = TypeVar("DataT_co", bound=SpanData, default=SpanData, covariant=True)
else:
    # try to deserialize to _FrameworkData and fallback to Any
    DataT_co = TypeVar("DataT_co", default=_FrameworkData | Any)
# covariant type can't be used for a function's input parameter, and we need
# to type span()
DataT = TypeVar("DataT", bound=SpanData)
