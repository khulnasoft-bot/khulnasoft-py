# `khulnasoft.functions` — Functions convenience exports

`khulnasoft.functions` provides convenience exports aggregating cache, env,
headers, deadline, and wait_until functionality.

## Quick start

```python
from khulnasoft.functions import get_env, Env, ip_address, geolocation
from khulnasoft.functions import set_headers, get_headers
from khulnasoft.functions import get_cache, RuntimeCache, AsyncRuntimeCache
from khulnasoft.functions import wait_until, get_deadline

# Environment
env = get_env()
print(env.KHULNASOFT_URL)

# IP and geo
ip = ip_address(headers)
geo = geolocation(headers)

# Headers
set_headers({"x-real-ip": "203.0.113.5"})
headers = get_headers()

# Cache
client = get_cache(namespace="my-app")
cache.set("key", "value", ttl=60)

# Deadline and wait_until
deadline = get_deadline()
await wait_until(condition)
```

## Package layout

```
src/khulnasoft/functions/
├── __init__.py    # Public API: convenience re-exports
├── aio.py         # Async functions client
├── deadline.py    # get_deadline()
├── wait_until.py  # wait_until()
├── README.md
└── py.typed
```

## Public API

| Symbol | Source | Purpose |
|--------|--------|---------|
| `get_env`, `Env` | `khulnasoft.env` | Environment parsing |
| `ip_address`, `geolocation` | `khulnasoft.headers` | IP and geolocation |
| `Geo` | `khulnasoft.headers` | Geolocation TypedDict |
| `set_headers`, `get_headers` | `khulnasoft.headers` | Header context |
| `get_cache`, `RuntimeCache`, `AsyncRuntimeCache` | `khulnasoft.cache` | Runtime cache |
| `wait_until` | `khulnasoft.functions.wait_until` | Wait until condition |
| `get_deadline` | `khulnasoft.functions.deadline` | Get deadline |

## Requirements

Python 3.10 or later. Depends on `khulnasoft.cache`, `khulnasoft.env`, `khulnasoft.headers`.
