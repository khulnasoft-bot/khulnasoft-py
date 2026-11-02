# `khulnasoft.project_routes` — Project-level routing rules

`khulnasoft.project_routes` provides project-level routing rule staging,
publishing, and history — clients and ops.

## Quick start

```python
from khulnasoft.project_routes import (
    AsyncProjectRoutesClient,
    ProjectRoutesClient,
    add_route,
    stage_routes,
    get_routes,
    ...
)

# Create a client
client = ProjectRoutesClient(access_token="...")

# Add a route
result = await add_route(...)

# Stage routes
await stage_routes(...)

# Get routes
routes = await get_routes(...)
```

## Package layout

```
src/khulnasoft/project_routes/
├── __init__.py        # Public API surface
├── aio.py             # Async client
├── client.py          # ProjectRoutesClient / AsyncProjectRoutesClient
├── errors.py          # ProjectRoutesError
├── ops.py             # Route operations (add, stage, get, edit, delete)
├── types.py           # Route types (ProjectRoute, RouteSpec, etc.)
├── README.md
└── py.typed
```

## Public API

### Clients

| Class | Purpose |
|-------|---------|
| `ProjectRoutesClient` | Sync project routes client |
| `AsyncProjectRoutesClient` | Async project routes client |

### Operations

| Symbol | Purpose |
|--------|---------|
| `add_route` / `add_route_async` | Add a route |
| `stage_routes` / `stage_routes_async` | Stage routes |
| `get_routes` / `get_routes_async` | Get routes |
| `edit_route` / `edit_route_async` | Edit a route |
| `delete_routes` / `delete_routes_async` | Delete routes |
| `generate_route` / `generate_route_async` | Generate a route |
| `update_route_version` / `update_route_version_async` | Update route version |
| `get_route_versions` / `get_route_versions_async` | Get route versions |

### Types

| Type | Purpose |
|------|---------|
| `ProjectRoute` | Project route |
| `RouteSpec` | Route specification |
| `RouteDefinition` | Route definition |
| `RouteInput` | Route input |
| `GeneratedRoute` | Generated route |
| `GeneratedRouteAction` | Generated route action |
| `GeneratedRouteCondition` | Generated route condition |
| `GeneratedRouteHeader` | Generated route header |
| `GeneratedPathCondition` | Generated path condition |
| `RedirectRoute` | Redirect route |
| `RewriteRoute` | Rewrite route |
| `SetStatusRoute` | Set status route |
| `RouteCondition` | Route condition |
| `RouteTransform` | Route transform |
| `Placement` | Route placement |
| `RouteType` | Route type |
| `RouteVersion` | Route version |
| `RouteLimit` | Route limit |
| `AddRouteResult` | Add route result |
| `EditRouteResult` | Edit route result |
| `DeleteRoutesResult` | Delete routes result |
| `GetRoutesResult` | Get routes result |
| `StagedRouteInput` | Staged route input |
| `SrcSyntax` | Source syntax |
| `VersionAction` | Version action |

## Errors

| Exception | Purpose |
|-----------|---------|
| `ProjectRoutesError` | Project routes error |

## Requirements

Python 3.10 or later.
