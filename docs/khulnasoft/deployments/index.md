# `khulnasoft.deployments` — Deployment creation

`khulnasoft.deployments` provides deployment creation and file upload helpers.

## Quick start

```python
from khulnasoft.deployments import create_deployment, upload_file

# Create a deployment
deployment = await create_deployment(...)

# Upload a file
result = await upload_file(...)
```

## Package layout

```
src/khulnasoft/deployments/
├── __init__.py    # Public API: create_deployment, upload_file
├── aio.py         # Async deployment client
├── client.py      # DeploymentsClient / AsyncDeploymentsClient
├── deployments.py # create_deployment, upload_file implementations
├── README.md
└── py.typed
```

## Public API

| Symbol | Purpose |
|--------|---------|
| `create_deployment(...)` | Create a deployment |
| `upload_file(...)` | Upload a file for deployment |

## Requirements

Python 3.10 or later.
