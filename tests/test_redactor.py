"""Tests for RedactingFilter."""

import pytest

from agent_logger import RedactingFilter
from agent_logger.redactor import REDACTED


class TestRedactingFilter:
    def test_default_fields_are_redacted(self):
        rf = RedactingFilter()
        record = {
            "api_key": "sk-abc",
            "token": "tok-xyz",
            "password": "hunter2",
            "secret": "shhh",
            "authorization": "Bearer abc",
            "user": "alice",
        }
        result = rf.filter(record)
        assert result["api_key"] == REDACTED
        assert result["token"] == REDACTED
        assert result["password"] == REDACTED
        assert result["secret"] == REDACTED
        assert result["authorization"] == REDACTED
        assert result["user"] == "alice"  # non-sensitive unchanged

    def test_custom_fields(self):
        rf = RedactingFilter(fields=["my_secret_field"])
        record = {"my_secret_field": "do-not-show", "safe": "show-me"}
        result = rf.filter(record)
        assert result["my_secret_field"] == REDACTED
        assert result["safe"] == "show-me"

    def test_does_not_mutate_original(self):
        rf = RedactingFilter()
        original = {"api_key": "sk-abc", "msg": "hello"}
        rf.filter(original)
        assert original["api_key"] == "sk-abc"  # original unchanged

    def test_non_sensitive_fields_passthrough(self):
        rf = RedactingFilter()
        record = {"model": "gpt-4", "latency_ms": 123, "tokens": 500}
        result = rf.filter(record)
        assert result == {"model": "gpt-4", "latency_ms": 123, "tokens": 500}

    def test_empty_record(self):
        rf = RedactingFilter()
        assert rf.filter({}) == {}

    def test_nested_dict_redaction(self):
        rf = RedactingFilter()
        record = {"meta": {"api_key": "sk-nested", "model": "gpt-4"}}
        result = rf.filter(record)
        assert result["meta"]["api_key"] == REDACTED
        assert result["meta"]["model"] == "gpt-4"

    def test_list_values_processed(self):
        rf = RedactingFilter(fields=["secret"])
        record = {"items": [{"secret": "abc"}, {"safe": "xyz"}]}
        result = rf.filter(record)
        assert result["items"][0]["secret"] == REDACTED
        assert result["items"][1]["safe"] == "xyz"
