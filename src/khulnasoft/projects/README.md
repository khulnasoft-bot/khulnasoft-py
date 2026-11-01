# Projects

`khulnasoft.projects` provides helpers for listing, creating, updating, and deleting
Khulnasoft projects.

For project request bodies and product behavior, see the official
[Khulnasoft projects docs](https://khulnasoft.com/docs).

## Credentials

Grouped project clients use `KHULNASOFT_TOKEN` by default. Pass
`access_token=get_credentials().token` or another explicit token to `Khulnasoft` /
`AsyncKhulnasoft` when you want to authenticate with OIDC-derived credentials.

## Async Client

```python
from khulnasoft.client import AsyncKhulnasoft


async def main() -> None:
    khulnasoft = AsyncKhulnasoft()
    listing = await khulnasoft.projects.get_projects(query={"limit": 10})
    created = await khulnasoft.projects.create_project(body={"name": "my-site"})
    updated = await khulnasoft.projects.update_project(
        id_or_name=created["id"],
        body={"name": "my-renamed-site"},
    )
    await khulnasoft.projects.delete_project(id_or_name=updated["id"])
```

Use sync functions in `khulnasoft.projects` or `Khulnasoft().projects` for synchronous
code.
