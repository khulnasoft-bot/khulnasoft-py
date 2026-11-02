from __future__ import annotations

from collections.abc import Generator

import pytest

pytest_plugins = ["vendor.respx.plugin"]


@pytest.fixture
def mock_env_clear(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    env_vars_to_clear = [
        "KHULNASOFT_TOKEN",
        "KHULNASOFT_TEAM_ID",
        "KHULNASOFT_PROJECT_ID",
        "BLOB_READ_WRITE_TOKEN",
        "BLOB_STORE_ID",
        "KHULNASOFT_OIDC_TOKEN",
        "KHULNASOFT_OIDC_TOKEN_HEADER",
        "KHULNASOFT_CACHE_API_TOKEN",
        "KHULNASOFT_CACHE_API_URL",
        "KHULNASOFT_URL",
        "KHULNASOFT_ENV",
        "KHULNASOFT_REGION",
    ]
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    import khulnasoft.cache.runtime_cache as runtime_cache
    from khulnasoft.headers import set_headers

    set_headers(None)
    monkeypatch.setattr(runtime_cache, "_cached_cache_instance", None)
    monkeypatch.setattr(runtime_cache, "_cached_async_cache_instance", None)
    yield
    set_headers(None)
