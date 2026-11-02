# Runtime Cache

`khulnasoft.cache` provides Runtime Cache clients and invalidation helpers for
Khulnasoft Functions.

## Async Client

```python
from khulnasoft.cache import AsyncRuntimeCache


async def main() -> None:
    cache = AsyncRuntimeCache(namespace="products")
    await cache.set("featured", ["sku_1", "sku_2"], {"ttl": 300, "tags": ["catalog"]})
    featured = await cache.get("featured")
    await cache.expire_tag("catalog")
```

Use `RuntimeCache` or `khulnasoft.cache.get_cache()` for synchronous code.
