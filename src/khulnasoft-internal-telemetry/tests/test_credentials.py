from __future__ import annotations

import pytest

from khulnasoft.internal.telemetry import credentials as credentials_module
from khulnasoft.internal.telemetry.credentials import extract_credentials


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KHULNASOFT_PROJECT_ID", raising=False)
    monkeypatch.delenv("KHULNASOFT_TEAM_ID", raising=False)
    monkeypatch.setattr(credentials_module, "decode_oidc_payload", lambda token: {})
    monkeypatch.setattr(credentials_module, "find_project_info", lambda: {})


def test_explicit_values_take_priority() -> None:
    assert extract_credentials(user_id="user", team_id="team", project_id="project") == (
        "user",
        "team",
        "project",
    )


def test_environment_values_are_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KHULNASOFT_PROJECT_ID", "env-project")
    monkeypatch.setenv("KHULNASOFT_TEAM_ID", "env-team")

    assert extract_credentials() == (None, "env-team", "env-project")


def test_oidc_token_fills_missing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        credentials_module,
        "decode_oidc_payload",
        lambda token: {"project_id": "token-project", "owner_id": "token-team"},
    )

    assert extract_credentials(token="token") == (None, "token-team", "token-project")


def test_oidc_team_id_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        credentials_module,
        "decode_oidc_payload",
        lambda token: {"team_id": "token-team"},
    )

    assert extract_credentials(token="token") == (None, "token-team", None)


def test_project_info_fills_missing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        credentials_module,
        "find_project_info",
        lambda: {"projectId": "file-project", "teamId": "file-team"},
    )

    assert extract_credentials() == (None, "file-team", "file-project")


def test_invalid_token_falls_back_to_project_info(monkeypatch: pytest.MonkeyPatch) -> None:
    def invalid_token(token: str) -> None:
        raise ValueError("invalid token")

    monkeypatch.setattr(credentials_module, "decode_oidc_payload", invalid_token)
    monkeypatch.setattr(
        credentials_module,
        "find_project_info",
        lambda: {"projectId": "file-project"},
    )

    assert extract_credentials(token="token") == (None, None, "file-project")


def test_project_info_errors_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_project() -> None:
        raise FileNotFoundError(".khulnasoft/project.json")

    monkeypatch.setattr(credentials_module, "find_project_info", missing_project)

    assert extract_credentials() == (None, None, None)
