from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from khulnasoft.integrations.celery import install_khulnasoft_celery_integration
from khulnasoft.queue import get_subscriptions
from khulnasoft.queue.testing import clear_subscriptions

EXAMPLE_ROOT = Path(__file__).parents[2] / "examples" / "chunks"


def test_chunks_example_uses_pyproject_subscriber_contract() -> None:
    assert not (EXAMPLE_ROOT / "khulnasoft.json").exists()
    assert (EXAMPLE_ROOT / "main.py").is_file()
    assert (EXAMPLE_ROOT / "worker.py").is_file()

    pyproject = (EXAMPLE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[[tool.khulnasoft.subscribers]]" in pyproject
    assert 'entrypoint = "worker:celery_app"' in pyproject
    assert "topics =" not in pyproject


def test_chunks_example_worker_registers_celery_subscription(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started_apps: list[object] = []
    monkeypatch.setenv("KHULNASOFT", "1")
    monkeypatch.setenv("KHULNASOFT_REGION", "iad1")
    monkeypatch.setenv("KHULNASOFT_QUEUE_TOKEN", "token")
    monkeypatch.setattr(
        "khulnasoft.integrations.celery._broker._start_embedded_worker",
        started_apps.append,
    )
    sys.path.insert(0, str(EXAMPLE_ROOT))
    clear_subscriptions()
    try:
        importlib.import_module("worker")
        # The Khulnasoft build installs the integration after importing the
        # subscriber entrypoint, which registers the queues of Celery apps
        # created during import.
        install_khulnasoft_celery_integration()
        tasks = importlib.import_module("tasks")

        assert ("celery-khulnasoft__celery__example__chunks-celery", "celery") in [
            (sub.topic, sub.consumer_group) for sub in get_subscriptions()
        ]
        assert tasks.celery_app in started_apps
    finally:
        clear_subscriptions()
        sys.path.remove(str(EXAMPLE_ROOT))
        for name in ("worker", "main", "tasks"):
            sys.modules.pop(name, None)
