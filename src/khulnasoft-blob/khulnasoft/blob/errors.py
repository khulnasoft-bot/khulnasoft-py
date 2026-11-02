from __future__ import annotations

from enum import Enum


class BlobError(Exception):
    def __init__(
        self, message: str, *, status_code: int | None = None, code: str | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class BlobNotFoundError(BlobError):
    pass


class BlobAccessError(BlobError):
    pass


class BlobStoreNotFoundError(BlobError):
    pass


class BlobPreconditionFailedError(BlobError):
    pass


class BlobServiceRateLimited(BlobError):
    pass


class BlobStreamError(BlobError):
    pass


class BlobCredentialsError(BlobError):
    pass


class BlobContentLengthError(BlobError):
    pass


class CredentialKind(str, Enum):
    TOKEN = "token"
    OIDC = "oidc"
