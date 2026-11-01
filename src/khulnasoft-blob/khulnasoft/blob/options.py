from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from khulnasoft._internal.core.options import ServiceOptions

from .errors import BlobCredentialsError, CredentialKind
from .types import BlobCredentials


class BlobCredentialsFactory(Protocol):
    async def __call__(self) -> BlobCredentials: ...


class SyncBlobCredentialsFactory(Protocol):
    def __call__(self) -> BlobCredentials: ...


def _strip_store_prefix(store_id: str) -> str:
    return store_id.removeprefix("store_")


def _default_async_credentials() -> BlobCredentials:

    store_id = os.getenv("BLOB_STORE_ID", "")
    token = None
    try:
        from khulnasoft.oidc.credentials import get_khulnasoft_oidc_token_from_context

        token = get_khulnasoft_oidc_token_from_context()
    except Exception:  # noqa: BLE001
        token = os.getenv("KHULNASOFT_OIDC_TOKEN")
    if token and store_id:
        return BlobCredentials(
            token=token, store_id=_strip_store_prefix(store_id), kind=CredentialKind.OIDC
        )

    for env in ("BLOB_READ_WRITE_TOKEN", "KHULNASOFT_BLOB_READ_WRITE_TOKEN"):
        value = os.getenv(env)
        if value:
            from khulnasoft._internal.blob import extract_store_id_from_token

            return BlobCredentials(
                token=value,
                store_id=extract_store_id_from_token(value),
                kind=CredentialKind.TOKEN,
            )
    raise BlobCredentialsError("No blob credentials found")


async def _default_async_factory() -> BlobCredentials:
    return _default_async_credentials()


def _default_sync_credentials() -> BlobCredentials:
    return _default_async_credentials()


class _BlobServiceOptionsKey(ServiceOptions):
    __slots__ = ()

    @classmethod
    def service_options_key(cls) -> type[ServiceOptions]:
        return _BlobServiceOptionsKey


@dataclass(frozen=True, slots=True, init=False)
class BlobServiceOptions(_BlobServiceOptionsKey):
    base_url: str
    credentials_factory: BlobCredentialsFactory
    timeout: timedelta

    def __init__(
        self,
        *,
        base_url: str | None = None,
        credentials_factory: BlobCredentialsFactory | None = None,
        timeout: timedelta | None = None,
    ) -> None:
        from khulnasoft._internal.blob import get_api_url

        object.__setattr__(self, "base_url", base_url or get_api_url(""))
        object.__setattr__(
            self, "credentials_factory", credentials_factory or _default_async_factory
        )
        object.__setattr__(self, "timeout", timeout or timedelta(seconds=30))


@dataclass(frozen=True, slots=True, init=False)
class SyncBlobServiceOptions(_BlobServiceOptionsKey):
    base_url: str
    credentials_factory: SyncBlobCredentialsFactory
    timeout: timedelta

    def __init__(
        self,
        *,
        base_url: str | None = None,
        credentials_factory: SyncBlobCredentialsFactory | None = None,
        timeout: timedelta | None = None,
    ) -> None:
        from khulnasoft._internal.blob import get_api_url

        object.__setattr__(self, "base_url", base_url or get_api_url(""))
        object.__setattr__(
            self, "credentials_factory", credentials_factory or _default_sync_credentials
        )
        object.__setattr__(self, "timeout", timeout or timedelta(seconds=30))
