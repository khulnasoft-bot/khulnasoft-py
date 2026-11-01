# OIDC

`khulnasoft.oidc` retrieves and decodes Khulnasoft OIDC tokens.

## Async Token Lookup

```python
from khulnasoft.oidc import decode_oidc_payload
from khulnasoft.headers import set_headers
from khulnasoft.oidc.aio import get_khulnasoft_oidc_token


async def main() -> None:
    token = await get_khulnasoft_oidc_token()
    payload = decode_oidc_payload(token)
    project_id = payload.get("project_id")
```

Token lookup prefers the `x-khulnasoft-oidc-token` request header registered with
`khulnasoft.headers.set_headers()`, then `KHULNASOFT_OIDC_TOKEN`. The compatibility
alias `khulnasoft.oidc.set_headers()` updates the same header context. In local development,
you can load a short-lived token dynamically:

```bash
KHULNASOFT_OIDC_TOKEN=$(vc project token some-project) some-command
```

Use `khulnasoft.oidc.get_khulnasoft_oidc_token()` for synchronous code.

## Verification

Requires the `verify` extra, which adds `pyjwt[crypto]`:

```bash
pip install "khulnasoft-oidc[verify]"
```

```python
from khulnasoft.oidc import extract_bearer_token, verify_khulnasoft_oidc_token

claims = verify_khulnasoft_oidc_token(extract_bearer_token(request.headers))
```

Verification allows only RS256, resolves the signing key by `kid` from Khulnasoft's
JWKS, and pins the issuer to Khulnasoft's OIDC service, which mints both
`https://oidc.khulnasoft.com` and the team-scoped `https://oidc.khulnasoft.com/<team>`.
It **fails closed**: when the expected project or environment cannot be resolved
from the arguments, `KHULNASOFT_PROJECT_ID`, or `KHULNASOFT_TARGET_ENV`/`KHULNASOFT_ENV`,
every token is rejected. `khulnasoft.oidc.aio.verify_khulnasoft_oidc_token()` is the
async twin.

## Token Identity

A token is a signature over an identity plus an expiry, so one identity is issued
many tokens over time. To key client-side state on the identity rather than on
the token, use:

```python
from khulnasoft.oidc import resolve_khulnasoft_oidc_token_identity

identity = resolve_khulnasoft_oidc_token_identity(token)  # stable across a refresh
```

The token is verified first — signature, issuer and expiry — and only then are its
identity claims reduced to an opaque digest that carries no credential and is safe
to log.

What it does **not** do is authorize: it returns no claims and does not check the
project, environment, owner or audience. Use `verify_khulnasoft_oidc_token()` for that.
