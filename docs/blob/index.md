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

### Access levels

`access` is either `"public"` or `"private"`. Private accesses require an
`Authorization: Bearer <token>` header, which the SDK adds automatically.

### Multipart uploads

For large files, use the multipart upload context manager:

```python
async with await blob.multipart_upload_blob(
    "large-file.bin", access="private"
) as uploader:
    for i, chunk in enumerate(chunks, start=1):
        await uploader.upload_part(chunk)
```

Parts must be between 1 byte and 5 GiB; all parts except the last must be at
least 5 MiB. A maximum of 10,000 parts is supported.

## Requirements

Python 3.10 or later. Dependencies:
- `khulnasoft-internal-core>=0.2.0,<0.3.0`
- `anyio>=4.0.0,<5`
- `httpx2>=2`
