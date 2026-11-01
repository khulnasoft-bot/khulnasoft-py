"""Test-only encoder for constructing plain workflow payloads."""

from khulnasoft.workflow._internal import serialization

PLAIN_ENCODER = serialization.PayloadEncoder()
