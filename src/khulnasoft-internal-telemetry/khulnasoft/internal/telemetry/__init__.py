"""Internal telemetry functionality for Khulnasoft Python packages."""

from khulnasoft.internal.telemetry.client import TelemetryClient
from khulnasoft.internal.telemetry.tracker import track

__all__ = ["TelemetryClient", "track"]
