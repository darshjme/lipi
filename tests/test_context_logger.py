"""Tests for ContextLogger."""

import json
import io
import logging

import pytest

from agent_logger import AgentLogger, ContextLogger, CorrelationContext
from agent_logger.logger import _JSONFormatter


def _capture_logger(name: str):
    buf = io.StringIO()
    logger = AgentLogger(name, level="DEBUG", output="stdout")
    handler = logging.StreamHandler(buf)
    handler.setFormatter(_JSONFormatter())
    handler.setLevel(logging.DEBUG)
    logger._logger.handlers = [handler]
    return logger, buf


class TestContextLogger:
    def setup_method(self):
        CorrelationContext.clear()

    def teardown_method(self):
        CorrelationContext.clear()

    def test_context_fields_injected(self):
        logger, buf = _capture_logger("ctx-inject")
        ctx = logger.with_context(agent="router", env="prod")
        ctx.info("routing request")
        record = json.loads(buf.getvalue().strip())
        assert record["agent"] == "router"
        assert record["env"] == "prod"
        assert record["message"] == "routing request"

    def test_bind_returns_new_instance(self):
        logger, _ = _capture_logger("ctx-bind")
        ctx1 = logger.with_context(a=1)
        ctx2 = ctx1.bind(b=2)
        assert ctx1 is not ctx2
        assert ctx2._fields["a"] == 1
        assert ctx2._fields["b"] == 2

    def test_bind_is_immutable(self):
        """Binding ctx2 from ctx1 should not affect ctx1's fields."""
        logger, buf = _capture_logger("ctx-immutable")
        ctx1 = logger.with_context(a=1)
        ctx2 = ctx1.bind(b=2)

        ctx1.info("from ctx1")
        line1 = buf.getvalue().strip().splitlines()[-1]
        rec1 = json.loads(line1)
        assert "b" not in rec1

    def test_chained_bind(self):
        logger, buf = _capture_logger("ctx-chain")
        ctx = (
            logger.with_context(level1="a")
            .bind(level2="b")
            .bind(level3="c")
        )
        ctx.info("deep chain")
        record = json.loads(buf.getvalue().strip())
        assert record["level1"] == "a"
        assert record["level2"] == "b"
        assert record["level3"] == "c"

    def test_kwargs_override_context(self):
        """Per-call kwargs should override bound context fields."""
        logger, buf = _capture_logger("ctx-override")
        ctx = logger.with_context(model="gpt-3")
        ctx.info("upgraded", model="gpt-4")
        record = json.loads(buf.getvalue().strip())
        assert record["model"] == "gpt-4"

    def test_correlation_id_flows_through(self):
        logger, buf = _capture_logger("ctx-cid")
        CorrelationContext.set("trace-999")
        ctx = logger.with_context(agent="fetcher")
        ctx.info("fetching")
        record = json.loads(buf.getvalue().strip())
        assert record["correlation_id"] == "trace-999"

    def test_all_log_levels_on_context_logger(self):
        for lvl in ("debug", "warning", "error", "critical"):
            logger, buf = _capture_logger(f"ctx-{lvl}")
            ctx = logger.with_context(x=1)
            getattr(ctx, lvl)("test")
            line = buf.getvalue().strip()
            assert line, f"Expected output for level {lvl}"
            record = json.loads(line)
            assert record["level"] == lvl.upper()
