# `khulnasoft-internal-core` — Shared internal runtime

`khulnasoft-internal-core` is the shared internal runtime for KhulnaSoft
Python packages — HTTP transport (httpx2), session management, errors,
options, time, and URL utilities. Not intended for direct end-user
installation or imports.

## Package layout

```
src/khulnasoft-internal-core/khulnasoft/
├── api/__init__.py        # Public session context (session)
├── errors/__init__.py     # Shared exception types
├── _internal/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── session.py           # session context manager
│   │   ├── errors.py            # Core error classes
│   │   ├── options.py           # KhulnasoftServiceOptions
│   │   ├── time.py              # Time utilities
│   │   ├── url.py               # URL construction utilities
│   │   ├── typeutils.py         # Type utility helpers
│   │   ├── iter_coroutine.py    # Async iteration coroutine helpers
│   │   ├── byte_stream.py       # Byte stream handling
│   │   ├── version.py           # Version string
│   │   ├── http/
│   │   │   ├── __init__.py
│   │   │   ├── httpx.py         # httpx2-based HTTP client
│   │   │   ├── transport.py     # HTTP transport abstraction
│   │   │   ├── retry.py         # Retry logic
│   │   │   ├── config.py        # HTTP client config
│   │   │   └── _compat.py       # Legacy httpx compatibility
│   │   └── polyfills/
│   │       ├── __init__.py
│   │       ├── _datetime.py     # Datetime polyfills
│   │       ├── _strenum.py      # StrEnum polyfill
│   │       ├── _strenum_impl.py # StrEnum implementation
│   │       └── _typing.py       # Typing polyfills
│   └── ...
```

## Public API

### `khulnasoft.api`

| Symbol | Purpose |
|--------|---------|
| `session` | Ambient SDK session context manager |

### `khulnasoft.errors`

| Symbol | Purpose |
|--------|---------|
| `KhulnasoftError` | Base SDK error |
| `KhulnasoftSessionError` | Session error |
| `KhulnasoftSessionClosedError` | Session closed error |
| `KhulnasoftServiceOptionsError` | Service options error |

## Key modules

| Module | Purpose |
|--------|---------|
| `_internal/core/session.py` | `session()` — ambient SDK session context manager |
| `_internal/core/errors.py` | Core error classes |
| `_internal/core/options.py` | `KhulnasoftServiceOptions` — service configuration |
| `_internal/core/http/httpx.py` | httpx2-based HTTP client implementation |
| `_internal/core/http/transport.py` | HTTP transport abstraction |
| `_internal/core/http/retry.py` | Retry logic |
| `_internal/core/http/config.py` | HTTP client config |
| `_internal/core/http/_compat.py` | Legacy httpx compatibility |
| `_internal/core/time.py` | Time utilities |
| `_internal/core/url.py` | URL construction utilities |
| `_internal/core/typeutils.py` | Type utility helpers |
| `_internal/core/iter_coroutine.py` | Async iteration coroutine helpers |
| `_internal/core/byte_stream.py` | Byte stream handling |
| `_internal/core/polyfills/` | Python version polyfills |

## Requirements

Python 3.10 or later. Dependencies:
- `httpx2`
- `anyio`
- `typing-extensions` (<3.12)

## Related

This package is an internal dependency of all other `khulnasoft-*` packages and
is not intended for direct end-user use.
