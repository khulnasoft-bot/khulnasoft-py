# `khulnasoft` — Python SDK (meta package)

`khulnasoft` is the umbrella Python SDK for KhulnaSoft services. It re-exports
and depends on all feature packages (blob, cache, cron, deployments, functions,
oidc, project_routes, projects, sandbox, workflow) and provides grouped REST
clients, environment parsing, and a CLI entry point.

## Quick start

```python
from khulnasoft.client import Khulnasoft, AsyncKhulnasoft

client = Khulnasoft(access_token="...")
projects = client.projects.list()
```

Or use individual feature packages directly:

```python
import khulnasoft.blob as blob
import khulnasoft.cache as cache
```

## Package layout

```
src/khulnasoft/
├── __main__.py          # CLI entry point (delegates to npx khulnasoft)
├── client.py            # Khulnasoft / AsyncKhulnasoft grouped clients
├── env.py               # Env dataclass and get_env()
├── version.py           # Version string
├── ai/                  # AI agents & models (see docs/ai/)
├── blob/                # Blob storage client
├── cache/               # Runtime cache (re-exports khulnasoft.cache)
├── cron/                # Cron schedule helpers
├── deployments/         # Deployment creation and file upload
├── functions/           # Convenience exports (cache, env, headers, deadline, wait_until)
├── project_routes/      # Project-level routing rules
├── projects/            # Project CRUD
└── _internal/           # Shared implementation details (not public API)
```

## Key modules

### `client.py` — Grouped REST clients

| Class | Purpose |
|-------|---------|
| `Khulnasoft` | Sync grouped client: `.deployments`, `.projects`, `.project_routes` |
| `AsyncKhulnasoft` | Async grouped client |

```python
from khulnasoft.client import AsyncKhulnasoft

async with AsyncKhulnasoft(access_token="...") as client:
    projects = await client.projects.list()
```

### `env.py` — Environment parsing

| Symbol | Purpose |
|--------|---------|
| `Env` | Dataclass of `KHULNASOFT_*` environment variables |
| `get_env()` | Parse environment into an `Env` |

```python
from khulnasoft.env import get_env

env = get_env()
print(env.KHULNASOFT_URL)
print(env.KHULNASOFT_GIT_COMMIT_SHA)
```

### Subpackages

| Subpackage | Purpose | Docs |
|------------|---------|------|
| `ai/` | AI agents, models, tools, streaming, telemetry | [`docs/ai/`](../ai/) |
| `blob/` | Blob storage — upload, download, list, copy, delete, multipart | [`docs/blob/`](../blob/) |
| `cache/` | Runtime cache with tag-based invalidation | [`docs/cache/`](../cache/) |
| `cron/` | Cron schedule helpers (`CronTab`, `cron` decorator) | [`docs/cron/`](../cron/) |
| `deployments/` | Deployment creation and file upload | [`docs/deployments/`](../deployments/) |
| `functions/` | Convenience exports (cache, env, headers, deadline, wait_until) | [`docs/functions/`](../functions/) |
| `project_routes/` | Project-level routing rules | [`docs/project_routes/`](../project_routes/) |
| `projects/` | Project CRUD | [`docs/projects/`](../projects/) |
| `_internal/` | Shared implementation details (not public API) | — |

## Requirements

Python 3.10 or later. See [`pyproject.toml`](../../pyproject.toml) for the full dependency list.

## Related

- [`AI_REFACTORING_PLAN.md`](../../AI_REFACTORING_PLAN.md) — refactoring plan for `khulnasoft.ai`
