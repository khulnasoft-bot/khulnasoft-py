# `khulnasoft-internal-telemetry` — Internal telemetry helpers

`khulnasoft-internal-telemetry` provides internal telemetry helpers for
KhulnaSoft Python packages — telemetry client, credentials, and tracking
decorator.

## Quick start

```python
from khulnasoft.internal.telemetry import TelemetryClient, track

# Create a telemetry client
client = TelemetryClient()

# Track an event
await client.track("event.name", {"key": "value"})

# Or use the track decorator
@track("my_function")
async def my_function():
    ...
```

## Package layout

```
src/khulnasoft-internal-telemetry/khulnasoft/internal/telemetry/
├── __init__.py     # Public API: TelemetryClient, track
├── client.py       # TelemetryClient — sends telemetry events
├── credentials.py  # Telemetry credentials management
├── tracker.py      # track — tracking helper/decorator
└── version.py      # Version string
```

## Public API

| Symbol | Purpose |
|--------|---------|
| `TelemetryClient` | Telemetry client for reporting events |
| `track` | Tracking decorator/function |

## Requirements

Python 3.10 or later. Dependencies:
- `httpx2`
- `khulnasoft-oidc`

## Related

This package is an internal dependency and is not intended for direct
end-user installation.
