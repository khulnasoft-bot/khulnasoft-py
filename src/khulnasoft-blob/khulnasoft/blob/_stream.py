from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from khulnasoft._internal.blob import (
    construct_blob_url,
    extract_store_id_from_token,
)
from khulnasoft._internal.blob.core import AsyncBlobOpsClient

from ._runtime import get_async_ops
from ._validation import validate_delivery_url, validate_pathname
from .errors import BlobError, BlobNotFoundError


class AsyncStreamDownload:
    def __init__(self, response: Any, ops: AsyncBlobOpsClient) -> None:
        self._response = response
        self._ops = ops
        self.metadata = None
        self._closed = False

    @property
    def response(self) -> Any:
        return self._response

    async def __aiter__(self) -> Any:
        async for chunk in self._response.aiter_bytes(chunk_size=65536):
            if chunk:
                yield chunk

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            await self._response.aclose()


@asynccontextmanager
async def stream_blob(pathname_or_url: str, *, access: str, session: Any = None):
    if pathname_or_url.startswith(("http://", "https://")):
        validate_delivery_url(pathname_or_url)
    else:
        validate_pathname(pathname_or_url)
    ops = await get_async_ops(session)
    token = await ops._request_client.resolve_token(None)
    if pathname_or_url.startswith(("http://", "https://")):
        target_url = pathname_or_url
    else:
        store_id = extract_store_id_from_token(token)
        if store_id:
            target_url = construct_blob_url(store_id, pathname_or_url.lstrip("/"), access)
        else:
            head = await ops.head_blob(pathname_or_url, token=token)
            target_url = head.url
    headers = {}
    if access == "private":
        headers["authorization"] = f"Bearer {token}"
    response = await ops._request_client.transport.send(
        "GET",
        target_url,
        headers=headers,
        stream=True,
        follow_redirects=False,
    )
    if response.status_code == 404:
        await response.aclose()
        raise BlobNotFoundError("not found")
    if response.status_code >= 400:
        await response.aclose()
        raise BlobError(f"request failed with status {response.status_code}")
    download = AsyncStreamDownload(response, ops)
    try:
        yield download
    finally:
        await download.aclose()
