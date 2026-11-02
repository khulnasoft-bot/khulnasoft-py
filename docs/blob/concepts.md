# Key concepts — `khulnasoft-blob`

## Credentials

The SDK resolves credentials automatically, in this order:

1. **OIDC** — If `BLOB_STORE_ID` is set, the SDK tries to get an OIDC token
   via `khulnasoft.oidc.credentials.get_khulnasoft_oidc_token_from_context()`,
   falling back to the `KHULNASOFT_OIDC_TOKEN` env var. Credential kind:
   `oidc`.
2. **Read/write token** — If `BLOB_READ_WRITE_TOKEN` (or
   `KHULNASOFT_BLOB_READ_WRITE_TOKEN`) is set, the SDK extracts the store ID
   from the token. Credential kind: `token`.
3. **Error** — If neither source yields credentials, `BlobCredentialsError` is
   raised.

You can supply a custom `credentials_factory` to `BlobServiceOptions` to
override this behavior:

```python
from khulnasoft.blob import BlobServiceOptions

async def my_creds():
    return BlobCredentials(token="...", store_id="...", kind="token")

options = BlobServiceOptions(credentials_factory=my_creds)
```

## Access levels

`access` is `"public"` or `"private"`:

- **`public`**: No `Authorization` header is sent; the blob is fetched using
  the public delivery URL.
- **`private`**: The SDK adds `Authorization: Bearer <token>` to the request.

## Pathnames vs delivery URLs

Most functions accept either a pathname or a delivery URL:

- **Pathname** — e.g. `"examples/assets/foo.txt"`. Validated by
  `validate_pathname`: must be a non-empty string, no control characters,
  valid UTF-8, no empty segments (`//`), no `.` or `..` segments, and
  (on upload) ≤ 950 UTF-16 code units. Leading `/` is stripped.
- **Delivery URL** — e.g. `https://store_x.blob.khulnasoft-storage.com/...`.
  Validated by `validate_delivery_url`: must use HTTPS, use the standard blob
  host (`.blob.khulnasoft-storage.com`), no fragment, valid path segments.
  Optionally checked against a `store_id`.

## Multipart uploads

For files larger than a single part, use the multipart upload context manager:

```python
async with await blob.multipart_upload_blob(
    "large-file.bin", access="private"
) as uploader:
    for i, chunk in enumerate(chunks, start=1):
        await uploader.upload_part(chunk)
result = uploader.result  # PutResult after exit
```

Constraints:
- 1 to 10,000 parts.
- Each part: 1 byte to 5 GiB.
- All parts except the last must be ≥ 5 MiB.
- On exit, parts are completed via `complete_multipart_upload`; the result is
  stored on `uploader.result` as a `PutResult`.
- If an exception occurs inside the context, the upload is abandoned (not
  completed).

## Listing

Two listing functions are available:

- **`query_blobs(prefix, page_size, cursor)`** — Returns `ListBlob` entries
  only. Uses `iter_objects` under the hood. Page size 1–1000.
- **`query_blob_entries(prefix, page_size, cursor)`** — Returns `ListBlob`
  entries **and** `BlobPrefix` entries (for "folder"-style prefixes). The
  prefix must end with `/` (unless empty/`None`). Uses `list_objects` pages
  manually to distinguish blobs from folders.

Both are async iterators.

## Errors

All errors subclass `BlobError`, which carries an optional `status_code` and
`code`. Catch `BlobError` (or a subclass) to handle failures:

```python
from khulnasoft.blob import BlobNotFoundError, BlobError

try:
    await blob.get_blob("missing.txt", access="public")
except BlobNotFoundError:
    print("blob does not exist")
except BlobError as exc:
    print(f"blob error (status={exc.status_code}, code={exc.code}): {exc}")
```

## Async vs sync

Every public function has both an async variant (in `khulnasoft.blob.__init__`)
and a sync variant (in `khulnasoft.blob.sync`). The sync variants block on the
underlying async transport via `iter_coroutine`. Choose based on your
application's concurrency model.

## Requirements

Python 3.10 or later. Dependencies:
- `khulnasoft-internal-core>=0.2.0,<0.3.0`
- `anyio>=4.0.0,<5`
- `httpx2>=2`
