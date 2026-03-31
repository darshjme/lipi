# Contributing to agent-logger

Thank you for your interest in contributing! 🎉

## Getting Started

```bash
git clone https://github.com/darshjme-codes/agent-logger.git
cd agent-logger
pip install -e ".[dev]"
```

## Running Tests

```bash
PYTHONPATH=src python -m pytest tests/ -v

> **Note:** `PYTHONPATH=src` is required for libraries using a `src/` layout.
```

## Code Style

- Follow PEP 8.
- Add type hints to all public APIs.
- Keep zero external runtime dependencies — use the Python stdlib only.

## Submitting Changes

1. Fork the repo and create a feature branch (`git checkout -b feature/my-feature`).
2. Write tests for your changes.
3. Ensure all tests pass (`PYTHONPATH=src python -m pytest tests/ -v`).

> **Note:** `PYTHONPATH=src` is required for libraries using a `src/` layout.
4. Open a pull request with a clear description of the change and why.

## Reporting Issues

Open a GitHub Issue with:
- Python version (`python --version`)
- OS and version
- Minimal reproducible example
- Expected vs actual behaviour

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
All contributors are expected to uphold it.
