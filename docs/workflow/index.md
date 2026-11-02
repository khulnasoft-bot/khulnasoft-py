# `khulnasoft-workflow` — Workflows SDK

`khulnasoft-workflow` is the Python SDK for KhulnaSoft Workflows — workflow
registration, step registration, durable sleeps, hooks, streaming, and run
startup.

## Quick start

```python
import khulnasoft.workflow as wf

# Create a workflow registry
workflows = wf.Workflows()

# Register a workflow
@workflows.workflow
async def my_workflow(name: str) -> str:
    result = await my_step(name)
    return f"Hello, {result}"

# Register a step
@workflows.step
async def my_step(name: str) -> str:
    await wf.sleep("1s")
    return name

# Start a workflow run
run = await wf.start(my_workflow, "World")
print(run.return_value())  # "Hello, World"
```

## Package layout

```
src/khulnasoft-workflow/khulnasoft/workflow/
├── __init__.py      # Public API surface
├── __main__.py      # CLI entry point
├── sandbox.py       # SandboxPolicy — sandbox configuration
├── errors.py        # Public error types
├── version.py       # Version string
└── _internal/
    ├── __init__.py
    ├── core.py          # Workflows, BaseHook, Hook, sleep, now, time_ns, random
    ├── run.py           # Run, start(), get_run()
    ├── runtime.py       # Run metadata, attributes, writable streams
    ├── serde.py         # serializable(), register_serializable()
    ├── streams.py       # WorkflowWritable, WorkflowStreamWriter, read_stream()
    ├── world.py         # HTTPHandler, HTTPRequest, HTTPResponse, WorkflowRunStatus
    ├── attributes.py    # Attribute get/set logic
    ├── duration.py      # Duration parsing
    ├── encryption.py    # Encryption for workflow data
    ├── error_serde.py   # Error serialization
    ├── errors.py        # Internal error types
    ├── loop.py          # Event loop utilities
    ├── nanoid.py        # ID generation
    ├── py_sandbox.py    # Python sandbox for local execution
    ├── serde.py         # Serialization logic
    ├── signature_codec.py   # Signature encoding/decoding
    ├── streams.py       # Stream types
    ├── ulid.py          # ULID generation
    ├── utils.py         # Utility functions
    ├── world.py         # World abstraction
    ├── compression.py   # Compression utilities
    ├── devalue/         # Devalue format parser/stringifier
    └── worlds/
        ├── __init__.py
        ├── khulnasoft.py  # Khulnasoft cloud world
        └── local.py       # Local development world
```

## Public API

### Workflow registration

| Symbol | Purpose |
|--------|---------|
| `Workflows()` | Create a workflow registry |
| `@workflows.workflow` | Register an async workflow function |
| `@workflows.step` | Register an async step (callable only from within a workflow) |

### Run execution

| Symbol | Purpose |
|--------|---------|
| `start(workflow_fn, *args)` | Start a workflow run, returns `Run` |
| `get_run(run_id)` | Retrieve a run by ID |
| `Run` | Run result access (`return_value()`, `attributes()`, `readable()`) |

### Time and sleep

| Symbol | Purpose |
|--------|---------|
| `sleep(duration)` | Durable wait within a workflow |
| `now()` | Current time |
| `time_ns()` | Current time in nanoseconds |
| `random()` | Cryptographically secure random |

### Metadata

| Symbol | Purpose |
|--------|---------|
| `set_attributes(attrs)` | Set run metadata |
| `remove_attributes(keys)` | Remove run metadata |
| `get_step_metadata()` | Get current step metadata |
| `get_workflow_metadata()` | Get current workflow metadata |
| `get_hook_by_token(token)` | Get hook by token |

### Streaming

| Symbol | Purpose |
|--------|---------|
| `get_writable()` | Get progress writable |
| `read_stream(handle)` | Read a workflow stream |
| `WorkflowWritable` | Progress streaming interface |
| `WorkflowStreamWriter` | Stream writer |
| `WorkflowStreamHandle` | Stream handle |

### Hooks

| Symbol | Purpose |
|--------|---------|
| `BaseHook` | Base class for hooks (external resume) |
| `Hook` | Hook type |
| `HookEvent` | Hook event |

### Serialization

| Symbol | Purpose |
|--------|---------|
| `serializable()` | Mark a type as serializable |
| `register_serializable()` | Register a custom type serializer |

### Sandbox integration

| Symbol | Purpose |
|--------|---------|
| `sandbox` | Sandbox integration |
| `SandboxPolicy` | Sandbox configuration for workflows |

### Types

| Type | Purpose |
|------|---------|
| `StepInfo` | Step information |
| `WorkflowInfo` | Workflow information |
| `WorkflowFeatures` | Workflow features |
| `HTTPHandler` / `HTTPRequest` / `HTTPResponse` | HTTP types |
| `WorkflowRunStatus` | Run status enum |

## Errors

| Exception | Purpose |
|-----------|---------|
| `FatalError` | Fatal step error (stop workflow) |
| `RetryableError` | Retryable step error |
| `HookNotFoundError` | Hook not found |
| `HookConflictError` | Hook conflict |
| `HookDisposedError` | Hook disposed |
| `TypeValidationError` | Type validation error |
| `SerializationError` | Serialization error |
| `RemoteError` | Remote error |
| `RunExpiredError` | Run expired |
| `StepNotRegisteredError` | Step not registered |
| `EntityConflictError` | Entity conflict |
| `ThrottleError` | Throttled |
| `TooEarlyError` | Too early |
| `WorkflowRunFailedError` | Workflow run failed |
| `WorkflowWorldError` | Workflow world error |

## Requirements

Python 3.10 or later. Dependencies:
- `khulnasoft-internal-core`
- `khulnasoft-headers`
- `khulnasoft-oidc`
- `khulnasoft-queue`
- `anyio`
- `httpx2`
- `pydantic`
- `semver`
- `cbor2`
- `cryptography`
- `zstandard`
- `typing-extensions`
- `tomli`

## Related

- [`khulnasoft-queue`](../queue/) — workflows use queue for durable execution
- [`khulnasoft-oidc`](../oidc/) — OIDC authentication
- [`khulnasoft-headers`](../headers/) — request headers
