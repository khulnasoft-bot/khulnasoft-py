# KhulnaSoft Python SDK — Documentation

This documentation covers all packages in the KhulnaSoft Python SDK monorepo.

## Packages

| Package | Name | Description |
|---------|------|-------------|
| [`khulnasoft`](khulnasoft/) | `khulnasoft` | Umbrella SDK — blob, cache, cron, deployments, functions, oidc, project_routes, projects, sandbox, workflow |
| [`khulnasoft-ai`](ai/) | `khulnasoft.ai` | AI agents, models, tools, streaming, and telemetry |
| [`khulnasoft-blob`](blob/) | `khulnasoft-blob` | Async and sync object operations for Blob storage |
| [`khulnasoft-cache`](cache/) | `khulnasoft-cache` | Runtime cache helpers with tag-based invalidation |
| [`khulnasoft-connect`](connect/) | `khulnasoft-connect` | Credential broker SDK for third-party APIs |
| [`khulnasoft-headers`](headers/) | `khulnasoft-headers` | Request header helpers (IP, geolocation) |
| [`khulnasoft-internal-core`](internal-core/) | `khulnasoft-internal-core` | Shared internal runtime (HTTP, session, errors) |
| [`khulnasoft-internal-telemetry`](internal-telemetry/) | `khulnasoft-internal-telemetry` | Internal telemetry helpers |
| [`khulnasoft-oidc`](oidc/) | `khulnasoft-oidc` | OIDC helpers (token retrieval, decode, verify) |
| [`khulnasoft-queue`](queue/) | `khulnasoft-queue` | Queue client — send, subscribe, poll messages |
| [`khulnasoft-sandbox`](sandbox/) | `khulnasoft-sandbox` | Sandbox SDK — create and manage sandboxes |
| [`khulnasoft-workflow`](workflow/) | `khulnasoft-workflow` | Workflows SDK — workflow registration and execution |

## Installation

```bash
pip install khulnasoft
```

Or install individual packages:

```bash
pip install khulnasoft-ai khulnasoft-blob khulnasoft-cache
```

## Requirements

Python 3.10 or later (Python 3.12+ for `khulnasoft.ai` due to PEP 695 syntax).

## Development

- Install dependencies and run the canonical checks:
```bash
uv sync --all-packages
uv run poe qa
```
- Build every workspace package:
```bash
uv build --all-packages --no-sources
```

## Repository layout

- `src/khulnasoft/` — Meta package
- `src/khulnasoft-*/` — Feature packages (cache, connect, headers, etc.)
- `integrations/` — Framework integrations (apscheduler, celery, django-tasks, dramatiq)
- `examples/` — Example applications
- `scripts/` — Workspace tooling (PoE tasks, hatch build, etc.)

## License

MIT
