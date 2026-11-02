# `khulnasoft.projects` — Project CRUD

`khulnasoft.projects` provides project list, create, update, and delete
operations.

## Quick start

```python
from khulnasoft.projects import (
    get_projects,
    create_project,
    update_project,
    delete_project,
)

# List projects
projects = await get_projects(...)

# Create a project
project = await create_project(...)

# Update a project
project = await update_project(...)

# Delete a project
await delete_project(...)
```

## Package layout

```
src/khulnasoft/projects/
├── __init__.py    # Public API: get_projects, create_project, update_project, delete_project
├── projects.py    # Project CRUD implementations
├── README.md
└── py.typed
```

## Public API

| Symbol | Purpose |
|--------|---------|
| `get_projects(...)` | List projects |
| `create_project(...)` | Create a project |
| `update_project(...)` | Update a project |
| `delete_project(...)` | Delete a project |

## Requirements

Python 3.10 or later.
