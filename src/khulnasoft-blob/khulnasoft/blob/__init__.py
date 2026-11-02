from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ._multipart import multipart_upload_blob
from ._runtime import get_async_ops
from ._stream import stream_blob
from ._validation import validate_delivery_url, validate_pathname
from .errors import (
    BlobAccessError,
    BlobContentLengthError,
    BlobCredentialsError,
    BlobError,
    BlobNotFoundError,
    BlobPreconditionFailedError,
    BlobServiceRateLimited,
    BlobStreamError,
    CredentialKind,
)
from .options import BlobServiceOptions
from .types import (
    Access,
    BlobCredentials,
    BlobPrefix,
    CopyResult,
    DownloadMetadata,
    GetResult,
    HeadResult,
    ListBlob,
    PutResult,
)
from .version import __version__

__all__ = [
    "Access",
    "BlobCredentials",
    "BlobError",
    "BlobNotFoundError",
    "BlobAccessError",
    "BlobPreconditionFailedError",
    "BlobServiceRateLimited",
    "BlobStreamError",
    "BlobCredentialsError",
    "BlobContentLengthError",
    "BlobServiceOptions",
    "CredentialKind",
    "CopyResult",
    "DownloadMetadata",
    "GetResult",
    "HeadResult",
    "ListBlob",
    "BlobPrefix",
    "PutResult",
    "put_blob",
    "__version__",
    "stream_blob",
    "multipart_upload_blob",
    "get_blob",
    "head_blob",
    "delete_blob",
    "query_blobs",
    "query_blob_entries",
    "copy_blob",
]


def _convert_put(raw: Any) -> PutResult:
    return PutResult(
        url=raw["url"],
        download_url=raw["downloadUrl"],
        pathname=raw["pathname"],
        content_type=raw["contentType"],
        content_disposition=raw["contentDisposition"],
        etag=raw.get("etag", ""),
    )


async def put_blob(
    pathname: str,
    body: Any,
    *,
    access: Access,
    content_length: int | None = None,
    content_type: str | None = None,
    add_random_suffix: bool = False,
    allow_overwrite: bool = False,
    cache_control_max_age: int | None = None,
    session: Any = None,
) -> PutResult:
    validate_pathname(pathname, upload=True)
    # exact content length validation for streams
    if isinstance(body, (bytes, bytearray, memoryview, str)):
        if content_length is not None and content_length != len(
            body.encode() if isinstance(body, str) else body
        ):
            raise BlobContentLengthError("content_length does not match body")
    else:
        if content_length is None:
            raise BlobContentLengthError("content_length is required for streaming bodies")
    ops = await get_async_ops(session)
    # Use ops put_blob with multipart=False
    result, _ = await ops.put_blob(
        pathname,
        body,
        access=access,
        content_type=content_type,
        add_random_suffix=add_random_suffix,
        overwrite=allow_overwrite,
        cache_control_max_age=cache_control_max_age,
        token=None,
        multipart=False,
        on_upload_progress=None,
    )
    return PutResult(
        url=result.url,
        download_url=result.download_url,
        pathname=result.pathname,
        content_type=result.content_type,
        content_disposition=result.content_disposition,
        etag=result.etag or "",
    )


async def get_blob(pathname_or_url: str, *, access: Access, session: Any = None) -> GetResult:
    from ._validation import validate_delivery_url, validate_pathname

    is_url = pathname_or_url.startswith(("http://", "https://"))
    if is_url:
        validate_delivery_url(pathname_or_url)
    else:
        validate_pathname(pathname_or_url)
    ops = await get_async_ops(session)
    internal = await ops.get_blob(
        pathname_or_url,
        access=access,
        timeout=None,
        use_cache=True,
        if_none_match=None,
        default_timeout=__import__("datetime").timedelta(seconds=30),
        token=None,
    )
    metadata = DownloadMetadata(
        url=internal.url,
        status_code=internal.status_code,
        size=internal.size,
        content_type=internal.content_type,
        content_disposition=internal.content_disposition,
        cache_control=internal.cache_control,
        etag=internal.etag,
        last_modified=internal.uploaded_at,
        uploaded_at=internal.uploaded_at,
    )
    return GetResult(metadata=metadata, body=internal.content)


