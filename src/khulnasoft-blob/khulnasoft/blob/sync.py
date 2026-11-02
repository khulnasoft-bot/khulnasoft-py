from __future__ import annotations

from contextlib import contextmanager

from ._runtime import get_sync_ops
from ._validation import validate_delivery_url, validate_pathname
from .errors import (
    BlobContentLengthError,
    BlobError,
    BlobNotFoundError,
)
from .options import SyncBlobServiceOptions
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

__all__ = [
    "BlobCredentials",
    "BlobError",
    "BlobNotFoundError",
    "BlobContentLengthError",
    "SyncBlobServiceOptions",
    "Access",
    "CopyResult",
    "DownloadMetadata",
    "GetResult",
    "HeadResult",
    "ListBlob",
    "BlobPrefix",
    "PutResult",
    "put_blob",
    "get_blob",
    "stream_blob",
    "head_blob",
    "delete_blob",
    "query_blobs",
    "query_blob_entries",
    "copy_blob",
    "multipart_upload_blob",
]


def put_blob(
    pathname,
    body,
    *,
    access,
    content_length=None,
    content_type=None,
    add_random_suffix=False,
    allow_overwrite=False,
    cache_control_max_age=None,
    session=None,
):
    validate_pathname(pathname, upload=True)
    if isinstance(body, (bytes, bytearray, memoryview, str)):
        if content_length is not None and content_length != len(
            body.encode() if isinstance(body, str) else body
        ):
            raise BlobContentLengthError("content_length does not match body")
    else:
        if content_length is None:
            raise BlobContentLengthError("content_length is required for streaming bodies")
    ops = get_sync_ops(session)
    result, _ = ops.put_blob(
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


def get_blob(pathname_or_url, *, access, session=None):
    if pathname_or_url.startswith(("http://", "https://")):
        validate_delivery_url(pathname_or_url)
    else:
        validate_pathname(pathname_or_url)
    ops = get_sync_ops(session)
    internal = ops.get_blob(
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


def head_blob(pathname_or_url, *, session=None):
    if pathname_or_url.startswith(("http://", "https://")):
        validate_delivery_url(pathname_or_url)
    else:
        validate_pathname(pathname_or_url)
    ops = get_sync_ops(session)
    internal = ops.head_blob(pathname_or_url, token=None)
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


def delete_blob(targets, *, session=None):
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
    ops = get_sync_ops(session)
    ops.delete_blob(targets, token=None)


def query_blobs(*, prefix=None, page_size=1000, cursor=None, session=None):
    if page_size < 1 or page_size > 1000:
        raise BlobError("page_size must be between 1 and 1000")
    ops = get_sync_ops(session)
    for item in ops.iter_objects(
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


def query_blob_entries(*, prefix=None, page_size=1000, cursor=None, session=None):
    if prefix not in (None, "") and not prefix.endswith("/"):
        raise BlobError("directory prefix must end with /")
    if page_size < 1 or page_size > 1000:
        raise BlobError("page_size must be between 1 and 1000")
    ops = get_sync_ops(session)
    next_cursor = cursor
    while True:
        page = ops.list_objects(
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


def copy_blob(
    source,
    destination,
    *,
    access,
    content_type=None,
    add_random_suffix=False,
    allow_overwrite=False,
    cache_control_max_age=None,
    if_match=None,
    session=None,
):
    validate_pathname(destination, upload=True)
    if source.startswith(("http://", "https://")):
        validate_delivery_url(source)
    else:
        validate_pathname(source)
    ops = get_sync_ops(session)
    internal = ops.copy_blob(
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


@contextmanager
def stream_blob(pathname_or_url, *, access, session=None):
    if pathname_or_url.startswith(("http://", "https://")):
        validate_delivery_url(pathname_or_url)
    else:
        validate_pathname(pathname_or_url)
    ops = get_sync_ops(session)
    from khulnasoft._internal.blob import construct_blob_url, extract_store_id_from_token

    token = ops._request_client.resolve_token(None) if False else None
    # sync resolve token is async internally; use iter_coroutine
    from khulnasoft._internal.core.iter_coroutine import iter_coroutine

    token = iter_coroutine(ops._request_client.resolve_token(None))
    if pathname_or_url.startswith(("http://", "https://")):
        target_url = pathname_or_url
    else:
        store_id = extract_store_id_from_token(token)
        if store_id:
            target_url = construct_blob_url(store_id, pathname_or_url.lstrip("/"), access)
        else:
            head = ops.head_blob(pathname_or_url, token=token)
            target_url = head.url
    headers = {}
    if access == "private":
        headers["authorization"] = f"Bearer {token}"
    response = ops._request_client.transport.send if False else None

    # SyncTransport.send is coroutine; run via iter_coroutine
    response = iter_coroutine(
        ops._request_client.transport.send(
            "GET", target_url, headers=headers, stream=True, follow_redirects=False
        )
    )
    if response.status_code == 404:
        response.close()
        raise BlobNotFoundError("not found")
    if response.status_code >= 400:
        response.close()
        raise BlobError(f"request failed with status {response.status_code}")

    class SyncStream:
        def __init__(self, response):
            self._response = response
            self._closed = False

        def __iter__(self):
            for chunk in self._response.iter_bytes(chunk_size=65536):
                if chunk:
                    yield chunk

        def close(self):
            if not self._closed:
                self._closed = True
                self._response.close()

    download = SyncStream(response)
    try:
        yield download
    finally:
        download.close()


# sync multipart
class SyncMultipartUpload:
    def __init__(
        self,
        path,
        access,
        *,
        content_type=None,
        add_random_suffix=False,
        allow_overwrite=False,
        cache_control_max_age=None,
        session=None,
    ):
        self.path = path
        self.access = access
        self.content_type = content_type
        self.add_random_suffix = add_random_suffix
        self.allow_overwrite = allow_overwrite
        self.cache_control_max_age = cache_control_max_age
        self.session = session
        self._ops = None
        self._client = None
        self._token = None
        self._upload_id = None
        self._key = None
        self._headers = None
        self._parts = []
        self._part_sizes = []
        self.result = None
        self._entered = False
        self._finished = False

    def __enter__(self):
        validate_pathname(self.path, upload=True)
        from khulnasoft._internal.blob import validate_access

        validate_access(self.access)
        self._ops = get_sync_ops(self.session)
        from khulnasoft._internal.core.iter_coroutine import iter_coroutine

        self._token = iter_coroutine(self._ops._request_client.resolve_token(None))
        self._client = self._ops._multipart_client
        from khulnasoft._internal.blob.multipart import prepare_upload_headers

        self._headers = prepare_upload_headers(
            access=self.access,
            content_type=self.content_type,
            add_random_suffix=self.add_random_suffix,
            overwrite=self.allow_overwrite,
            cache_control_max_age=self.cache_control_max_age,
        )
        response = iter_coroutine(
            self._client.create_multipart_upload(self.path, self._headers, token=self._token)
        )
        self._upload_id = response["uploadId"]
        self._key = response["key"]
        self._entered = True
        return self

    def _body_size(self, body, content_length):
        if isinstance(body, (bytes, bytearray, memoryview)):
            size = len(body)
        elif isinstance(body, str):
            size = len(body.encode())
        else:
            if content_length is None:
                raise BlobContentLengthError("content_length is required for streaming parts")
            size = content_length
        if size < 1 or size > 5 * 1024 * 1024 * 1024:
            raise BlobError("part size must be between 1 byte and 5 GiB")
        return size

    def upload_part(self, body, *, content_length=None):
        if not self._entered or self._finished:
            raise BlobError("upload_part must be called inside the multipart context")
        if len(self._parts) >= 10000:
            raise BlobError("multipart upload supports at most 10000 parts")
        size = self._body_size(body, content_length)
        if self._part_sizes and self._part_sizes[-1] < 5 * 1024 * 1024:
            raise BlobError("every part except the last must be at least 5 MiB")
        from khulnasoft._internal.core.iter_coroutine import iter_coroutine

        assert self._client is not None
        response = iter_coroutine(
            self._client.upload_part(
                upload_id=self._upload_id,
                key=self._key,
                path=self.path,
                headers=self._headers,
                part_number=len(self._parts) + 1,
                body=body,
                token=self._token,
            )
        )
        self._parts.append({"partNumber": len(self._parts) + 1, "etag": response["etag"]})
        self._part_sizes.append(size)

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self._finished = True
            return
        if not self._parts:
            self._finished = True
            raise BlobError("multipart upload requires at least one part")
        for size in self._part_sizes[:-1]:
            if size < 5 * 1024 * 1024:
                raise BlobError("every part except the last must be at least 5 MiB")
        from khulnasoft._internal.blob.core import build_put_blob_result
        from khulnasoft._internal.core.iter_coroutine import iter_coroutine

        assert self._client is not None
        response = iter_coroutine(
            self._client.complete_multipart_upload(
                upload_id=self._upload_id,
                key=self._key,
                path=self.path,
                headers=self._headers,
                parts=self._parts,
                token=self._token,
            )
        )
        self.result = build_put_blob_result(response)
        self._finished = True
        # convert to public PutResult
        from .types import PutResult

        self.result = PutResult(
            url=self.result.url,
            download_url=self.result.download_url,
            pathname=self.result.pathname,
            content_type=self.result.content_type,
            content_disposition=self.result.content_disposition,
            etag=self.result.etag or "",
        )
        return False


def multipart_upload_blob(
    path,
    *,
    access,
    content_type=None,
    add_random_suffix=False,
    allow_overwrite=False,
    cache_control_max_age=None,
    session=None,
):
    return SyncMultipartUpload(
        path,
        access,
        content_type=content_type,
        add_random_suffix=add_random_suffix,
        allow_overwrite=allow_overwrite,
        cache_control_max_age=cache_control_max_age,
        session=session,
    )
