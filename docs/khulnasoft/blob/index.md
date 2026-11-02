# `khulnasoft.blob` — Blob storage (meta package)

`khulnasoft.blob` is the blob storage client within the `khulnasoft` meta
package — uploads, downloads, metadata, listing, copy, delete, and multipart
uploads.

This is the same blob functionality available in the standalone
[`khulnasoft-blob`](../blob/) package, re-exported here for convenience.

## Quick start

```python
import khulnasoft.blob as blob

# Upload
result = await blob.put(
    "examples/assets/hello.txt",
    b"hello from python",
    access="public",
    content_type="text/plain",
)

# Download
result = await blob.get("examples/assets/hello.txt", access="public")
print(result.body)

# List
async for item in blob.list_objects(prefix="examples/assets/", access="public"):
    print(item.pathname, item.size)

# Delete
await blob.delete("examples/assets/hello.txt", access="public")

# Multipart upload
async with await blob.create_multipart_uploader(
    "large-file.bin", access="public"
) as uploader:
    for i, chunk in enumerate(chunks, start=1):
        await uploader.upload_part(chunk)
```

Sync variant:

```python
from khulnasoft.blob import put, get, delete

result = put("examples/assets/hello.txt", b"hello", access="public")
```

## Package layout

```
src/khulnasoft/blob/
├── __init__.py      # Public API surface
├── aio.py           # Async client (aioblob)
├── client.py        # BlobClient / AsyncBlobClient
├── errors.py        # Error hierarchy
├── multipart/       # Multipart upload helpers
├── ops.py           # Core operations (put, get, delete, list, copy)
├── types.py         # Data types
├── README.md
└── py.typed
```

## Public API

### Core operations

| Symbol | Purpose |
|--------|---------|
| `put` / `put_async` | Upload a blob |
| `get` / `get_async` | Download a blob |
| `head` / `head_async` | Retrieve blob metadata |
| `delete` / `delete_async` | Delete blobs |
| `list_objects` / `list_objects_async` | List blobs |
| `iter_objects` / `iter_objects_async` | Iterate over blobs |
| `copy` / `copy_async` | Copy a blob |
| `create_folder` / `create_folder_async` | Create a folder |
| `download_file` / `download_file_async` | Download to file |
| `upload_file` / `upload_file_async` | Upload from file |

### Multipart

| Symbol | Purpose |
|--------|---------|
| `create_multipart_upload` / `create_multipart_upload_async` | Create multipart upload |
| `upload_part` / `upload_part_async` | Upload a part |
| `complete_multipart_upload` / `complete_multipart_upload_async` | Complete upload |
| `create_multipart_uploader` / `create_multipart_uploader_async` | Uploader context manager |
| `auto_multipart_upload` / `auto_multipart_upload_async` | Automatic multipart upload |
| `MultipartUploader` / `AsyncMultipartUploader` | Uploader classes |

### Clients

| Class | Purpose |
|-------|---------|
| `BlobClient` | Sync blob client |
| `AsyncBlobClient` | Async blob client |

### Helpers

| Symbol | Purpose |
|--------|---------|
| `get_download_url` | Get download URL |
| `aioblob` | Async blob module |

### Types

| Type | Purpose |
|------|---------|
| `Access` | `"public"` \| `"private"` |
| `PutBlobResult` | Upload result |
| `GetBlobResult` | Download result |
| `HeadBlobResult` | HEAD result |
| `ListBlobResult` | List result |
| `ListBlobItem` | Listed item |
| `CreateFolderResult` | Create folder result |
| `MultipartCreateResult` | Multipart create result |
| `MultipartPart` | Multipart part |
| `UploadProgressEvent` | Upload progress event |
| `OnUploadProgressCallback` | Progress callback type |

## Errors

| Exception | Purpose |
|-----------|---------|
| `BlobError` | Base blob error |
| `BlobNotFoundError` | Blob not found |
| `BlobAccessError` | Access denied |
| `BlobStoreNotFoundError` | Store not found |
| `BlobStoreSuspendedError` | Store suspended |
| `BlobPreconditionFailedError` | Precondition failed |
| `BlobServiceRateLimited` | Rate limited |
| `BlobClientTokenExpiredError` | Token expired |
| `BlobContentTypeNotAllowedError` | Content type not allowed |
| `BlobPathnameMismatchError` | Pathname mismatch |
| `BlobFileTooLargeError` | File too large |
| `BlobRequestAbortedError` | Request aborted |
| `BlobUnexpectedResponseContentTypeError` | Unexpected content type |
| `BlobInvalidResponseJSONError` | Invalid JSON response |
| `BlobServiceNotAvailable` | Service not available |
| `BlobNoTokenProvidedError` | No token provided |
| `BlobUnknownError` | Unknown error |

## Requirements

Python 3.10 or later.

## Related

- [`khulnasoft-blob`](../blob/) — standalone blob package with identical functionality
