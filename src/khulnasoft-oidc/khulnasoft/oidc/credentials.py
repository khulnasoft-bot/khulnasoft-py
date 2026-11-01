from __future__ import annotations

import os

from .token import (
    KhulnasoftOidcTokenError,
    decode_oidc_payload,
    get_khulnasoft_oidc_token_from_context,
)
from .types import Credentials


def get_credentials(
    *,
    token: str | None = None,
    project_id: str | None = None,
    team_id: str | None = None,
) -> Credentials:
    if token and project_id and team_id:
        return Credentials(token=token, project_id=project_id, team_id=team_id)

    # Resolve OIDC token from request headers (set by the runtime) or env var.
    oidc: str | None = None
    try:
        oidc = get_khulnasoft_oidc_token_from_context()
    except KhulnasoftOidcTokenError:
        pass

    if oidc:
        project = os.getenv("KHULNASOFT_PROJECT_ID")
        team = os.getenv("KHULNASOFT_TEAM_ID")
        if not (project and team):
            try:
                payload = decode_oidc_payload(oidc)
                project = payload.get("project_id")
                team = payload.get("owner_id")
            except Exception:
                pass
        if project and team:
            return Credentials(token=oidc, project_id=project, team_id=team)
        raise RuntimeError(
            "OIDC token present but could not determine "
            "KHULNASOFT_PROJECT_ID and KHULNASOFT_TEAM_ID"
        )

    token = token or os.getenv("KHULNASOFT_TOKEN")
    project_id = project_id or os.getenv("KHULNASOFT_PROJECT_ID")
    team_id = team_id or os.getenv("KHULNASOFT_TEAM_ID")

    if token and project_id and team_id:
        return Credentials(token=token, project_id=project_id, team_id=team_id)

    raise RuntimeError(
        "Missing credentials. "
        "For local development, run 'khulnasoft link && khulnasoft env pull'. "
        "Otherwise, set KHULNASOFT_TOKEN, KHULNASOFT_PROJECT_ID, and KHULNASOFT_TEAM_ID."
    )
