"""Shared errors for Khulnasoft Python services."""


class KhulnasoftError(Exception):
    """Base error for Khulnasoft Python SDK failures."""


class KhulnasoftSessionError(KhulnasoftError):
    """Base error for SDK session failures."""


class KhulnasoftSessionClosedError(KhulnasoftSessionError):
    """Raised when code uses an SDK session after it has been closed."""


class KhulnasoftServiceOptionsError(KhulnasoftSessionError):
    """Raised when SDK session service options are invalid."""
