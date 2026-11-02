"""Characterization tests for the public ``khulnasoft.ai`` API.

These tests lock in the current public surface so refactors in
:file:`src/khulnasoft/ai` cannot accidentally remove or rename exports.
"""

from __future__ import annotations

import importlib

import pytest

import khulnasoft.ai as ai

_PROVIDER_MODULES = [
    "khulnasoft.ai.providers",
    "khulnasoft.ai.providers.ai_gateway",
    "khulnasoft.ai.providers.anthropic",
    "khulnasoft.ai.providers.base",
    "khulnasoft.ai.providers.openai",
    "khulnasoft.ai.providers.typesafe",
]


@pytest.mark.parametrize("name", sorted(ai.__all__))
def test_public_export_is_importable(name: str) -> None:
    """Every name in ``ai.__all__`` must be reachable as an attribute."""
    assert hasattr(ai, name), f"missing public export: {name}"
    assert getattr(ai, name) is not None


def test_public_exports_match_all() -> None:
    """``dir(ai)`` should contain every name declared in ``__all__``."""
    missing = [name for name in ai.__all__ if name not in dir(ai)]
    assert not missing, f"__all__ names not in dir(ai): {missing}"


@pytest.mark.parametrize("module", _PROVIDER_MODULES)
def test_provider_modules_import(module: str) -> None:
    """Provider entry-point modules must import cleanly."""
    importlib.import_module(module)


def test_get_provider_is_callable() -> None:
    """``get_provider`` must be exposed and callable."""
    from khulnasoft.ai.providers import get_provider

    assert callable(get_provider)


def test_submodules_exposed() -> None:
    """Top-level subpackage modules referenced in ``ai.__init__`` must attach."""
    for attr in (
        "durable",
        "errors",
        "experimental_telemetry",
        "models",
        "ops",
        "providers",
        "testing",
        "ui",
        "util",
        "agents",
        "types",
    ):
        assert hasattr(ai, attr), f"missing submodule attribute: {attr}"
