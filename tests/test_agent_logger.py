"""Tests for AgentLogger."""

import json
import io
import sys

import pytest

from agent_logger import AgentLogger, CorrelationContext


def _capture_logger(name: str, level: str = "DEBUG") -> tuple:
    """Return (logger, captured_lines_list).

    The logger writes JSON to a StringIO that we can inspect.
    We monkey-patch stdout capture via a real handler pointing at our buffer.
    """
    import logging
    buf = io.StringIO()
    logger = AgentLogger(name, level=level, output="stdout")
    # Redirect the last handler to our buffer
    handler = logging.StreamHandler(buf)
    from agent_logger.logger import _JSONFormatter
    handler.setFormatter(_JSONFormatter())
    handler.setLevel(logging.DEBUG)
    logger._logger.handlers = [handler]
    return logger, buf


class TestAgentLogger:
    def setup_method(self):
        CorrelationContext.clear()

    def teardown_method(self):
        CorrelationContext.clear()

    def test_info_produces_valid_json(self):
        logger, buf = _capture_logger("test-info")
        logger.info("hello world")
        line = buf.getvalue().strip()
        record = json.loads(line)
        assert record["level"] == "INFO"
        assert record["name"] == "test-info"
        assert record["message"] == "hello world"
        assert "timestamp" in record

    def test_all_levels(self):
        for level_name in ("DEBUG", "WARNING", "ERROR", "CRITICAL"):
            logger, buf = _capture_logger("test-levels", level="DEBUG")
            getattr(logger, level_name.lower())("msg")
            line = buf.getvalue().strip()
            record = json.loads(line)
            assert record["level"] == level_name

    def test_kwargs_in_record(self):
        logger, buf = _capture_logger("test-kwargs")
        logger.info("llm call", model="gpt-4", tokens=500, latency_ms=123)
        record = json.loads(buf.getvalue().strip())
        assert record["model"] == "gpt-4"
        assert record["tokens"] == 500
        assert record["latency_ms"] == 123

    def test_correlation_id_in_record(self):
        logger, buf = _capture_logger("test-cid")
        logger.set_correlation_id("req-abc")
        logger.info("with cid")
        record = json.loads(buf.getvalue().strip())
        assert record["correlation_id"] == "req-abc"

    def test_no_correlation_id_is_none(self):
        logger, buf = _capture_logger("test-no-cid")
        logger.info("no cid")
        record = json.loads(buf.getvalue().strip())
        assert record["correlation_id"] is None

    def test_set_and_get_correlation_id(self):
        logger, _ = _capture_logger("test-cid-rw")
        logger.set_correlation_id("my-id")
        assert logger.get_correlation_id() == "my-id"

    def test_level_filtering(self):
        logger, buf = _capture_logger("test-filter", level="ERROR")
        logger.debug("should be filtered")
        logger.info("also filtered")
        logger.error("this passes")
        lines = [l for l in buf.getvalue().strip().splitlines() if l]
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["level"] == "ERROR"

    def test_redacting_filter_integrated(self):
        import logging
        from agent_logger import RedactingFilter
        from agent_logger.logger import _JSONFormatter

        buf = io.StringIO()
        rf = RedactingFilter()
        logger = AgentLogger("test-redact", output="stdout", redacting_filter=rf)
        handler = logging.StreamHandler(buf)
        handler.setFormatter(_JSONFormatter())
        handler.setLevel(logging.DEBUG)
        logger._logger.handlers = [handler]

        logger.info("secret call", api_key="sk-abc123", model="gpt-4")
        record = json.loads(buf.getvalue().strip())
        assert record["api_key"] == "***REDACTED***"
        assert record["model"] == "gpt-4"

    def test_with_context_returns_context_logger(self):
        from agent_logger import ContextLogger
        logger, _ = _capture_logger("test-ctx")
        ctx = logger.with_context(agent="router")
        assert isinstance(ctx, ContextLogger)
