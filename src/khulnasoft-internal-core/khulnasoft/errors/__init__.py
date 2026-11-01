"""Public shared error types."""

from khulnasoft._internal.core.errors import (
    KhulnasoftError,
    KhulnasoftServiceOptionsError,
    KhulnasoftSessionClosedError,
    KhulnasoftSessionError,
)

__all__ = [
    "KhulnasoftError",
    "KhulnasoftServiceOptionsError",
    "KhulnasoftSessionClosedError",
    "KhulnasoftSessionError",
]
