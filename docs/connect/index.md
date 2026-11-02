# `khulnasoft-connect` — Credential broker SDK

`khulnasoft-connect` is the Python SDK for KhulnaSoft Connect — a credential
broker for third-party APIs. Your deployment proves which project and
environment it is with the Khulnasoft OIDC token the platform injects, and
Connect returns a short-lived credential for a third-party service. Your
project never stores provider secrets, and Connect owns OAuth client
registration, PKCE, state, refresh, and revocation server-side.

A connector must be attached to your project for the target environment before
any of these calls succeed.

## Quick start

```python
from khulnasoft.connect import get_token, get_connector_metadata

# Mint a short-lived upstream credential
token_response = await get_token("my-connector", scopes=["read"])

# Get connector metadata
metadata = await get_connector_metadata("my-connector")
print(metadata.name)
```

Start an end-user authorization flow:

```python
from khulnasoft.connect import start_authorization

result = await start_authorization("my-connector", redirect_uri="https://my-app.com/callback")
# result.consent_url -> URL to send the user to for consent
# or result.device_code -> device code for device flow
```

Verify an inbound Connect trigger webhook:

```python
from khulnasoft.connect import verify_connect_webhook

claims = await verify_connect_webhook(headers, body)
print(claims.subject)
```

Sync variant:

```python
from khulnasoft.connect.sync import get_token

token_response = get_token("my-connector", scopes=["read"])
```

## Package layout

```
src/khulnasoft-connect/khulnasoft/connect/
├── __init__.py      # Public API surface (async)
├── sync.py          # Synchronous mirror of all async functions
├── version.py       # Version string
└── _internal/
    ├── __init__.py
    ├── api_client.py       # HTTP API client
    ├── async_runtime.py    # Async runtime implementations
    ├── base.py             # Base classes
    ├── cache.py            # Token caching
    ├── errors.py           # All Connect error types
    ├── identity.py         # Identity/claims handling
    ├── models.py           # Pydantic models (subjects, tokens, responses)
    ├── options.py          # ConnectOptions, ConnectServiceOptions
    ├── service.py          # ConnectService, get_connect_service
    ├── single_flight.py    # Single-flight request deduplication
    ├── state.py            # Shared state management
    └── sync_runtime.py     # Sync runtime implementations
```

## Public API

### Functions

| Symbol | Purpose |
|--------|---------|
| `get_token(subject, ...)` | Mint a short-lived upstream credential (async) |
| `get_token_response(subject, ...)` | Get full token response (async) |
| `revoke_token(subject, ...)` | Revoke a token (async) |
| `start_authorization(subject, ...)` | Start end-user consent flow (async) |
| `get_connector_metadata(connector)` | Get connector metadata (async) |
| `verify_connect_webhook(headers, body)` | Verify Connect trigger webhook (async) |
| `delete_token_cache_entry(subject)` | Delete cached token (async) |
| `clear_token_cache()` | Clear all cached tokens (async) |
| `get_connect_service()` | Get the Connect service instance |

### Sync variants (in `khulnasoft.connect.sync`)

All async functions have synchronous equivalents in the `sync` submodule.

### Types

| Type | Purpose |
|------|---------|
| `ConnectAppTokenSubject` | App-level token subject |
| `ConnectUserTokenSubject` | User-level token subject |
| `ConnectJwtBearerTokenSubject` | JWT bearer token subject |
| `ConnectTokenExchangeSubject` | Token exchange subject |
| `ConnectTokenSubject` | Base token subject |
| `ConnectAuthorizationDetail` | Authorization detail |
| `ConnectAuthorizationResponse` | Authorization response |
| `ConnectCustomAuthorizationDetail` | Custom authorization detail |
| `ConnectGitHubAppInstallationAuthorizationDetail` | GitHub App installation detail |
| `ConnectorMetadata` | Connector metadata |
| `ConnectorRef` | Connector reference |
| `ConnectTokenResponse` | Token response |
| `ConnectWebhookClaims` | Webhook claims |
| `ConnectOptions` | Connect options |
| `ConnectServiceOptions` | Advanced service configuration |
| `KhulnasoftTokenInput` | Khulnasoft token input |
| `DurationInput` | Duration input |
| `StringContainer` | String container |

## Errors

| Exception | Purpose |
|-----------|---------|
| `ConnectError` | Base Connect error |
| `ConnectApiError` | API error |
| `ConnectCredentialsError` | Credentials error |
| `ConnectResponseError` | Response error |
| `ConnectValidationError` | Validation error |
| `ConnectWebhookVerificationError` | Webhook verification error |
| `ConnectNotFoundError` | Not found error |
| `AuthorizationDeniedError` | Authorization denied |
| `AuthorizationExpiredError` | Authorization expired |
| `AuthorizationPendingError` | Authorization pending |
| `UserAuthorizationRequiredError` | User authorization required |
| `ConnectorInstallationRequiredError` | Connector installation required |
| `InvalidGrantError` | Invalid grant |
| `NoValidTokenError` | No valid token |

## Requirements

Python 3.10 or later. Dependencies:
- `khulnasoft-internal-core`
- `khulnasoft-oidc[verify]`
- `httpx2`
- `pydantic`

## Related

- [`khulnasoft-oidc`](../oidc/) — Connect uses OIDC tokens for authentication
- [`khulnasoft-headers`](../headers/) — header helpers used by Connect
