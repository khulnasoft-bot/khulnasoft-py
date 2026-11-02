"""Credential checks for live Sandbox tests."""

import os

import pytest


def has_sandbox_credentials() -> bool:
    """Return whether credentials needed by Sandbox live tests are present."""
    if os.getenv("KHULNASOFT_OIDC_TOKEN"):
        return True
    return bool(
        os.getenv("KHULNASOFT_TOKEN")
        and os.getenv("KHULNASOFT_TEAM_ID")
        and os.getenv("KHULNASOFT_PROJECT_ID")
    )


requires_sandbox_credentials = pytest.mark.skipif(
    not has_sandbox_credentials(),
    reason=(
        "Requires KHULNASOFT_OIDC_TOKEN, or KHULNASOFT_TOKEN plus KHULNASOFT_TEAM_ID "
        "and KHULNASOFT_PROJECT_ID for sandbox"
    ),
)
