# `khulnasoft-cache` — Runtime cache

`khulnasoft-cache` provides runtime cache helpers for KhulnaSoft Python
applications — sync and async cache clients with tag-based invalidation,
falling back to an in-memory cache.

## Quick start

```python
import khulnasoft.cache as cache

# Get or create a cache client
client = cache.get_cache(namespace="my-app")

# Read / write
value = cache.get("key")
cache.set("key", {"hello": "world"}, ttl=60, tags=["demo"])
cache.delete("key")

# Tag-based invalidation
cache.invalidate_by_tag("demo")
```

Async variant:

```python
from khulnasoft.cache.aio import get_cache

async def main():
    client = await get_cache(namespace="my-app")
    await client.set("key", "value", ttl=60)
    value = await client.get("key")
```

## Package layout

```
src/khulnasoft-cache/khulnasoft/cache/
├── __init__.py          # Public API surface
├── runtime_cache.py     # RuntimeCache / AsyncRuntimeCache implementations
├── cache_build.py       # RuntimeCacheError exception
├── purge.py             # invalidate_by_tag, dangerously_delete_by_tag
├── aio.py               # Async cache entry point (get_cache)
├── cache_in_memory.py   # In-memory fallback cache implementation
├── context.py           # Cache context management
├── types.py             # Cache type definitions
├── utils.py             # Cache utility functions
└── version.py           # Version string
```

## Key modules

| Module | Purpose |
|--------|---------|
| `runtime_cache.py` | Core `RuntimeCache` / `AsyncRuntimeCache` implementations |
| `cache_build.py` | `RuntimeCacheError` exception |
| `purge.py` | `invalidate_by_tag`, `dangerously_delete_by_tag` |
| `aio.py` | Async cache entry point (`get_cache` for async) |
| `cache_in_memory.py` | In-memory fallback cache implementation |
| `context.py` | Cache context management |
| `types.py` | Cache type definitions |
| `utils.py` | Cache utility functions |
| `version.py` | Version string |

## Public API

| Symbol | Purpose |
|--------|---------|
| `RuntimeCache` | Sync runtime cache client |
| `AsyncRuntimeCache` | Async runtime cache client |
| `get_cache()` | Factory to obtain a sync cache client |
| `khulnasoft.cache.aio.get_cache()` | Factory to obtain an async cache client |
| `prime_runtime_cache()` | Pre-populate cache |
| `invalidate_by_tag()` | Invalidate cache entries by tag |
| `dangerously_delete_by_tag()` | Force-delete cache entries by tag |
| `RuntimeCacheError` | Cache exception |

## Usage example

```python
import khulnasoft.cache as cache

client = cache.get_cache(namespace="my-app", tags=["demo"])

# Set a value with a TTL and tags
cache.set("user:1", {"name": "Alice"}, ttl=300, tags=["demo", "user"])

# Get it back
user = cache.get("user:1")

# Invalidate everything tagged "demo"
cache.invalidate_by_tag("demo")

# Pre-populate multiple entries
cache.prime_runtime_cache({
    "a": 1,
    "b": 2,
}, ttl=60, tags=["init"])
```

## Requirements

Python 3.10 or later. Dependencies:
- `khulnasoft-headers`
- `khulnasoft-internal-telemetry`
- `httpx2`

## Related

- [`khulnasoft-headers`](../headers/) — request header helpers used by cache context
