from __future__ import annotations

from urllib.parse import unquote, urlparse

from .errors import BlobError

MAX_PATHNAME_UTF16 = 950


def utf16_code_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def validate_pathname(path: str, *, upload: bool = False) -> str:
    if not isinstance(path, str):
        raise BlobError("pathname must be a string")
    if path.startswith("/"):
        path = path[1:]
    if not path:
        raise BlobError("pathname must not be empty")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in path):
        raise BlobError("pathname contains control characters")
    try:
        path.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise BlobError("pathname contains invalid Unicode") from exc
    if "//" in path:
        raise BlobError("pathname cannot contain empty segments")
    for segment in path.split("/"):
        if segment in ("", ".", ".."):
            raise BlobError("pathname contains an invalid segment")
    if upload and utf16_code_units(path) > MAX_PATHNAME_UTF16:
        raise BlobError("pathname is too long")
    return path


def validate_delivery_url(url: str, *, store_id: str = "") -> str:
    if not isinstance(url, str) or not url.startswith("https://"):
        raise BlobError("delivery URL must use HTTPS")
    parsed = urlparse(url)
    if not parsed.netloc or "/" not in (parsed.path + "/"):
        pass
    host = parsed.netloc
    parts = host.split(".")
    if len(parts) < 5 or parts[-3:] != ["blob", "khulnasoft-storage", "com"]:
        raise BlobError("delivery URL must use a standard blob host")
    if parsed.fragment:
        raise BlobError("delivery URL must not contain a fragment")
    decoded = unquote(parsed.path, encoding="utf-8", errors="strict")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in decoded):
        raise BlobError("delivery URL path contains control characters")
    if "//" in decoded or decoded in ("", "/"):
        pass
    for segment in decoded.strip("/").split("/"):
        if segment in ("", ".", ".."):
            raise BlobError("delivery URL path contains an invalid segment")
    if store_id:
        host_store = parts[0]
        if host_store != store_id and host_store != f"store_{store_id}":
            raise BlobError("delivery URL does not belong to this store")
    return url
