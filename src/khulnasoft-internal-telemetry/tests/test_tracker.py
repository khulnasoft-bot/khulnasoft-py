from __future__ import annotations

from typing import Any

import pytest

from khulnasoft.internal.telemetry import client as client_module, tracker


@pytest.fixture(autouse=True)
def reset_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tracker, "_telemetry_client", None)


def test_get_client_reuses_single_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[FakeClient] = []

    class FakeClient:
        def __init__(self) -> None:
            created.append(self)

    monkeypatch.setattr(client_module, "TelemetryClient", FakeClient)

    first = tracker.get_client()
    second = tracker.get_client()

    assert first is second
    assert created == [first]


def test_get_client_returns_none_when_initialization_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenClient:
        def __init__(self) -> None:
            raise RuntimeError("cannot initialize")

    monkeypatch.setattr(client_module, "TelemetryClient", BrokenClient)

    assert tracker.get_client() is None


def test_track_delegates_to_client(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    class FakeClient:
        def track(self, event: str, **attrs: Any) -> None:
            calls.append((event, attrs))

    monkeypatch.setattr(tracker, "_telemetry_client", FakeClient())

    tracker.track("cache_get", hit=True)

    assert calls == [("cache_get", {"hit": True})]


def test_track_swallows_client_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenClient:
        def track(self, event: str, **attrs: Any) -> None:
            raise RuntimeError("telemetry failed")

    monkeypatch.setattr(tracker, "_telemetry_client", BrokenClient())

    tracker.track("cache_get")


def test_with_telemetry_extracts_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(tracker, "track", lambda event, **attrs: calls.append((event, attrs)))

    @tracker.with_telemetry("blob_put", extract_metadata=lambda size: {"size_bytes": size})
    def upload(size: int) -> int:
        return size + 1

    assert upload(4) == 5
    assert calls == [
        (
            "blob_put",
            {"token": None, "team_id": None, "project_id": None, "size_bytes": 4},
        )
    ]


async def test_with_telemetry_async_extracts_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(tracker, "track", lambda event, **attrs: calls.append((event, attrs)))

    @tracker.with_telemetry("blob_put", extract_metadata=lambda size: {"size_bytes": size})
    async def upload(size: int) -> int:
        return size + 1

    assert await upload(4) == 5
    assert calls == [
        (
            "blob_put",
            {"token": None, "team_id": None, "project_id": None, "size_bytes": 4},
        )
    ]


def _explode_metadata() -> dict[str, Any]:
    raise RuntimeError("metadata failed")


def _explode_text() -> str | None:
    raise RuntimeError("extraction failed")


def test_with_telemetry_ignores_extractor_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(tracker, "track", lambda event, **attrs: calls.append((event, attrs)))

    @tracker.with_telemetry(
        "blob_put",
        extract_metadata=_explode_metadata,
        extract_token=_explode_text,
        extract_team_id=_explode_text,
        extract_project_id=_explode_text,
    )
    def upload() -> None:
        return None

    upload()

    assert calls == [("blob_put", {"token": None, "team_id": None, "project_id": None})]


def test_telemetry_captures_named_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(tracker, "track", lambda event, **attrs: calls.append((event, attrs)))

    @tracker.telemetry(
        "blob_delete",
        capture=["token"],
        derive={"count": lambda args, kwargs, result: len(result)},
    )
    def delete(urls: list[str], *, token: str | None = None) -> list[str]:
        return urls

    assert delete(["a", "b"], token="secret") == ["a", "b"]
    assert calls == [("blob_delete", {"token": "secret", "count": 2})]


def test_telemetry_ignores_derivation_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(tracker, "track", lambda event, **attrs: calls.append((event, attrs)))

    @tracker.telemetry("blob_delete", derive={"count": lambda args, kwargs, result: 1 / 0})
    def delete() -> None:
        return None

    delete()

    assert calls == [("blob_delete", {})]


def test_telemetry_can_emit_before_call(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(tracker, "track", lambda event, **attrs: calls.append((event, attrs)))

    @tracker.telemetry(
        "blob_put",
        derive={"size_bytes": lambda args, kwargs, result: result},
        when="before",
    )
    def upload() -> int:
        return 10

    assert upload() == 10
    assert calls == [("blob_put", {"size_bytes": None})]


async def test_telemetry_async_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(tracker, "track", lambda event, **attrs: calls.append((event, attrs)))

    @tracker.telemetry("blob_put", derive={"size_bytes": lambda args, kwargs, result: result})
    async def upload() -> int:
        return 10

    assert await upload() == 10
    assert calls == [("blob_put", {"size_bytes": 10})]
