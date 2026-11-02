# Module structure — `khulnasoft-blob`

This page breaks down every module in `src/khulnasoft-blob/khulnasoft/blob/`
and its responsibilities.

## Package root — async API (`__init__.py`)

| Symbol | Purpose |
|--------|---------|
| `put_blob` | Upload a blob (pathname + body) |
| `get_blob` | Download a blob (returns metadata + body bytes) |
| `head_blob` | Retrieve blob metadata without body |
| `delete_blob` | Delete 1–1000 blobs by pathname or URL |
| `query_blobs` | Async iterator of `ListBlob` entries (prefix pagination) |
| `query_blob_entries` | Async iterator of `ListBlob \| BlobPrefix` (folder-aware listing) |
| `copy_blob` | Copy a blob from source to destination |
| `stream_blob` | Async context manager streaming a blob download in chunks |
| `multipart_upload_blob` | Async context manager for multipart uploads |
| `BlobServiceOptions` | Service configuration (base URL, credentials factory, timeout) |
| `Access` | Literal `"public"` \| `"private"` |
| Error types | `BlobError`, `BlobNotFoundError`, `BlobAccessError`, `BlobStoreNotFoundError`, `BlobPreconditionFailedError`, `BlobServiceRateLimited`, `BlobStreamError`, `BlobCredentialsError`, `BlobContentLengthError`, `CredentialKind` |
| Data types | `BlobCredentials`, `DownloadMetadata`, `PutResult`, `GetResult`, `HeadResult`, `ListBlob`, `BlobPrefix`, `CopyResult` |
| `__version__` | Package version string |

## `sync.py` — sync API

Mirror of the async API in `__init__.py`, but all functions are synchronous
(blocking). Uses `SyncBlobServiceOptions` and `get_sync_ops()`. The
`stream_blob` context manager and `SyncMultipartUpload` class are also
provided here.

| Symbol | Purpose |
|--------|---------|
| `put_blob`, `get_blob`, `head_blob`, `delete_blob` | Sync variants of the async functions |
| `query_blobs`, `query_blob_entries`, `copy_blob` | Sync variants |
| `stream_blob` | Sync context manager (`contextmanager`) for streaming download |
| `multipart_upload_blob` | Returns a `SyncMultipartUpload` context manager |
| `SyncBlobServiceOptions` | Sync service options |
| Data types / error types | Same as async API |

## `types.py` — Data types

| Type | Purpose |
|------|---------|
| `BlobCredentials` | Token, store ID, credential kind |
| `DownloadMetadata` | URL, status code, size, content type/disposition, cache control, ETag, timestamps |
| `PutResult` | Result of an upload (URL, download URL, pathname, content type/disposition, ETag) |
| `GetResult` | Result of a download (`metadata` + `body` bytes) |
| `HeadResult` | Result of a HEAD request (size, uploaded at, pathname, content type/disposition, URL, download URL, cache control, ETag) |
| `ListBlob` | Listed blob entry (URL, download URL, pathname, size, uploaded at, ETag) |
| `BlobPrefix` | Folder prefix (from `query_blob_entries`) |
| `CopyResult` | Result of a copy (same shape as `PutResult`) |
| `Access` | `"public"` \| `"private"` |

## `errors.py` — Error hierarchy

| Exception | Purpose |
|-----------|---------|
| `BlobError` | Base error (message, optional status code + code) |
| `BlobNotFoundError` | Blob not found |
| `BlobAccessError` | Access denied |
| `BlobStoreNotFoundError` | Store not found |
| `BlobPreconditionFailedError` | Precondition failed |
| `BlobServiceRateLimited` | Rate limited |
| `BlobStreamError` | Stream error |
| `BlobCredentialsError` | Missing/invalid credentials |
| `BlobContentLengthError` | Content length mismatch |
| `CredentialKind` | `TOKEN` \| `OIDC` |

## `options.py` — Service options & credentials

| Symbol | Purpose |
|--------|---------|
| `BlobCredentialsFactory` | Async protocol: `async def __call__() -> BlobCredentials` |
| `SyncBlobCredentialsFactory` | Sync protocol: `def __call__() -> BlobCredentials` |
| `BlobServiceOptions` | Async options: `base_url`, `credentials_factory`, `timeout` |
| `SyncBlobServiceOptions` | Sync options: same fields |
| `_default_async_credentials` / `_default_sync_credentials` | Resolve credentials from env (`BLOB_STORE_ID`/`KHULNASOFT_OIDC_TOKEN`, then `BLOB_READ_WRITE_TOKEN`) |

## `_runtime.py` — Ops client construction

| Symbol | Purpose |
|--------|---------|
| `get_async_ops(session)` | Build an `AsyncBlobOpsClient` from an SDK session |
| `get_sync_ops(session)` | Build a `SyncBlobOpsClient` from an SDK session |

Wires together the SDK session, transport, retry policy, request client, and
multipart client.

## `_stream.py` — Streaming download

| Symbol | Purpose |
|--------|---------|
| `AsyncStreamDownload` | Async iterable wrapper over an HTTP response (64 KiB chunks) |
| `stream_blob(pathname_or_url, *, access, session)` | Async context manager: resolves token, builds URL, GETs the blob, yields chunks |

## `_multipart.py` — Multipart upload

| Symbol | Purpose |
|--------|---------|
| `AsyncMultipartUpload` | Async context manager: create upload, `upload_part` per chunk, complete on exit |
| `multipart_upload_blob(...)` | Factory returning an `AsyncMultipartUpload` |

Enforces: 1–10,000 parts, 1 byte–5 GiB per part, all parts except the last
≥ 5 MiB.

## `_validation.py` — Input validation

| Symbol | Purpose |
|--------|---------|
| `validate_pathname(path, *, upload=False)` | Validate a blob pathname (no control chars, valid UTF-8, no empty segments, no `.`/`..`, length ≤ 950 UTF-16 units on upload) |
| `validate_delivery_url(url, *, store_id="")` | Validate a blob delivery URL (HTTPS, standard blob host, no fragment, valid path segments) |

## Directory sizes

| Module | LOC |
|--------|-----|
| `__init__.py` | 288 |
| `sync.py` | 459 |
| `types.py` | 84 |
| `errors.py` | 49 |
| `options.py` | 111 |
| `_runtime.py` | 95 |
| `_stream.py` | 76 |
| `_multipart.py` | 144 |
| `_validation.py` | 61 |
| `version.py` | small |

Total: ~1,367 LOC across 9 source modules (plus tests).
