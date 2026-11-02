from __future__ import annotations

from typing import Any

from khulnasoft._internal.blob import validate_access
from khulnasoft._internal.blob.core import build_put_blob_result
from khulnasoft._internal.blob.multipart import MultipartClient, prepare_upload_headers

from ._runtime import get_async_ops
from ._validation import validate_pathname
from .errors import BlobContentLengthError, BlobError


class AsyncMultipartUpload:
    def __init__(
        self,
        path: str,
        access: str,
        *,
        content_type=None,
        add_random_suffix=True,
        allow_overwrite=False,
        cache_control_max_age=None,
        session=None,
    ) -> None:
        self.path = path
        self.access = access
        self.content_type = content_type
        self.add_random_suffix = add_random_suffix
        self.allow_overwrite = allow_overwrite
        self.cache_control_max_age = cache_control_max_age
        self.session = session
        self._client: MultipartClient | None = None
        self._token: str | None = None
        self._upload_id: str | None = None
        self._key: str | None = None
        self._headers: dict[str, Any] | None = None
        self._parts: list[dict[str, Any]] = []
        self._part_sizes: list[int] = []
        self.result: Any = None
        self._entered = False
        self._finished = False

    async def __aenter__(self) -> AsyncMultipartUpload:
        validate_pathname(self.path, upload=True)
        validate_access(self.access)
        ops = await get_async_ops(self.session)
        self._token = await ops._request_client.resolve_token(None)
        self._client = ops._multipart_client
        self._headers = prepare_upload_headers(
            access=self.access,
            content_type=self.content_type,
            add_random_suffix=self.add_random_suffix,
            overwrite=self.allow_overwrite,
            cache_control_max_age=self.cache_control_max_age,
        )
        response = await self._client.create_multipart_upload(
            self.path, self._headers, token=self._token
        )
        self._upload_id = response["uploadId"]
        self._key = response["key"]
        self._entered = True
        return self

    def _body_size(self, body: Any, content_length: int | None) -> int:
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

    async def upload_part(self, body: Any, *, content_length: int | None = None) -> None:
        if not self._entered or self._finished:
            raise BlobError("upload_part must be called inside the multipart context")
        if len(self._parts) >= 10000:
            raise BlobError("multipart upload supports at most 10000 parts")
        size = self._body_size(body, content_length)
        # previous part must be at least 5 MiB if another part follows
        if self._part_sizes and self._part_sizes[-1] < 5 * 1024 * 1024:
            raise BlobError("every part except the last must be at least 5 MiB")
        assert self._client is not None
        response = await self._client.upload_part(
            upload_id=self._upload_id,
            key=self._key,
            path=self.path,
            headers=self._headers,
            part_number=len(self._parts) + 1,
            body=body,
            token=self._token,
        )
        self._parts.append({"partNumber": len(self._parts) + 1, "etag": response["etag"]})
        self._part_sizes.append(size)

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self._finished = True
            return
        if not self._parts:
            self._finished = True
            raise BlobError("multipart upload requires at least one part")
        assert self._client is not None
        # validate non-last parts
        for size in self._part_sizes[:-1]:
            if size < 5 * 1024 * 1024:
                raise BlobError("every part except the last must be at least 5 MiB")
        response = await self._client.complete_multipart_upload(
            upload_id=self._upload_id,
            key=self._key,
            path=self.path,
            headers=self._headers,
            parts=self._parts,
            token=self._token,
        )

        raw = response
        self.result = build_put_blob_result(raw)
        self._finished = True


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
    return AsyncMultipartUpload(
        path,
        access,
        content_type=content_type,
        add_random_suffix=add_random_suffix,
        allow_overwrite=allow_overwrite,
        cache_control_max_age=cache_control_max_age,
        session=session,
    )
