"""
AgentLogger — structured JSON logger for LLM agents.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .correlation import CorrelationContext
from .redactor import RedactingFilter

_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class _JSONFormatter(logging.Formatter):
    """Formats a LogRecord as a JSON string."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = record.__dict__.get("_agent_payload", {})
        return json.dumps(payload, default=str)


class AgentLogger:
    """Structured JSON logger for LLM agents.

    Args:
        name:        Logger name (appears in every log line).
        level:       Minimum log level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        output:      Where to write logs ("stdout" or a file path).
        json_format: If True emit JSON; if False emit a plain text line.
        redacting_filter: Optional RedactingFilter applied to every record.
    """

    def __init__(
        self,
        name: str,
        level: str = "INFO",
        output: str = "stdout",
        json_format: bool = True,
        redacting_filter: Optional[RedactingFilter] = None,
    ) -> None:
        self.name = name
        self.json_format = json_format
        self.redacting_filter = redacting_filter

        # resolve numeric level
        numeric_level = _LEVEL_MAP.get(level.upper(), logging.INFO)

        # build an internal stdlib logger with a unique name to avoid clashes
        internal_name = f"agent_logger.{name}.{id(self)}"
        self._logger = logging.getLogger(internal_name)
        self._logger.setLevel(numeric_level)
        self._logger.propagate = False

        # remove any existing handlers (e.g., if name collides)
        self._logger.handlers.clear()

        # output stream / file
        if output == "stdout":
            handler = logging.StreamHandler(sys.stdout)
        elif output == "stderr":
            handler = logging.StreamHandler(sys.stderr)
        else:
            handler = logging.FileHandler(output, encoding="utf-8")

        handler.setLevel(numeric_level)

        if json_format:
            handler.setFormatter(_JSONFormatter())
        else:
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
            )

        self._logger.addHandler(handler)

    # ------------------------------------------------------------------
    # Correlation ID helpers
    # ------------------------------------------------------------------

    def set_correlation_id(self, id: str) -> None:
        """Set correlation ID for the current thread."""
        CorrelationContext.set(id)

    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID for the current thread."""
        return CorrelationContext.get()

    # ------------------------------------------------------------------
    # Context binding
    # ------------------------------------------------------------------

    def with_context(self, **kwargs: Any) -> "ContextLogger":
        """Return a ContextLogger with bound fields merged into every log line."""
        from .context import ContextLogger  # avoid circular at module level
        return ContextLogger(self, **kwargs)

    # ------------------------------------------------------------------
    # Internal emit
    # ------------------------------------------------------------------

    def _build_record(self, level: str, message: str, **kwargs: Any) -> Dict[str, Any]:
        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "name": self.name,
            "message": message,
            "correlation_id": CorrelationContext.get(),
        }
        record.update(kwargs)

        if self.redacting_filter is not None:
            record = self.redacting_filter.filter(record)

        return record

    def _emit(self, level: str, message: str, **kwargs: Any) -> None:
        log_level = _LEVEL_MAP.get(level, logging.INFO)

        # honour the logger's effective level — skip if too low
        if not self._logger.isEnabledFor(log_level):
            return

        record = self._build_record(level, message, **kwargs)

        if self.json_format:
            lr = logging.LogRecord(
                name=self._logger.name,
                level=log_level,
                pathname="",
                lineno=0,
                msg="",
                args=(),
                exc_info=None,
            )
            lr._agent_payload = record  # type: ignore[attr-defined]
            self._logger.handle(lr)
        else:
            self._logger.log(log_level, message)

    # ------------------------------------------------------------------
    # Public log methods
    # ------------------------------------------------------------------

    def debug(self, message: str, **kwargs: Any) -> None:
        self._emit("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._emit("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._emit("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._emit("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._emit("CRITICAL", message, **kwargs)
