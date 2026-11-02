# `khulnasoft-headers` — Request header helpers

`khulnasoft-headers` provides request header helpers for KhulnaSoft Python
applications — stores request headers in a context variable, and exposes IP
address and geolocation helpers.

## Quick start

```python
from khulnasoft.headers import set_headers, get_headers, ip_address, geolocation

# Register request headers in context
set_headers({"x-real-ip": "203.0.113.5", "x-khulnasoft-ip-country": "US"})

# Read headers back
headers = get_headers()

# Extract client IP
ip = ip_address(headers)

# Extract geolocation
geo = geolocation(headers)
# geo = {
#   "city": "...",
#   "country": "...",
#   "flag": "🇺🇸",
#   "countryRegion": "...",
#   "region": "...",
#   "latitude": "...",
#   "longitude": "...",
#   "postalCode": "...",
# }
```

## ASGI / WSGI integration

```python
from khulnasoft.headers import headers_from_asgi_scope, headers_from_wsgi_environ, set_headers

# ASGI
headers = headers_from_asgi_scope(scope)
set_headers(headers)

# WSGI
headers = headers_from_wsgi_environ(environ)
set_headers(headers)
```

## HeadersContext — scoped header management

`HeadersContext` is an immutable snapshot of current headers that can be used
as a context manager or decorator to scope header lookups:

```python
from khulnasoft.headers import HeadersContext

ctx = HeadersContext(headers={"x-real-ip": "203.0.113.5"})

# As context manager
with ctx.use():
    ip = ip_address(ctx.headers)

# As decorator/runner
result = ctx.run(my_function, arg1, arg2)
```

## Package layout

```
src/khulnasoft-headers/khulnasoft/headers/
├── __init__.py   # Entire public API
└── version.py    # Version string
```

## Public API

| Symbol | Purpose |
|--------|---------|
| `set_headers(headers)` | Register request headers in context var |
| `get_headers()` | Retrieve registered headers |
| `HeadersContext` | Immutable snapshot of current headers (context manager + `run()`) |
| `ip_address(input)` | Extract client IP from headers/request-like object |
| `geolocation(request)` | Extract `Geo` dict (city, country, flag, region, lat/long, postalCode) |
| `headers_from_asgi_scope(scope)` | Decode headers from an ASGI scope |
| `headers_from_wsgi_environ(environ)` | Decode headers from a WSGI environ |
| `Geo` | TypedDict for geolocation data |
| `HeadersContext.use()` / `HeadersContext.run()` | Context manager / runner for header scoping |

## Header constants

| Constant | Header name |
|----------|-------------|
| `IP_HEADER_NAME` | `x-real-ip` |
| `CITY_HEADER_NAME` | `x-khulnasoft-ip-city` |
| `COUNTRY_HEADER_NAME` | `x-khulnasoft-ip-country` |
| `REGION_HEADER_NAME` | `x-khulnasoft-ip-country-region` |
| `LATITUDE_HEADER_NAME` | `x-khulnasoft-ip-latitude` |
| `LONGITUDE_HEADER_NAME` | `x-khulnasoft-ip-longitude` |
| `POSTAL_CODE_HEADER_NAME` | `x-khulnasoft-ip-postal-code` |
| `REQUEST_ID_HEADER_NAME` | `x-khulnasoft-id` |

## Requirements

Python 3.10 or later. No dependencies.

## Related

- [`khulnasoft-cache`](../cache/) — uses headers context for cache scoping
- [`khulnasoft-oidc`](../oidc/) — re-exports `set_headers`
