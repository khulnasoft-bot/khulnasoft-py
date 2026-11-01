from __future__ import annotations

from collections.abc import Mapping

import pytest

from khulnasoft.headers import geolocation, ip_address

CITY_HEADER = "x-khulnasoft-ip-city"
COUNTRY_HEADER = "x-khulnasoft-ip-country"
LATITUDE_HEADER = "x-khulnasoft-ip-latitude"
LONGITUDE_HEADER = "x-khulnasoft-ip-longitude"
POSTAL_CODE_HEADER = "x-khulnasoft-ip-postal-code"
REGION_HEADER = "x-khulnasoft-ip-country-region"
REQUEST_ID_HEADER = "x-khulnasoft-id"


class FakeRequest:
    def __init__(self, headers: Mapping[str, str]) -> None:
        self.headers = headers


def test_ip_address_accepts_headers_mapping() -> None:
    assert ip_address({"x-real-ip": "203.0.113.10"}) == "203.0.113.10"
    assert ip_address({"x-real-ip": ""}) == ""
    assert ip_address({}) is None


def test_ip_address_accepts_request_object() -> None:
    request = FakeRequest({"x-real-ip": "198.51.100.7"})
    assert ip_address(request) == "198.51.100.7"


def test_geolocation_reads_and_decodes_headers() -> None:
    request = FakeRequest(
        {
            CITY_HEADER: "S%C3%A3o%20Paulo",
            COUNTRY_HEADER: "br",
            REGION_HEADER: "SP",
            LATITUDE_HEADER: "-23.5505",
            LONGITUDE_HEADER: "-46.6333",
            POSTAL_CODE_HEADER: "01000-000",
            REQUEST_ID_HEADER: "gru1::abc123",
        }
    )

    assert geolocation(request) == {
        "city": "São Paulo",
        "country": "br",
        "flag": "🇧🇷",
        "countryRegion": "SP",
        "region": "gru1",
        "latitude": "-23.5505",
        "longitude": "-46.6333",
        "postalCode": "01000-000",
    }


def test_geolocation_defaults_region_without_request_id() -> None:
    assert geolocation(FakeRequest({})) == {
        "city": None,
        "country": None,
        "flag": None,
        "countryRegion": None,
        "region": "dev1",
        "latitude": None,
        "longitude": None,
        "postalCode": None,
    }


@pytest.mark.parametrize("country", ["USA", "u1", "1x", ""])
def test_geolocation_ignores_invalid_country_codes(country: str) -> None:
    assert geolocation(FakeRequest({COUNTRY_HEADER: country}))["flag"] is None
