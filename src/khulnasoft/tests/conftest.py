"""Shared fixtures for all tests."""

import os
import time
import uuid
from collections.abc import Generator

import pytest

pytest_plugins = ["vendor.respx.plugin"]


@pytest.fixture
def mock_env_clear(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Clear all Khulnasoft-related environment variables for testing.

    This ensures tests don't accidentally use real credentials from the environment.
    """
    env_vars_to_clear = [
        # General Khulnasoft
        "KHULNASOFT_TOKEN",
        "KHULNASOFT_TEAM_ID",
        "KHULNASOFT_PROJECT_ID",
        # Blob storage
        "BLOB_READ_WRITE_TOKEN",
        "BLOB_STORE_ID",
        # OIDC
        "KHULNASOFT_OIDC_TOKEN",
        "KHULNASOFT_OIDC_TOKEN_HEADER",
        # Cache
        "KHULNASOFT_CACHE_API_TOKEN",
        "KHULNASOFT_CACHE_API_URL",
        # Functions
        "KHULNASOFT_URL",
        "KHULNASOFT_ENV",
        "KHULNASOFT_REGION",
    ]
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    from khulnasoft.headers import set_headers
    from khulnasoft.oidc.token import _clear_cached_oidc_token

    set_headers(None)
    _clear_cached_oidc_token()
    yield
    _clear_cached_oidc_token()
    set_headers(None)


@pytest.fixture
def mock_token() -> str:
    """Mock Khulnasoft API token for testing."""
    return "test_token_123456789"


@pytest.fixture
def mock_team_id() -> str:
    """Mock Khulnasoft team ID for testing."""
    return "team_test123456789"


@pytest.fixture
def mock_project_id() -> str:
    """Mock Khulnasoft project ID for testing."""
    return "prj_test123456789"


@pytest.fixture
def mock_blob_token() -> str:
    """Mock blob storage token for testing."""
    return "khulnasoft_blob_rw_test_token_123456789"


@pytest.fixture
def unique_test_name() -> str:
    """Generate a unique test resource name with timestamp."""
    timestamp = int(time.time())
    unique_id = uuid.uuid4().hex[:8]
    return f"khulnasoft-py-test-{timestamp}-{unique_id}"


def has_khulnasoft_credentials() -> bool:
    """Check if Khulnasoft API credentials are available."""
    return bool(os.getenv("KHULNASOFT_TOKEN") and os.getenv("KHULNASOFT_TEAM_ID"))


def has_blob_credentials() -> bool:
    """Check if Blob storage credentials are available."""
    return bool(os.getenv("BLOB_READ_WRITE_TOKEN"))


# Skip markers for live tests
requires_khulnasoft_credentials = pytest.mark.skipif(
    not has_khulnasoft_credentials(),
    reason="Requires KHULNASOFT_TOKEN and KHULNASOFT_TEAM_ID environment variables",
)

requires_blob_credentials = pytest.mark.skipif(
    not has_blob_credentials(),
    reason="Requires BLOB_READ_WRITE_TOKEN environment variable",
)
