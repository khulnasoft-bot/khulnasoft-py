from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .errors import CredentialKind


@dataclass(frozen=True, slots=True)
class BlobCredentials:
    token: str
    store_id: str = ""
    kind: CredentialKind = CredentialKind.TOKEN


@dataclass(frozen=True, slots=True)
class DownloadMetadata:
    url: str
    status_code: int
    size: int | None = None
    content_type: str | None = None
    content_disposition: str | None = None
    cache_control: str | None = None
    etag: str | None = None
    last_modified: datetime | None = None
    uploaded_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PutResult:
    url: str
    download_url: str
    pathname: str
    content_type: str
    content_disposition: str
    etag: str


@dataclass(frozen=True, slots=True)
class GetResult:
    metadata: DownloadMetadata
    body: bytes


@dataclass(frozen=True, slots=True)
class HeadResult:
    size: int | None
    uploaded_at: datetime | None
    pathname: str
    content_type: str | None
    content_disposition: str | None
    url: str
    download_url: str
    cache_control: str | None
    etag: str | None = None


@dataclass(frozen=True, slots=True)
class ListBlob:
    url: str
    download_url: str
    pathname: str
    size: int
    uploaded_at: datetime | None
    etag: str | None = None


@dataclass(frozen=True, slots=True)
class BlobPrefix:
    prefix: str


@dataclass(frozen=True, slots=True)
class CopyResult:
    url: str
    download_url: str
    pathname: str
    content_type: str
    content_disposition: str
    etag: str


Access = Literal["public", "private"]
