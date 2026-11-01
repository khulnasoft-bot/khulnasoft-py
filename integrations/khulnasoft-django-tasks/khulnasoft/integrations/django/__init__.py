"""Django task integration for Khulnasoft Queue Service."""

import sys

if sys.version_info >= (3, 12):
    pass
else:  # pragma: no cover - dependency marker mirrors this gate.
    raise RuntimeError(
        "khulnasoft.integrations.django requires Python 3.12 or newer because Django 6 "
        "does not support earlier Python versions."
    )

from ._backend import (
    KhulnasoftQueuesBackend,
    install_khulnasoft_django_task_integration,
)
from .version import __version__

__all__ = [
    "KhulnasoftQueuesBackend",
    "__version__",
    "install_khulnasoft_django_task_integration",
]
