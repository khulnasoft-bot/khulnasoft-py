"""KhulnaSoft AI Gateway client error hierarchy.

Maps HTTP error responses from the gateway server to typed Python exceptions.
Each error class corresponds to a specific ``error.type`` value in the
gateway's JSON error response format::

    {
      "error": {
        "message": "...",
        "type": "authentication_error" | "invalid_request_error" | ...,
        "param": ...,
        "code": ...
      },
      "generationId": "..."
    }
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from ._client import AuthMethod

_KEY_URL = "https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai%2Fapi-keys"


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class GatewayError(Exception):
    """Base class for all KhulnaSoft AI Gateway client errors."""

    type: str | None = "gateway_error"
    status_code: int
    generation_id: str | None
    is_retryable: bool
    response_body: Any = None
    """Full HTTP error response body from the gateway (parsed JSON when
    possible, else the raw text).

    The gateway includes provider routing/fallback details here -- which
    backends it tried and how each one failed -- so the whole body is
    retained rather than just the extracted ``message``/``type``.
    """

    def __init__(
        self,
        message: str = "",
        *,
        status_code: int = 500,
        generation_id: str | None = None,
        is_retryable: bool | None = None,
        response_body: Any = None,
    ) -> None:
        display = f"{message} [{generation_id}]" if generation_id else message
        super().__init__(display)
        self.message = display
        self.status_code = status_code
        self.generation_id = generation_id
        self.response_body = response_body
        self.is_retryable = (
            status_code in {408, 409, 429} or status_code >= 500
            if is_retryable is None
            else is_retryable
        )


# ---------------------------------------------------------------------------
# Concrete errors — thin subclasses that set type + default status_code
# ---------------------------------------------------------------------------


class GatewayAuthenticationError(GatewayError):
    """Authentication failed (HTTP 401)."""

    type: str | None = "authentication_error"

    def __init__(
        self,
        message: str = "Authentication failed",
        *,
        status_code: int = 401,
        generation_id: str | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            generation_id=generation_id,
        )

    @classmethod
    def create_contextual(
        cls,
        *,
        auth_method: AuthMethod | None,
        status_code: int = 401,
        generation_id: str | None = None,
    ) -> Self:
        if auth_method is None:
            message = "No authentication method configured"
        else:
            message = f"Authentication failed using {auth_method!r}"
        return cls(
            message=message,
            status_code=status_code,
            generation_id=generation_id,
        )

