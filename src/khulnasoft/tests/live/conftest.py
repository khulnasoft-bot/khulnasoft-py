"""Fixtures for live API tests.

These tests require real API credentials set via environment variables:
- KHULNASOFT_TOKEN or KHULNASOFT_OIDC_TOKEN: Khulnasoft API/OIDC token
- KHULNASOFT_TEAM_ID and KHULNASOFT_PROJECT_ID when using KHULNASOFT_TOKEN
- BLOB_READ_WRITE_TOKEN: Blob storage read/write token
"""

import os
import uuid
from collections.abc import Generator
from typing import Any

import pytest


def has_khulnasoft_credentials() -> bool:
    """Check if Khulnasoft API credentials are available."""
    return bool(
        (os.getenv("KHULNASOFT_TOKEN") or os.getenv("KHULNASOFT_OIDC_TOKEN"))
        and os.getenv("KHULNASOFT_TEAM_ID")
    )


def has_blob_credentials() -> bool:
    """Check if Blob storage credentials are available."""
    return bool(os.getenv("BLOB_READ_WRITE_TOKEN"))


# Skip markers for live tests
requires_khulnasoft_credentials = pytest.mark.skipif(
    not has_khulnasoft_credentials(),
    reason="Requires KHULNASOFT_TOKEN or KHULNASOFT_OIDC_TOKEN, plus KHULNASOFT_TEAM_ID",
)

requires_blob_credentials = pytest.mark.skipif(
    not has_blob_credentials(),
    reason="Requires BLOB_READ_WRITE_TOKEN environment variable",
)


@pytest.fixture
def khulnasoft_token() -> str:
    """Get Khulnasoft API or OIDC token from environment."""
    token = os.getenv("KHULNASOFT_TOKEN") or os.getenv("KHULNASOFT_OIDC_TOKEN")
    if not token:
        pytest.skip("KHULNASOFT_TOKEN or KHULNASOFT_OIDC_TOKEN environment variable not set")
    return token


@pytest.fixture
def khulnasoft_team_id() -> str:
    """Get Khulnasoft team ID from environment when provided."""
    team_id = os.getenv("KHULNASOFT_TEAM_ID")
    if not team_id and os.getenv("KHULNASOFT_TOKEN"):
        pytest.skip("KHULNASOFT_TEAM_ID environment variable not set")
    return team_id or ""


@pytest.fixture
def blob_token() -> str:
    """Get Blob storage token from environment."""
    token = os.getenv("BLOB_READ_WRITE_TOKEN")
    if not token:
        pytest.skip("BLOB_READ_WRITE_TOKEN environment variable not set")
    return token


@pytest.fixture
def unique_test_name() -> str:
    """Generate a collision-resistant test resource name.

    Format: khulnasoft-py-test-{uuid}
    """
    return f"khulnasoft-py-test-{uuid.uuid4().hex}"


@pytest.fixture
def unique_blob_path() -> str:
    """Generate a collision-resistant blob path for testing.

    Format: test/{uuid}/file.txt
    """
    return f"test/{uuid.uuid4().hex}/file.txt"


class CleanupRegistry:
    """Registry for tracking resources that need cleanup after tests."""

    def __init__(self) -> None:
        self._cleanups: list[tuple[str, Any]] = []

    def register(self, resource_type: str, resource_id: Any) -> None:
        """Register a resource for cleanup.

        Args:
            resource_type: Type of resource (e.g., "blob" or "project")
            resource_id: Identifier for the resource
        """
        self._cleanups.append((resource_type, resource_id))

    def get_resources(self, resource_type: str) -> list[Any]:
        """Get all registered resources of a specific type."""
        return [rid for rtype, rid in self._cleanups if rtype == resource_type]

    def clear(self) -> None:
        """Clear all registered resources."""
        self._cleanups.clear()


@pytest.fixture
def cleanup_registry() -> Generator[CleanupRegistry, None, None]:
    """Fixture providing a cleanup registry for tracking test resources.

    Usage:
        def test_create_resource(cleanup_registry, blob_token):
            result = put("test.txt", b"data", token=blob_token)
            cleanup_registry.register("blob", result.url)
            # Test continues...
            # Cleanup happens automatically after test
    """
    registry = CleanupRegistry()
    yield registry

    # Cleanup blob resources
    blob_urls = registry.get_resources("blob")
    if blob_urls:
        try:
            from khulnasoft.blob import delete

            blob_token = os.getenv("BLOB_READ_WRITE_TOKEN")
            if blob_token:
                for url in blob_urls:
                    try:
                        delete(url, token=blob_token)
                    except Exception:
                        pass  # Best effort cleanup
        except ImportError:
            pass

    # Cleanup project resources
    project_ids = registry.get_resources("project")
    if project_ids:
        try:
            from khulnasoft.projects import delete_project

            khulnasoft_token = os.getenv("KHULNASOFT_TOKEN") or os.getenv("KHULNASOFT_OIDC_TOKEN")
            team_id = os.getenv("KHULNASOFT_TEAM_ID")
            if khulnasoft_token and team_id:
                for project_id in project_ids:
                    try:
                        delete_project(project_id, token=khulnasoft_token, team_id=team_id)
                    except Exception:
                        pass  # Best effort cleanup
        except ImportError:
            pass

    registry.clear()
