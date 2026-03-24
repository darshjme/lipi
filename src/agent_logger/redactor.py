"""
RedactingFilter — auto-redact sensitive fields from log records.
"""

from typing import Any, Dict, List, Optional

_DEFAULT_SENSITIVE_FIELDS = [
    "api_key",
    "token",
    "password",
    "secret",
    "authorization",
]

REDACTED = "***REDACTED***"


class RedactingFilter:
    """Post-processor that replaces sensitive field values with REDACTED.

    Usage:
        rf = RedactingFilter(fields=["api_key", "password"])
        safe_record = rf.filter({"user": "alice", "api_key": "sk-abc123"})
        # => {"user": "alice", "api_key": "***REDACTED***"}
    """

    def __init__(self, fields: Optional[List[str]] = None) -> None:
        if fields is None:
            self.fields = set(_DEFAULT_SENSITIVE_FIELDS)
        else:
            self.fields = set(fields)

    def filter(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Return a new dict with sensitive values replaced by REDACTED.

        Performs a shallow copy and redacts top-level keys only.
        Nested dicts are recursively processed.
        """
        return self._redact(record)

    def _redact(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: (REDACTED if k in self.fields else self._redact(v))
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [self._redact(item) for item in obj]
        return obj
