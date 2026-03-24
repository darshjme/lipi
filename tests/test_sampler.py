"""Tests for LogSampler and SampledLogger."""

import pytest

from agent_logger import LogSampler


class TestLogSampler:
    def test_rate_1_always_logs(self):
        sampler = LogSampler(rate=1.0)
        assert all(sampler.should_log() for _ in range(100))

    def test_rate_0_never_logs(self):
        sampler = LogSampler(rate=0.0)
        assert not any(sampler.should_log() for _ in range(100))

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError):
            LogSampler(rate=1.5)
        with pytest.raises(ValueError):
            LogSampler(rate=-0.1)

    def test_fractional_rate_statistical(self):
        """At rate=0.5, roughly half the calls should return True over 1000 samples."""
        sampler = LogSampler(rate=0.5)
        hits = sum(1 for _ in range(1000) if sampler.should_log())
        # Expect between 350 and 650 (very wide band to avoid flakiness)
        assert 300 <= hits <= 700, f"unexpected hit count: {hits}"


class TestSampledLogger:
    def test_wrap_returns_sampled_logger(self):
        from agent_logger import AgentLogger
        from agent_logger.sampler import SampledLogger
        import io, sys

        logger = AgentLogger("sampled-test", output="stdout")
        sampler = LogSampler(rate=1.0)
        sl = sampler.wrap(logger)
        assert isinstance(sl, SampledLogger)

    def test_sampled_logger_rate0_emits_nothing(self, capsys):
        from agent_logger import AgentLogger

        logger = AgentLogger("sampled-zero", output="stdout")
        sampler = LogSampler(rate=0.0)
        sl = sampler.wrap(logger)
        for _ in range(20):
            sl.info("should not appear")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_sampled_logger_rate1_emits_all(self, capsys):
        from agent_logger import AgentLogger

        logger = AgentLogger("sampled-full", output="stdout")
        sampler = LogSampler(rate=1.0)
        sl = sampler.wrap(logger)
        sl.info("hello sampled")
        captured = capsys.readouterr()
        assert "hello sampled" in captured.out
