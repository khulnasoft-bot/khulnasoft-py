"""Live smoke tests against a real connector.

Requires a linked project with an attached connector:

    khulnasoft link && khulnasoft env pull
    export KHULNASOFT_CONNECT_TEST_CONNECTOR=slack/my-bot
    uv run poe test khulnasoft-connect -- -m live
"""

import os

import pytest

from khulnasoft.connect import (
    ConnectAppTokenSubject,
    get_connector_metadata,
    get_token_response,
    sync as connect_sync,
)

pytestmark = pytest.mark.live

CONNECTOR = os.environ.get("KHULNASOFT_CONNECT_TEST_CONNECTOR", "")


@pytest.fixture(autouse=True)
def require_connector() -> None:
    if not CONNECTOR:
        pytest.skip("set KHULNASOFT_CONNECT_TEST_CONNECTOR to run live Connect tests")


async def test_live_mints_a_token_async() -> None:
    response = await get_token_response(CONNECTOR, subject=ConnectAppTokenSubject())

    assert response.token
    assert response.expires_at
    assert response.connector.uid


def test_live_mints_a_token_sync() -> None:
    response = connect_sync.get_token_response(CONNECTOR, subject=ConnectAppTokenSubject())

    assert response.token


async def test_live_reads_connector_metadata() -> None:
    metadata = await get_connector_metadata(CONNECTOR)

    assert metadata.id
    assert metadata.uid
