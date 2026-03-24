# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅         |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Please report security issues privately by emailing **darshjme@gmail.com** with:

- A description of the vulnerability.
- Steps to reproduce.
- Potential impact.
- (Optional) Suggested fix or patch.

We will respond within **72 hours** and aim to release a patch within **7 days** for critical issues.

## Security Notes

- `RedactingFilter` redacts sensitive fields from log output. However, it operates on the **log record** only — it does NOT sanitize data before it reaches your application logic.
- Thread-local correlation IDs are automatically cleared when `CorrelationContext.scope()` exits. In async frameworks (asyncio, trio), use framework-native context variables (`contextvars.ContextVar`) instead of the thread-local `CorrelationContext`.
- When writing logs to files (`output="path/to/file.log"`), ensure appropriate filesystem permissions to protect log data.
