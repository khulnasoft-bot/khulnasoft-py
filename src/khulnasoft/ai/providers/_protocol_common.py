"""Shared utilities for provider protocol conversion.

Contains helpers that are identical across OpenAI, Anthropic, AI Gateway,
and TypeSafe protocol modules: default/seed/header filtering and tool-ref
normalization.  Provider-specific conversion logic stays in each
provider's protocol module.
"""

from __future__ import annotations

from collections.abc import Mapping

from ..models.core import params as params_


def is_default(value: object) -> bool:
    """Return True when *value* is a ``ModelProviderDefault`` sentinel."""
    return isinstance(value, params_.ModelProviderDefault)


def not_default(value: object) -> bool:
    """Return True when *value* is not a ``ModelProviderDefault`` sentinel."""
    return not is_default(value)


def seed_value(seed: object) -> int | None:
    """Coerce a seed parameter into an int or ``None``."""
    if seed is None or seed == -1 or isinstance(seed, params_.RandomSeed):
        return None
    if isinstance(seed, int):
        return seed
    if isinstance(seed, params_.ModelProviderDefault):
        return None
    raise TypeError("seed must be an int, RANDOM, DEFAULT, or None")


def filter_extra_headers(
    headers: Mapping[str, str | params_.Unset] | None,
) -> dict[str, str] | None:
    """Drop ``Unset`` header values; return ``None`` for ``None`` input."""
    if headers is None:
        return None
    return {key: value for key, value in headers.items() if not isinstance(value, params_.Unset)}


def tool_ref_name(tool_ref: params_.ToolRef | str) -> str:
    """Normalize a tool ref to its string name."""
    return str(tool_ref)
