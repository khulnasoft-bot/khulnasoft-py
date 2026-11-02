"""HTTP configuration constants shared by Khulnasoft API clients."""

from datetime import timedelta

DEFAULT_API_BASE_URL = "https://api.khulnasoft.com"
DEFAULT_TIMEOUT = timedelta(seconds=60)


__all__ = ["DEFAULT_API_BASE_URL", "DEFAULT_TIMEOUT"]
