"""Shared fixtures for standalone Sandbox tests."""

from collections.abc import Generator

import pytest

pytest_plugins = ["vendor.respx.plugin"]


@pytest.fixture
def mock_env_clear(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Prevent tests from resolving credentials from the developer environment."""
    for name in (
        "KHULNASOFT_TOKEN",
        "KHULNASOFT_TEAM_ID",
        "KHULNASOFT_PROJECT_ID",
        "KHULNASOFT_OIDC_TOKEN",
        "KHULNASOFT_OIDC_TOKEN_HEADER",
        "KHULNASOFT_REGION",
    ):
        monkeypatch.delenv(name, raising=False)

    from khulnasoft.oidc.token import _clear_cached_oidc_token

    _clear_cached_oidc_token()
    yield
    _clear_cached_oidc_token()
