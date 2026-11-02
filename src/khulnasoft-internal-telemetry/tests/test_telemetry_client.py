from __future__ import annotations

from typing import Any

import pytest

from khulnasoft.internal.telemetry import client as client_module
from khulnasoft.internal.telemetry.client import TelemetryClient


@pytest.fixture
def enabled_client(monkeypatch: pytest.MonkeyPatch) -> TelemetryClient:
    monkeypatch.setattr(client_module, "_TELEMETRY_ENABLED", True)
    return TelemetryClient(session_id="session-1")


def test_track_whitelists_and_normalizes_fields(enabled_client: TelemetryClient) -> None:
    enabled_client.track(
        "blob_put",
        user_id="user-1",
        team_id="team-1",
        project_id="project-1",
        access="public",
        size_bytes=1024.0,
        unknown_field="ignored",
    )

    (event,) = enabled_client._events
    assert event["action"] == "blob_put"
    assert event["session_id"] == "session-1"
    assert event["user_id"] == "user-1"
    assert event["team_id"] == "team-1"
    assert event["project_id"] == "project-1"
    assert event["access"] == "public"
    assert event["size_bytes"] == 1024
    assert "unknown_field" not in event


def test_track_does_nothing_when_disabled() -> None:
    client = TelemetryClient()

    client._enabled = False
    client.track("cache_get", hit=True)

    assert client._events == []


def test_reset_clears_events(enabled_client: TelemetryClient) -> None:
    enabled_client.track("cache_get")
    enabled_client.reset()

    assert enabled_client._events == []


def test_flush_posts_batch_and_clears_events(
    enabled_client: TelemetryClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []

    class FakeResponse:
        status_code = 204

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> FakeResponse:
            calls.append({"url": url, "headers": headers, "json": json})
            return FakeResponse()

    monkeypatch.setattr(client_module.httpx, "Client", FakeClient)
    monkeypatch.setattr(client_module, "_TELEMETRY_BRIDGE_URL", "https://telemetry.test/events")

    enabled_client.track("cache_get", hit=True)
    enabled_client.track("blob_put", size_bytes=10)
    enabled_client.flush()

    assert enabled_client._events == []
    (call,) = calls
    assert call["url"] == "https://telemetry.test/events"
    assert call["headers"]["x-khulnasoft-py-session-id"] == "session-1"
    assert [event["action"] for event in call["json"]["generic"]] == ["cache_get", "blob_put"]


def test_flush_keeps_events_when_delivery_fails(
    enabled_client: TelemetryClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeResponse:
        status_code = 500

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, *args: object, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(client_module.httpx, "Client", FakeClient)

    enabled_client.track("cache_get")
    enabled_client.flush()

    assert len(enabled_client._events) == 1


def test_flush_is_a_noop_without_events(
    enabled_client: TelemetryClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("httpx.Client should not be constructed")

    monkeypatch.setattr(client_module.httpx, "Client", fail)

    enabled_client.flush()


def test_flush_swallows_transport_errors(
    enabled_client: TelemetryClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("network down")

    monkeypatch.setattr(client_module.httpx, "Client", FakeClient)

    enabled_client.track("cache_get")
    enabled_client.flush()

    assert len(enabled_client._events) == 1
