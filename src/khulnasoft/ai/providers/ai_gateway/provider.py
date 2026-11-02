"""AI Gateway provider.

Defines the callable :data:`ai_gateway` provider.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Protocol, cast

import pydantic

from ... import errors as ai_errors
from .. import _optional, base
from . import client as gateway_client
from . import errors
from . import protocol as protocol_module
from .client import errors as client_errors

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Mapping, Sequence
    from types import ModuleType

    import httpx2 as httpx
    import modelsdotdev

    from ...models.core import model as model_
    from ...models.core import params as params_
    from ...types import events
    from ...types import messages as messages_
    from ...types import tools as tools_

_BASE_URL = "https://ai-gateway.vercel.sh/v4/ai"
_API_KEY_ENV = "AI_GATEWAY_API_KEY"
_KHULNASOFT_ENV = "KHULNASOFT"
_OIDC_TOKEN_ENV = "KHULNASOFT_OIDC_TOKEN"


class _KhulnasoftOidc(Protocol):
    def get_khulnasoft_oidc_token(self) -> str: ...


def _get_khulnasoft_oidc_token() -> str:
    try:
        oidc = cast(
            "_KhulnasoftOidc",
            _optional.import_optional_sdk(
                "khulnasoft.oidc",
                provider="AI Gateway OIDC",
                extra="khulnasoft",
            ),
        )
    except ai_errors.InstallationError as exc:
        raise ai_errors.InstallationError(
            "AI Gateway OIDC authentication requires the optional "
            "`khulnasoft-oidc` package. Install it with `pip install "
            '"ai[khulnasoft]"` or '
            '`uv add "ai[khulnasoft]"`, or set `AI_GATEWAY_API_KEY` to use '
            "API key authentication."
        ) from exc
    return oidc.get_khulnasoft_oidc_token()


class GatewayProvider(base.Provider[gateway_client.GatewayClient]):
    """Provider configuration for the KhulnaSoft AI Gateway."""

    handles: ClassVar[tuple[str, ...]] = ("khulnasoft", "@ai-sdk/gateway")

    provider_class_id: Literal["gateway"] = "gateway"
    name: Literal["ai-gateway"] = "ai-gateway"
    default_base_url: str = _BASE_URL
    api_key_env: str | None = _API_KEY_ENV

    _http_client: httpx.AsyncClient | None = pydantic.PrivateAttr(default=None)

    def _set_http_client(self, client: httpx.AsyncClient | None) -> None:
        self._http_client = client

    @property
    def client(self) -> gateway_client.GatewayClient:
        if self._client is None:
            self._set_client(
                gateway_client.GatewayClient(
                    base_url=self.base_url,
                    headers=self.headers,
                    client=self._http_client,
                )
            )
        client = super().client
        # only auth is refreshed per access: OIDC tokens rotate
        client.auth_token, client.auth_method = self._gateway_auth()
        return client

    def default_protocol(
        self,
    ) -> base.ProviderProtocol[gateway_client.GatewayClient]:
        """Return the default Gateway protocol."""
        return protocol_module.GatewayV4Protocol()

    def _gateway_auth(
        self,
    ) -> tuple[str | None, Literal["api-key", "oidc"] | None]:
        """Resolve ``(auth_token, auth_method)`` for this request.

        OIDC tokens rotate per access, so auth is resolved lazily on every
        client access. Falls back to API-key auth when an API key is
        configured, and to unauthenticated requests otherwise.
        """
        oidc_token = os.environ.get(_OIDC_TOKEN_ENV)
        if oidc_token:
            return oidc_token, "oidc"
        api_key = os.environ.get(_API_KEY_ENV)
        if api_key:
            return api_key, "api-key"
        return None, None

