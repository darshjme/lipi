"""
CorrelationContext — thread-local correlation ID manager.
"""

import threading
import uuid
from contextlib import contextmanager
from typing import Optional

_local = threading.local()


class CorrelationContext:
    """Thread-local correlation ID manager.

    Usage:
        CorrelationContext.set("req-abc-123")
        cid = CorrelationContext.get()

        with CorrelationContext.scope("req-xyz"):
            # correlation ID is set inside, cleared on exit
            ...
    """

    @classmethod
    def set(cls, id: str) -> None:
        """Set correlation ID for the current thread."""
        _local.correlation_id = id

    @classmethod
    def get(cls) -> Optional[str]:
        """Get correlation ID for the current thread. Returns None if not set."""
        return getattr(_local, "correlation_id", None)

    @classmethod
    def generate(cls) -> str:
        """Generate a new UUID4 correlation ID (does NOT set it)."""
        return str(uuid.uuid4())

    @classmethod
    def clear(cls) -> None:
        """Clear the correlation ID for the current thread."""
        if hasattr(_local, "correlation_id"):
            del _local.correlation_id

    @classmethod
    @contextmanager
    def scope(cls, id: str):
        """Context manager: sets correlation ID on enter, restores previous on exit."""
        previous = cls.get()
        cls.set(id)
        try:
            yield id
        finally:
            if previous is None:
                cls.clear()
            else:
                cls.set(previous)
