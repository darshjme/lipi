# Changelog

All notable changes to **agent-logger** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2026-03-24

### Added
- `AgentLogger` — structured JSON logger with correlation ID support.
- `ContextLogger` — immutable logger with bound context fields via `bind()`.
- `LogSampler` — probabilistic sampling (`rate` 0.0–1.0) with `SampledLogger` wrapper.
- `RedactingFilter` — auto-redact sensitive fields (api_key, token, password, secret, authorization).
- `CorrelationContext` — thread-local correlation ID manager with `scope()` context manager.
- Zero external dependencies (pure Python stdlib: `logging`, `json`, `threading`, `uuid`).
- Full pytest test suite (22+ tests).
- README with 3-agent request tracing example.
