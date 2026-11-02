from __future__ import annotations

from collections.abc import AsyncIterable

from khulnasoft.queue import subscribe


@subscribe(topic="files")
async def archive_file(payload: AsyncIterable[bytes]) -> None:
    size = 0
    async for chunk in payload:
        size += len(chunk)
    print(f"received {size} bytes")
