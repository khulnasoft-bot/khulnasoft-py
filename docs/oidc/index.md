# `khulnasoft-oidc` — OIDC helpers

`khulnasoft-oidc` provides OIDC helpers for KhulnaSoft Python applications —
retrieves and decodes Khulnasoft OIDC tokens, with optional signature
verification.

## Quick start

```python
from khulnasoft.oidc import get_khulnasoft_oidc_token, decode_oidc_payload

# Get the OIDC token (prefers x-khulnasoft-oidc-token header, then env var)
token = get_khulnasoft_oidc_token()

# Decode the JWT payload without verification
payload = decode_oidc_payload(token)
print(payload.get("sub"))
print(payload.get("email"))
```

Sync variant:

```python
from khulnasoft.oidc import get_khulnasoft_oidc_token_sync

token = get_khulnasoft_oidc_token_sync()
```

Verify token signature (requires `verify` extra):

```python
from khulnasoft.oidc import verify_khulnasoft_oidc_token

# Verifies RS256 signature via JWKS, pins issuer, fails closed
payload = verify_khulnasoft_oidc_token(token)
```

Resolve stable token identity (useful across token refreshes):

```python
from khulnasoft.oidc import resolve_khulnasoft_oidc_token_identity

identity = resolve_khulnasoft_oidc_token_identity(token)
```

## Package layout

```
src/khulnasoft-oidc/khulnasoft/oidc/
├── __init__.py     # Public API surface
├── aio.py          # Async token lookup
├── token.py        # Token decoding, payload extraction, KhulnasoftOidcTokenError
├── verify.py       # Token signature verification (RS256, JWKS, issuer pinning)
├── credentials.py  # Credentials, get_credentials()
├── types.py        # OIDC type definitions
├── utils.py        # Utility functions
└── version.py      # Version string
```

## Public API

| Symbol | Purpose |
|--------|---------|
| `get_khulnasoft_oidc_token()` | Get OIDC token (async; prefers header, then env var) |
| `get_khulnasoft_oidc_token_sync()` | Get OIDC token (sync) |
| `decode_oidc_payload(token)` | Decode JWT payload without verification |
| `get_token_payload()` | Get token payload |
| `extract_bearer_token(headers)` | Extract bearer token from `Authorization` header |
| `verify_khulnasoft_oidc_token(token)` | Verify token signature (requires `verify` extra) |
| `resolve_khulnasoft_oidc_token_identity(token)` | Resolve stable token identity |
| `Credentials` | Credential management class |
| `get_credentials()` | Get credentials |
| `set_headers` | Re-exported from `khulnasoft.headers` |

## Errors

| Exception | Purpose |
|-----------|---------|
| `KhulnasoftOidcTokenError` | Base OIDC token error |
| `KhulnasoftOidcVerificationError` | Token verification failed |

## Installation with verification

```bash
pip install "khulnasoft-oidc[verify]"
```

The `verify` extra adds `pyjwt[crypto]` and `cryptography` for RS256 signature
verification via JWKS with issuer pinning.

## Requirements

Python 3.10 or later. Dependencies:
- `anyio`
- `httpx2`
- `khulnasoft-headers`

Optional (`verify` extra):
- `pyjwt[crypto]`
- `cryptography`

## Related

- [`khulnasoft-headers`](../headers/) — `set_headers` is re-exported here
- [`khulnasoft-connect`](../connect/) — uses OIDC tokens for credential brokerage
