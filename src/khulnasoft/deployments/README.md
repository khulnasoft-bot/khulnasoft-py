# Deployments

`khulnasoft.deployments` provides helpers for Khulnasoft deployment creation and
deployment file uploads.

For deployment request bodies and product behavior, see the official
[Khulnasoft deployments docs](https://khulnasoft.com/docs).

## Credentials

Grouped deployment clients use `KHULNASOFT_TOKEN` by default. Pass
`access_token=get_credentials().token` or another explicit token to `Khulnasoft` /
`AsyncKhulnasoft` when you want to authenticate with OIDC-derived credentials.

## Async Client

```python
from khulnasoft.client import AsyncKhulnasoft


async def main() -> None:
    khulnasoft = AsyncKhulnasoft()
    result = await khulnasoft.deployments.create_deployment(
        body={
            "name": "my-site",
            "project": "my-site",
            "target": "preview",
            "files": [],
        }
    )
```

```python
from khulnasoft.client import AsyncKhulnasoft


async def upload(content: bytes, digest: str) -> dict:
    khulnasoft = AsyncKhulnasoft()
    return await khulnasoft.deployments.upload_file(
        content=content,
        content_length=len(content),
        x_khulnasoft_digest=digest,
    )
```

Use sync functions in `khulnasoft.deployments` or `Khulnasoft().deployments` for
synchronous code.
