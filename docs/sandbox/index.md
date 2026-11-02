# `khulnasoft-sandbox` — Sandbox SDK

`khulnasoft-sandbox` is the Python SDK for KhulnaSoft Sandbox — create and
manage sandboxes with sync and async APIs, drives, snapshots, forks, and
filesystem/process operations.

## Quick start

```python
import khulnasoft.sandbox as sandbox

# Create a sandbox
async with await sandbox.create_sandbox() as sb:
    # Run a process inside the sandbox
    result = await sb.run_process("echo hello")
    print(result.output)

    # Write a file
    await sb.fs.write_text("hello.txt", "world")
    content = await sb.fs.read_text("hello.txt")

# Create a drive
drive = await sandbox.get_or_create_drive("my-drive")

# Create a sandbox from a git source
async with await sandbox.create_sandbox(
    sources=[sandbox.GitSource(repo="https://github.com/...")]
) as sb:
    ...
```

Sync variant:

```python
from khulnasoft.sandbox.sync import create_sandbox

async with create_sandbox() as sb:
    result = sb.run_process("echo hello")
```

## Package layout

```
src/khulnasoft-sandbox/khulnasoft/sandbox/
├── __init__.py      # Public async API
├── __main__.py      # CLI entry point
├── client.py        # SandboxClient — standalone client
├── sync/__init__.py # Synchronous mirror
├── sync/client.py   # SyncSandboxClient
├── version.py       # Version string
└── _internal/
    ├── __init__.py
    ├── api_client.py        # HTTP API client
    ├── async_runtime.py     # Async runtime: Sandbox, Drive, Process, Snapshot
    ├── sync_runtime.py      # Sync runtime: SyncSandbox, SyncDrive, SyncProcess
    ├── service.py           # SandboxService, get_sandbox_service
    ├── models.py            # Pydantic models for all sandbox types
    ├── options.py           # SandboxServiceOptions, SandboxCredentials
    ├── errors.py            # All sandbox error types
    ├── async_filesystem_handle.py  # Async filesystem handles
    ├── sync_filesystem_handle.py   # Sync filesystem handles
    ├── filesystem_handle_core.py   # Shared filesystem logic
    ├── filesystem_write.py         # Filesystem write operations
    ├── log_stream.py               # Log streaming
    ├── text_reader.py                # TextReader
    ├── streaming_archive.py        # Streaming archive (tar) support
    ├── recovery.py                   # Recovery logic
    ├── state.py                        # SnapshotRetentionState
    ├── pagination.py                   # Pagination helpers
    └── runtime_common.py               # Common runtime types
```

## Public API

### Sandbox lifecycle

| Symbol | Purpose |
|--------|---------|
| `create_sandbox()` | Create a new sandbox (async context manager) |
| `fork_sandbox()` | Fork an existing sandbox (async context manager) |
| `get_or_create_sandbox()` | Get or create a named sandbox |
| `get_sandbox()` | Fetch a sandbox by ID |
| `resume_sandbox()` | Resume a suspended sandbox |
| `query_sandboxes()` | Query sandboxes |
| `query_sessions()` | Query sandbox sessions |
| `query_snapshots()` | Query snapshots |
| `get_snapshot()` | Get a snapshot by ID |

### Drive management

| Symbol | Purpose |
|--------|---------|
| `get_or_create_drive()` | Get or create a drive |
| `delete_drive()` | Delete a drive |
| `query_drives()` | Query drives |

### Types

| Type | Purpose |
|------|---------|
| `Sandbox` | Sandbox instance |
| `SandboxClient` | Standalone async client |
| `SyncSandboxClient` | Standalone sync client |
| `Drive` | Drive instance |
| `SyncDrive` | Sync drive instance |
| `SandboxMount` | Sandbox mount configuration |
| `SandboxResources` | Sandbox resource limits |
| `Process` | Process instance |
| `CompletedProcess` | Completed process result |
| `Snapshot` | Snapshot instance |
| `GitSource` | Git source for sandbox creation |
| `TarballSource` | Tarball source for sandbox creation |
| `SnapshotSource` | Snapshot source |
| `TagFilter` | Tag filter for queries |
| `NetworkPolicy` | Network policy (matchers/rules) |
| `TextReader` / `SandboxTextReader` | Text reader |
| `SandboxFilesystem` | Sandbox filesystem interface |

## Errors

| Exception | Purpose |
|-----------|---------|
| `SandboxError` | Base sandbox error |
| `SandboxApiError` | API error |
| `SandboxCredentialsError` | Credentials error |
| `SandboxResponseError` | Response error |
| `SandboxTerminalStateError` | Terminal state error |
| `SandboxTimeoutError` | Timeout error |
| `SandboxCleanupError` | Cleanup error |
| `SandboxFilesystemError` | Filesystem error |
| `SandboxFilesystemCommandError` | Filesystem command error |
| `SandboxFilesystemTransferError` | Filesystem transfer error |
| `SandboxFilesystemWriteError` | Filesystem write error |
| `SandboxInvalidHandleError` | Invalid handle error |
| `SandboxPathNotFoundError` | Path not found error |
| `SandboxUploadSizeMismatchError` | Upload size mismatch |
| `SandboxStreamError` | Stream error |

## Requirements

Python 3.10 or later. Dependencies:
- `khulnasoft-internal-core`
- `khulnasoft-oidc`
- `anyio`
- `httpx2`
- `pydantic`

Console scripts: `khulnasoft-sandbox`, `sandbox` (both delegate to `npx sandbox`)

## Related

- [`khulnasoft-internal-core`](../internal-core/) — shared runtime
- [`khulnasoft-oidc`](../oidc/) — OIDC authentication
