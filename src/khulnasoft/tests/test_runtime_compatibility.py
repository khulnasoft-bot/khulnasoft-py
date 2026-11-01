from datetime import timezone

from khulnasoft._internal.core.polyfills import UTC, Self, StrEnum


def test_internal_polyfills_expose_compatibility_surface() -> None:
    assert Self is not None
    assert issubclass(StrEnum, str)
    assert UTC is timezone.utc
