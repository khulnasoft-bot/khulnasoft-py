"""Unit tests for shared provider protocol utilities."""

from __future__ import annotations

import pytest

from khulnasoft.ai.models.core import params as params_
from khulnasoft.ai.providers._protocol_common import (
    filter_extra_headers,
    is_default,
    not_default,
    seed_value,
    tool_ref_name,
)


class TestIsDefault:
    def test_sentinel_is_default(self):
        assert is_default(params_.DEFAULT) is True

    def test_plain_values_are_not_default(self):
        assert is_default("foo") is False
        assert is_default(42) is False
        assert is_default(None) is False
        assert is_default(0) is False
        assert is_default(params_.GLOBAL) is False
        assert is_default(params_.RANDOM) is False
        assert is_default(params_.UNSET) is False


class TestNotDefault:
    def test_plain_values_are_not_default(self):
        assert not_default("foo") is True
        assert not_default(42) is True
        assert not_default(None) is True

    def test_sentinel_is_not_default(self):
        assert not_default(params_.DEFAULT) is False


class TestSeedValue:
    def test_none_returns_none(self):
        assert seed_value(None) is None

    def test_minus_one_returns_none(self):
        assert seed_value(-1) is None

    def test_random_returns_none(self):
        assert seed_value(params_.RANDOM) is None

    def test_default_returns_none(self):
        assert seed_value(params_.DEFAULT) is None

    def test_int_returns_int(self):
        assert seed_value(42) == 42
        assert seed_value(0) == 0

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            seed_value("not-a-seed")


class TestFilterExtraHeaders:
    def test_none_returns_none(self):
        assert filter_extra_headers(None) is None

    def test_drops_unset_values(self):
        headers: dict[str, str | params_.Unset] = {
            "X-A": "foo",
            "X-B": params_.UNSET,
            "X-C": "bar",
        }
        assert filter_extra_headers(headers) == {"X-A": "foo", "X-C": "bar"}

    def test_all_unset_returns_empty(self):
        headers = {"X-A": params_.UNSET, "X-B": params_.UNSET}
        assert filter_extra_headers(headers) == {}

    def test_empty_dict_returns_empty(self):
        assert filter_extra_headers({}) == {}


class TestToolRefName:
    def test_string_passthrough(self):
        assert tool_ref_name("my-tool") == "my-tool"

    def test_tool_ref_str(self):
        assert tool_ref_name(params_.ToolRef("my-tool")) == "my-tool"
