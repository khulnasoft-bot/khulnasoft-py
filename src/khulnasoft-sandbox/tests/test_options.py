from datetime import timedelta
from types import SimpleNamespace

import httpx2 as httpx
import pytest

import vendor.respx as respx
from khulnasoft import sandbox
from khulnasoft.sandbox._internal.options import (
    SandboxCredentials,
    SandboxServiceOptions,
)


def test_options_resolves_region_from_argument_or_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("KHULNASOFT_REGION", raising=False)
    assert SandboxServiceOptions().region is None

    monkeypatch.setenv("KHULNASOFT_REGION", "iad1")
    assert SandboxServiceOptions().region == "iad1"
    assert SandboxServiceOptions(region="sfo1").region == "sfo1"
    assert sandbox.sync.SandboxServiceOptions().region == "iad1"
    assert sandbox.sync.SandboxServiceOptions(region="cle1").region == "cle1"

    monkeypatch.setenv("KHULNASOFT_REGION", "")
    assert SandboxServiceOptions().region is None
    assert sandbox.sync.SandboxServiceOptions().region is None


def test_options_equality_preserves_custom_credential_factory_identity() -> None:
    assert SandboxServiceOptions() == SandboxServiceOptions()
    assert SandboxServiceOptions(
        base_url="https://example.com",
        file_transfer_timeout=timedelta(seconds=30),
    ) == SandboxServiceOptions(
        base_url="https://example.com",
        file_transfer_timeout=timedelta(seconds=30),
    )

    async def first_factory() -> SandboxCredentials:
        return SandboxCredentials("token", "team", "project")

    async def second_factory() -> SandboxCredentials:
        return SandboxCredentials("token", "team", "project")

    assert SandboxServiceOptions(credentials_factory=first_factory) != SandboxServiceOptions(
        credentials_factory=second_factory
    )


@respx.mock
@pytest.mark.asyncio
async def test_public_request_uses_default_oidc_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from khulnasoft.oidc import credentials

    monkeypatch.setattr(
        credentials,
        "get_credentials",
        lambda: SimpleNamespace(token="token", team_id="team_123", project_id="prj_123"),
    )
    route = respx.get("https://khulnasoft.com/api/v2/sandboxes/snapshots/snap_123").mock(
        return_value=httpx.Response(
            200,
            json={
                "snapshot": {
                    "id": "snap_123",
                    "sourceSessionId": "sbx_123",
                    "region": "iad1",
                    "status": "created",
                    "sizeBytes": 1024,
                    "createdAt": 1,
                    "updatedAt": 2,
                }
            },
        )
    )

    snapshot = await sandbox.get_snapshot(snapshot_id="snap_123")

    assert snapshot.id == "snap_123"
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer token"
    assert request.url.params["teamId"] == "team_123"
