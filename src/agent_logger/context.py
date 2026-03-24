"""
ContextLogger — immutable logger with bound context fields.
"""

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .logger import AgentLogger


class ContextLogger:
    """Logger that merges a fixed set of fields into every log line.

    Immutable: each call to bind() returns a NEW ContextLogger.

    Args:
        parent: The underlying AgentLogger (or another ContextLogger).
        **fields: Key-value pairs to inject into every log record.
    """

    def __init__(self, parent: "AgentLogger", **fields: Any) -> None:
        self._parent = parent
        self._fields: Dict[str, Any] = dict(fields)

    # ------------------------------------------------------------------
    # Chaining
    # ------------------------------------------------------------------

    def bind(self, **kwargs: Any) -> "ContextLogger":
        """Return a new ContextLogger with additional bound fields."""
        merged = {**self._fields, **kwargs}
        return ContextLogger(self._parent, **merged)

    # ------------------------------------------------------------------
    # Delegation — forward to parent after injecting bound context
    # ------------------------------------------------------------------

    def _emit(self, level: str, message: str, **kwargs: Any) -> None:
        merged = {**self._fields, **kwargs}
        self._parent._emit(level, message, **merged)

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

    # ------------------------------------------------------------------
    # Passthrough helpers
    # ------------------------------------------------------------------

    def set_correlation_id(self, id: str) -> None:
        self._parent.set_correlation_id(id)

    def get_correlation_id(self):
        return self._parent.get_correlation_id()

    def with_context(self, **kwargs: Any) -> "ContextLogger":
        """Return a new ContextLogger layered on top of this one."""
        return self.bind(**kwargs)
