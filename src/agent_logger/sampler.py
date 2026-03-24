"""
LogSampler — probabilistic log sampling for high-volume agents.
"""

import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .logger import AgentLogger


class LogSampler:
    """Decides probabilistically whether a log record should be emitted.

    Args:
        rate: Float in [0.0, 1.0]. 1.0 = log everything, 0.0 = log nothing.
    """

    def __init__(self, rate: float = 1.0) -> None:
        if not (0.0 <= rate <= 1.0):
            raise ValueError(f"rate must be between 0.0 and 1.0, got {rate}")
        self.rate = rate

    def should_log(self) -> bool:
        """Return True if this record should be emitted."""
        if self.rate >= 1.0:
            return True
        if self.rate <= 0.0:
            return False
        return random.random() < self.rate

    def wrap(self, logger: "AgentLogger") -> "SampledLogger":
        """Wrap an AgentLogger so that only ~rate fraction of calls are logged."""
        return SampledLogger(logger, self)


class SampledLogger:
    """A thin wrapper around AgentLogger that applies a LogSampler gate.

    Args:
        logger:  The underlying AgentLogger.
        sampler: The LogSampler controlling emit probability.
    """

    def __init__(self, logger: "AgentLogger", sampler: LogSampler) -> None:
        self._logger = logger
        self._sampler = sampler

    def debug(self, message: str, **kwargs: Any) -> None:
        if self._sampler.should_log():
            self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        if self._sampler.should_log():
            self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        if self._sampler.should_log():
            self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        if self._sampler.should_log():
            self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        if self._sampler.should_log():
            self._logger.critical(message, **kwargs)