async def head_blob(pathname_or_url: str, *, session: Any = None) -> HeadResult:
    from ._validation import validate_delivery_url, validate_pathname

    if pathname_or_url.startswith(("http://", "https://")):
        validate_delivery_url(pathname_or_url)
    else:
        validate_pathname(pathname_or_url)
    ops = await get_async_ops(session)
    internal = await ops.head_blob(pathname_or_url, token=None)
    return HeadResult(
        size=internal.size,
        uploaded_at=internal.uploaded_at,
        pathname=internal.pathname,
        content_type=internal.content_type,
        content_disposition=internal.content_disposition,
        url=internal.url,
        download_url=internal.download_url,
        cache_control=internal.cache_control,
        etag=getattr(internal, "etag", None),
    )


async def delete_blob(targets, *, session: Any = None) -> None:
    from ._validation import validate_delivery_url, validate_pathname

    if isinstance(targets, str):
        targets = [targets]
    targets = list(targets)
    if not (1 <= len(targets) <= 1000):
        raise BlobError("delete accepts 1 to 1000 targets")
    for target in targets:
        if target.startswith(("http://", "https://")):
            validate_delivery_url(target)
        else:
            validate_pathname(target)
    ops = await get_async_ops(session)
    await ops.delete_blob(targets, token=None)


async def query_blobs(
    *,
    prefix: str | None = None,
    page_size: int = 1000,
    cursor: str | None = None,
    session: Any = None,
) -> AsyncIterator[ListBlob]:
    if page_size < 1 or page_size > 1000:
        raise BlobError("page_size must be between 1 and 1000")
    ops = await get_async_ops(session)
    async for item in ops.iter_objects(
        prefix=prefix, mode=None, batch_size=page_size, limit=None, cursor=cursor, token=None
    ):
        yield ListBlob(
            url=item.url,
            download_url=item.download_url,
            pathname=item.pathname,
            size=item.size,
            uploaded_at=item.uploaded_at,
            etag=getattr(item, "etag", None),
        )


async def query_blob_entries(
    *,
    prefix: str | None = None,
    page_size: int = 1000,
    cursor: str | None = None,
    session: Any = None,
) -> AsyncIterator[ListBlob | BlobPrefix]:
    if prefix not in (None, "") and not (prefix or "").endswith("/"):
        raise BlobError("directory prefix must end with /")
    if page_size < 1 or page_size > 1000:
        raise BlobError("page_size must be between 1 and 1000")
    ops = await get_async_ops(session)
    # Use list_objects pages manually to distinguish folders
    next_cursor = cursor
    while True:
        page = await ops.list_objects(
            limit=page_size, prefix=prefix, cursor=next_cursor, mode=None, token=None
        )
        for blob in page.blobs:
            yield ListBlob(
                url=blob.url,
                download_url=blob.download_url,
                pathname=blob.pathname,
                size=blob.size,
                uploaded_at=blob.uploaded_at,
                etag=getattr(blob, "etag", None),
            )
        for folder in page.folders or []:
            yield BlobPrefix(prefix=folder)
        next_cursor = page.cursor if page.has_more else None
        if next_cursor is None:
            break


async def copy_blob(
    source: str,
    destination: str,
    *,
    access: Access,
    content_type: str | None = None,
    add_random_suffix: bool = False,
    allow_overwrite: bool = False,
    cache_control_max_age: int | None = None,
    if_match: str | None = None,
    session: Any = None,
) -> CopyResult:
    validate_pathname(destination, upload=True)
    if source.startswith(("http://", "https://")):
        validate_delivery_url(source)
    else:
        validate_pathname(source)
    ops = await get_async_ops(session)
    internal = await ops.copy_blob(
        source,
        destination,
        access=access,
        content_type=content_type,
        add_random_suffix=add_random_suffix,
        overwrite=allow_overwrite,
        cache_control_max_age=cache_control_max_age,
        token=None,
    )
    return CopyResult(
        url=internal.url,
        download_url=internal.download_url,
        pathname=internal.pathname,
        content_type=internal.content_type,
        content_disposition=internal.content_disposition,
        etag=internal.etag or "",
    )
