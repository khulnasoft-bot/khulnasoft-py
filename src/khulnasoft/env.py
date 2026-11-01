from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass

__all__ = ["Env", "get_env"]


@dataclass(frozen=True)
class Env:
    KHULNASOFT: str | None = None
    CI: str | None = None
    KHULNASOFT_ENV: str | None = None
    KHULNASOFT_URL: str | None = None
    KHULNASOFT_BRANCH_URL: str | None = None
    KHULNASOFT_PROJECT_PRODUCTION_URL: str | None = None
    KHULNASOFT_REGION: str | None = None
    KHULNASOFT_DEPLOYMENT_ID: str | None = None
    KHULNASOFT_SKEW_PROTECTION_ENABLED: str | None = None
    KHULNASOFT_AUTOMATION_BYPASS_SECRET: str | None = None
    KHULNASOFT_GIT_PROVIDER: str | None = None
    KHULNASOFT_GIT_REPO_SLUG: str | None = None
    KHULNASOFT_GIT_REPO_OWNER: str | None = None
    KHULNASOFT_GIT_REPO_ID: str | None = None
    KHULNASOFT_GIT_COMMIT_REF: str | None = None
    KHULNASOFT_GIT_COMMIT_SHA: str | None = None
    KHULNASOFT_GIT_COMMIT_MESSAGE: str | None = None
    KHULNASOFT_GIT_COMMIT_AUTHOR_LOGIN: str | None = None
    KHULNASOFT_GIT_COMMIT_AUTHOR_NAME: str | None = None
    KHULNASOFT_GIT_PREVIOUS_SHA: str | None = None
    KHULNASOFT_GIT_PULL_REQUEST_ID: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)

    def __getitem__(self, key: str) -> str | None:
        try:
            return getattr(self, key)
        except AttributeError as exc:
            raise KeyError(key) from exc

    def get(self, key: str, default: str | None = None) -> str | None:
        return getattr(self, key, default)


def _get(env: Mapping[str, str], key: str) -> str | None:
    value = env.get(key)
    if value == "":
        return None
    return value


def get_env(env: Mapping[str, str] | None = None) -> Env:
    """Return Khulnasoft system environment variables.

    Empty strings are normalized to ``None``. Returns an immutable ``Env``
    dataclass that supports both attribute access (e.g. ``ev.KHULNASOFT_URL``)
    and mapping-like access (e.g. ``ev["KHULNASOFT_URL"]``).
    """
    if env is None:
        env = os.environ

    return Env(
        KHULNASOFT=_get(env, "KHULNASOFT"),
        CI=_get(env, "CI"),
        KHULNASOFT_ENV=_get(env, "KHULNASOFT_ENV"),
        KHULNASOFT_URL=_get(env, "KHULNASOFT_URL"),
        KHULNASOFT_BRANCH_URL=_get(env, "KHULNASOFT_BRANCH_URL"),
        KHULNASOFT_PROJECT_PRODUCTION_URL=_get(env, "KHULNASOFT_PROJECT_PRODUCTION_URL"),
        KHULNASOFT_REGION=_get(env, "KHULNASOFT_REGION"),
        KHULNASOFT_DEPLOYMENT_ID=_get(env, "KHULNASOFT_DEPLOYMENT_ID"),
        KHULNASOFT_SKEW_PROTECTION_ENABLED=_get(env, "KHULNASOFT_SKEW_PROTECTION_ENABLED"),
        KHULNASOFT_AUTOMATION_BYPASS_SECRET=_get(env, "KHULNASOFT_AUTOMATION_BYPASS_SECRET"),
        KHULNASOFT_GIT_PROVIDER=_get(env, "KHULNASOFT_GIT_PROVIDER"),
        KHULNASOFT_GIT_REPO_SLUG=_get(env, "KHULNASOFT_GIT_REPO_SLUG"),
        KHULNASOFT_GIT_REPO_OWNER=_get(env, "KHULNASOFT_GIT_REPO_OWNER"),
        KHULNASOFT_GIT_REPO_ID=_get(env, "KHULNASOFT_GIT_REPO_ID"),
        KHULNASOFT_GIT_COMMIT_REF=_get(env, "KHULNASOFT_GIT_COMMIT_REF"),
        KHULNASOFT_GIT_COMMIT_SHA=_get(env, "KHULNASOFT_GIT_COMMIT_SHA"),
        KHULNASOFT_GIT_COMMIT_MESSAGE=_get(env, "KHULNASOFT_GIT_COMMIT_MESSAGE"),
        KHULNASOFT_GIT_COMMIT_AUTHOR_LOGIN=_get(env, "KHULNASOFT_GIT_COMMIT_AUTHOR_LOGIN"),
        KHULNASOFT_GIT_COMMIT_AUTHOR_NAME=_get(env, "KHULNASOFT_GIT_COMMIT_AUTHOR_NAME"),
        KHULNASOFT_GIT_PREVIOUS_SHA=_get(env, "KHULNASOFT_GIT_PREVIOUS_SHA"),
        KHULNASOFT_GIT_PULL_REQUEST_ID=_get(env, "KHULNASOFT_GIT_PULL_REQUEST_ID"),
    )
