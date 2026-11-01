from __future__ import annotations

import asyncio
import time
from typing import Any

from khulnasoft._internal.blob.core import (
    AsyncBlobOpsClient,
    BlobRequestClient,
    RetryPolicy,
    SyncBlobOpsClient,
    _retry_on_blob_response,
    get_retries,
)
from khulnasoft._internal.blob.multipart import (
    MultipartClient,
    create_async_multipart_upload_runtime,
    create_sync_multipart_upload_runtime,
)
from khulnasoft._internal.core.session import SdkSession, SyncSdkSession

from .options import (
    BlobServiceOptions,
    SyncBlobServiceOptions,
)


def _async_session(sess: Any = None) -> SdkSession:
    if sess is None:
        return SdkSession.default()
    return sess


def _sync_session(sess: Any = None) -> SyncSdkSession:
    if sess is None:
        return SyncSdkSession.default()
    return sess


async def get_async_ops(session: Any = None) -> AsyncBlobOpsClient:
    sess = _async_session(session)
    from khulnasoft._internal.core.session import SdkSession

    if not isinstance(sess, SdkSession):
        raise TypeError("async session required")
    options = sess.get_service_option(BlobServiceOptions)
    if options is None:
        options = BlobServiceOptions()
    creds = await options.credentials_factory()

    transport = sess.get_transport()

    retry = RetryPolicy(retries=get_retries(), retry_on_response=_retry_on_blob_response)
    request_client = BlobRequestClient(
        transport=transport,
        retry=retry,
        sleep_fn=asyncio.sleep,
        token_provider=lambda: _resolve_token(options, creds),
        await_progress_callback=True,
        async_content=True,
    )
    ops = AsyncBlobOpsClient.__new__(AsyncBlobOpsClient)
    ops._request_client = request_client
    ops._multipart_client = MultipartClient(request_client)
    ops._multipart_runtime = create_async_multipart_upload_runtime()
    return ops


async def _resolve_token(options: Any, creds: Any) -> str:
    return creds.token


def get_sync_ops(session: Any = None) -> SyncBlobOpsClient:
    sess = _sync_session(session)
    options = sess.get_service_option(SyncBlobServiceOptions)
    if options is None:
        options = SyncBlobServiceOptions()
    creds = options.credentials_factory()

    transport = sess.get_transport()

    retry = RetryPolicy(retries=get_retries(), retry_on_response=_retry_on_blob_response)
    request_client = BlobRequestClient(
        transport=transport,
        retry=retry,
        sleep_fn=time.sleep,
        token_provider=lambda: creds.token,
        await_progress_callback=False,
        async_content=False,
    )
    ops = SyncBlobOpsClient.__new__(SyncBlobOpsClient)
    ops._request_client = request_client
    ops._multipart_client = MultipartClient(request_client)
    ops._multipart_runtime = create_sync_multipart_upload_runtime()
    return ops
