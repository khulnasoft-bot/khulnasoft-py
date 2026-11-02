"""Connect service and per-call options."""

from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Annotated, TypeAlias

from pydantic import Field, field_validator

from khulnasoft._internal.core.http import DEFAULT_API_BASE_URL, DEFAULT_TIMEOUT
from khulnasoft._internal.core.options import ServiceOptions
from khulnasoft.connect._internal.base import ConnectModel, reject_bool
from khulnasoft.connect._internal.errors import ConnectCredentialsError
from khulnasoft.connect._internal.models import DurationInput

DEFAULT_CONNECT_API_BASE_URL = DEFAULT_API_BASE_URL
DEFAULT_VALIDITY_BUFFER = timedelta(seconds=30)
DEFAULT_TOKEN_CACHE_SIZE = 100

KhulnasoftTokenInput: TypeAlias = str | Callable[[], str | Awaitable[str]]
"""A platform identity token, or a callable resolving one at call time.

Prefer the callable form for anything long-lived: OIDC tokens are short-lived,
so a captured string goes stale.

A callable returning an awaitable is only usable from the async surface. The sync
surface steps its coroutine exactly once, so a callable that actually suspends —
one performing network I/O, for instance — cannot be resolved there. Supply a
plain synchronous callable when calling `khulnasoft.connect.sync`.
"""


ConnectCredentialsFactory: TypeAlias = Callable[[], Awaitable[str]]
"""Resolves the deployment's Khulnasoft OIDC token.

A callable rather than a `Protocol`, so it can be a validated field of
`ConnectServiceOptions`: pydantic cannot build a schema for a protocol.
"""


def _missing_token_error() -> ConnectCredentialsError:
    return ConnectCredentialsError(
        "no Khulnasoft OIDC token available; run `khulnasoft env pull` for local "
        "development, or pass options=ConnectOptions(khulnasoft_token=...)"
    )


async def _default_async_credentials_factory() -> str:
    """Resolve the deployment identity for an async session."""
    try:
        from khulnasoft.oidc.aio import get_khulnasoft_oidc_token

        token = await get_khulnasoft_oidc_token()
    except Exception as exc:
        raise ConnectCredentialsError(str(exc)) from exc

    if not token:
        raise _missing_token_error()
    return token


async def _default_sync_credentials_factory() -> str:
    """Resolve the deployment identity for a sync session.

    Declared async to satisfy the shared service, but deliberately calls the
    purely synchronous resolver: the sync surface is driven by `iter_coroutine`,
    which cannot tolerate a suspension. The async resolver awaits an HTTP refresh
    on the local-dev path, so using it here would fail exactly when a token needs
    refreshing. `khulnasoft-sandbox` makes the same choice for the same reason.
    """
    try:
        from khulnasoft.oidc import get_khulnasoft_oidc_token

        token = get_khulnasoft_oidc_token()
    except Exception as exc:
        raise ConnectCredentialsError(str(exc)) from exc

    if not token:
        raise _missing_token_error()
    return token


class ConnectServiceOptions(ServiceOptions, ConnectModel):
    """Configuration for `khulnasoft.connect` calls in an SDK session.

    A session that does not receive this option still constructs one with the
    default Connect API base URL and credential resolver. Supplying the option
    overrides the whole service configuration for that session scope. This is
    both the user configuration seam and the test seam.
    """

    base_url: str = DEFAULT_CONNECT_API_BASE_URL
    # `None` until the service picks the resolver matching the session mode.
    credentials_factory: ConnectCredentialsFactory | None = None
    timeout: Annotated[timedelta, Field(gt=timedelta(0))] = DEFAULT_TIMEOUT
    # A negative buffer would treat an already-expired token as still usable.
    validity_buffer: Annotated[timedelta, Field(ge=timedelta(0))] = DEFAULT_VALIDITY_BUFFER
    # Below one, eviction would pop from an empty mapping.
    token_cache_size: Annotated[int, Field(ge=1)] = DEFAULT_TOKEN_CACHE_SIZE


class ConnectOptions(ConnectModel):
    """Per-call overrides for a single Connect operation.

    Attributes:
        khulnasoft_token: Supply the platform identity yourself instead of resolving
            it from the environment. Accepts a string or a callable resolved at
            call time.
        force_refresh: Bypass the local token cache and re-validate upstream.
            Use this to surface a grant revoked elsewhere, and to poll a
            device-code authorization to completion.
        no_cache: Neither read from nor write to the local token cache.
        validity_buffer: Treat a cached token as stale this long before its
            expiry. Client-side read policy only; never sent to the server.
    """

    khulnasoft_token: KhulnasoftTokenInput | None = None
    force_refresh: bool = False
    no_cache: bool = False
    validity_buffer: DurationInput | None = None

    @field_validator("validity_buffer", mode="before")
    @classmethod
    def _check_validity_buffer(cls, value: object) -> object:
        return reject_bool(value)


__all__ = [
    "DEFAULT_CONNECT_API_BASE_URL",
    "DEFAULT_TOKEN_CACHE_SIZE",
    "DEFAULT_VALIDITY_BUFFER",
    "ConnectCredentialsFactory",
    "ConnectOptions",
    "ConnectServiceOptions",
    "KhulnasoftTokenInput",
]
