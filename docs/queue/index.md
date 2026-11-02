# `khulnasoft-queue` — Queue client

`khulnasoft-queue` is the KhulnaSoft Queue client for Python — send, subscribe,
and poll messages with sync/async clients, typed payloads, custom transports,
and a local dev server.

## Quick start

```python
import khulnasoft.queue as queue

# Send a message
await queue.send("my-topic", {"hello": "world"})

# Subscribe to a topic
@queue.subscribe(topic="my-topic")
async def handler(message):
    print(message.payload)

# Poll for messages
async for message in queue.poll("my-topic"):
    print(message.payload)
    break

# Poll and handle automatically
await queue.poll_and_handle(handler, topic="my-topic")
```

Sync variant:

```python
from khulnasoft.queue.sync import send

send("my-topic", {"hello": "world"})
```

## Package layout

```
src/khulnasoft-queue/khulnasoft/queue/
├── __init__.py       # Public API (re-exports from api_async + api_common)
├── __main__.py       # CLI/devserver entry point
├── sync.py           # Synchronous mirror of async API
├── embedded.py       # Embedded in-process queue service
├── devserver.py      # Standalone HTTP dev server
├── version.py        # Version string
├── testing/
│   ├── __init__.py   # Pytest plugin
│   ├── pytest.py     # Pytest fixtures
│   └── state.py      # Test state management
└── _internal/
    ├── __init__.py
    ├── api_async.py      # Async client API
    ├── api_sync.py       # Sync client API
    ├── api_common.py     # Shared types/constants
    ├── client.py         # QueueClient
    ├── client_sync.py    # SyncQueueClient
    ├── config.py         # Client configuration
    ├── constants.py      # Constants
    ├── errors.py         # All queue error types
    ├── http.py           # HTTP client
    ├── lease.py          # Message lease management
    ├── log.py            # Logging
    ├── messages.py       # Message[T] envelope types
    ├── multipart.py      # Multipart handling
    ├── names.py          # sanitize_name, SanitizedName
    ├── polling.py        # poll(), poll_and_handle()
    ├── push.py           # Push-mode subscriber handling
    ├── retry.py          # RetryAfter, retry logic
    ├── response.py       # Response handling
    ├── streams.py        # Stream handling
    ├── subscribers.py    # @subscribe decorator and registry
    ├── transports.py     # Message transports (JSON, text, bytes, streams)
    └── types.py          # Internal types
```

## Public API

### Core functions

| Symbol | Purpose |
|--------|---------|
| `send(topic, payload, ...)` | Publish a message |
| `subscribe(topic=...)` | Decorator to register message handlers |
| `poll(topic, ...)` | Manual polling iterator |
| `poll_and_handle(handler, ...)` | Automatic polling loop |

### Types

| Type | Purpose |
|------|---------|
| `Topic[T]` | Type-specialized topic for custom serialization |
| `Message[T]` | Typed message envelope |
| `QueueClient` | Async explicit client |
| `SyncQueueClient` | Sync explicit client |

### Transports

| Transport | Purpose |
|-----------|---------|
| `RawJsonTransport` | Raw JSON transport |
| `TypedJsonTransport` | Typed JSON transport |
| `ByteBufferTransport` | Byte buffer transport |
| `TextBufferTransport` | Text buffer transport |
| `ByteStreamTransport` | Byte stream transport |
| `TextStreamTransport` | Text stream transport |

### Local dev

| Symbol | Purpose |
|--------|---------|
| `embedded_queue_service()` | Local in-memory queue service |
| `devserver` | Standalone HTTP dev server (optional extra) |

## Errors

| Exception | Purpose |
|-----------|---------|
| `ServiceError` | Base service error |
| `BadRequestError` | 400 Bad Request |
| `UnauthorizedError` | 401 Unauthorized |
| `ForbiddenError` | 403 Forbidden |
| `InternalServerError` | 500 Internal Server Error |
| `DuplicateIdempotencyKeyError` | Duplicate idempotency key |
| `ConsumerDiscoveryError` | Consumer discovery failed |
| `ConsumerRegistryNotConfiguredError` | Consumer registry not configured |
| `DeploymentResolutionError` | Deployment resolution failed |
| `DuplicateSubscriptionError` | Duplicate subscription |
| `InvalidLimitError` | Invalid limit |
| `MessageAlreadyProcessedError` | Message already processed |
| `MessageCorruptedError` | Message corrupted |
| `MessageLockedError` | Message locked |
| `MessageNotFoundError` | Message not found |
| `MessageUnavailableError` | Message unavailable |
| `PayloadValidationError` | Payload validation failed |
| `ProtocolError` | Protocol error |
| `SubscriptionError` | Subscription error |
| `ThrottledError` | Throttled |
| `TokenResolutionError` | Token resolution failed |
| `UnhandledMessageError` | Unhandled message |
| `RetryAfter` | Raise from subscriber to control retry timing |

## Requirements

Python 3.10 or later. Dependencies:
- `anyio`
- `httpx2[http2]`
- `python-multipart`
- `typing_extensions`
- `khulnasoft-headers`
- `khulnasoft-internal-core`
- `khulnasoft-oidc`

Optional extras:
- `devserver` — `uvicorn`
- `typed` — `pydantic`
- `trio` — `anyio[trio]`

## Testing

The package includes a pytest plugin for queue testing:

```python
import pytest

@pytest.fixture
def queue_state():
    ...
```

Live tests (marked `live`) require KhulnaSoft Queue credentials and are
excluded by default:

```bash
uv run --python 3.10 -m pytest src/khulnasoft-queue/tests -m 'not live'
```

## Related

- [`khulnasoft-headers`](../headers/) — header helpers used by queue
- [`khulnasoft-internal-core`](../internal-core/) — shared runtime
