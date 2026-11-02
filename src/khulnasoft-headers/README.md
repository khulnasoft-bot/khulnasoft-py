# Headers

`khulnasoft.headers` stores request headers for Khulnasoft Function helpers and exposes
IP address and geolocation helpers.

Register request headers once per request:

```python
from khulnasoft.headers import set_headers

set_headers(request.headers)
```

OIDC and cache helpers read the same registered header context.
