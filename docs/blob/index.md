# `khulnasoft-blob` — Blob Storage SDK

`khulnasoft-blob` provides async and sync object operations for KhulnaSoft Blob
storage: upload, download, list, delete, copy, and multipart uploads.

## Quick start

```python
import khulnasoft.blob as blob

client = blob.BlobClient()  # or use module-level functions

# Upload
result = await blob.put_blob(
    "examples/assets/hello.txt",
    b"hello from python",
    access="public",
    content_type="text/plain",
)

# Download
result = await blob.get_blob("examples/assets/hello.txt", access="public")
print(result.body)

# List
async for item in blob.query_blobs(prefix="examples/assets/", access="public"):
    print(item.pathname, item.size)

# Delete
await blob.delete_blob("examples/assets/hello.txt", access="public")
```

## Sync usage

All operations also have synchronous variants under `khulnasoft.blob.sync`:

```python
from khulnasoft.blob import sync

result = sync.put_blob(
    "examples/assets/hello.txt",
    b"hello",
    access="public",
)
```

## Package layout

```
src/khulnasoft-blob/khulnasoft/blob/
├── __init__.py          # Async public API surface
├── sync.py              # Sync public API surface
├── types.py             # Data types (PutResult, GetResult, HeadResult, ...)
├── errors.py            # Error hierarchy
├── options.py           # Service options and credential factories
├── _runtime.py          # Async/sync ops client construction
├── _stream.py           # Streaming download helpers
├── _multipart.py        # Multipart upload helpers
├── _validation.py       # Pathname and URL validation
└── version.py           # Version string
```

## Key concepts

### Credentials

The SDK resolves credentials automatically from the environment:

1. OIDC token (`BLOB_STORE_ID` + `KHULNASOFT_OIDC_TOKEN`)
2. Read/write token (`BLOB_READ_WRITE_TOKEN` or `KHULNASOFT_BLOB_READ_WRITE_TOKEN`)

You can also supply a custom `credentials_factory` via `BlobServiceOptions`.

### Access levels

`access` is either `"public"` or `"private"`. Private accesses require an
`Authorization: Bearer <token>` header, which the SDK adds automatically.

### Pathnames vs delivery URLs

Most functions accept either a **pathname** (e.g. `"examples/assets/foo.txt"`)
or a **delivery URL** (an `https://...` blob URL). Pathnames are validated
against the blob naming rules; delivery URLs must be HTTPS and use the standard
blob host.

### Multipart uploads

For large files, use the multipart upload context manager:

```python
async with await blob.multipart_upload_blob(
    "large-file.bin", access="private"
) as uploader:
    for i, chunk in enumerate(chunks, start=1):
        await uploader.upload_part(chunk)
    # result available on uploader.result after exit
```

Parts must be between 1 byte and 5 GiB; all parts except the last must be at
least 5 MiB. A maximum of 10,000 parts is supported.

## Module structure

See [`docs/blob/modules.md`](modules.md) for a detailed breakdown of every
module and its responsibilities.

## Key concepts

See [`docs/blob/concepts.md`](concepts.md) for deep dives on credentials,
access levels, pathnames, and multipart uploads.

## Testing

Tests live under `src/khulnasoft-blob/tests/`. Live tests (marked `live`)
require KhulnaSoft Blob credentials and are excluded by default:

```bash
uv run --python 3.10 -m pytest src/khulnasoft-blob/tests
```

## Requirements

Python 3.10 or later. Dependencies:
- `khulnasoft-internal-core>=0.2.0,<0.3.0`
- `anyio>=4.0.0,<5`
- `httpx2>=2`

## Related

- [`AI_REFACTORING_PLAN.md`](../AI_REFACTORING_PLAN.md) — refactoring plan
- [`docs/ai/`](../ai/) — documentation for the `khulnasoft.ai` package
