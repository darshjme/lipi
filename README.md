# agent-logger

**Structured JSON logging for LLM agents** — correlation IDs, context binding, probabilistic sampling, and sensitive field redaction. Zero external dependencies (pure Python stdlib).

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Quick Install

```bash
pip install agent-logger
```

---

## The Problem

Standard Python logging is unstructured:

```python
logging.info("Called LLM")  # 🤔 what model? how long? which request?
```

In production multi-agent systems you need:
- JSON records ingestible by Datadog / Loki / CloudWatch
- **Correlation IDs** to trace a request across agent boundaries
- Automatic context fields (model, tokens, latency)
- **Log sampling** to avoid drowning in high-volume debug noise
- **Redaction** of API keys and secrets before they hit disk

---

## 3-Agent Request Tracing Example

```python
from agent_logger import AgentLogger, CorrelationContext

# --- Agent 1: Router ---
router_log = AgentLogger("router")

def handle_request(user_query: str):
    # Generate and broadcast the correlation ID for this request
    cid = CorrelationContext.generate()
    with CorrelationContext.scope(cid):
        router_log.info("request received", query=user_query[:50])
        # hand off to Agent 2
        result = call_retriever(user_query)
        # hand off to Agent 3
        answer = call_llm(result)
        router_log.info("request complete", answer_len=len(answer))
        return answer


# --- Agent 2: Retriever ---
retriever_log = AgentLogger("retriever")

def call_retriever(query: str):
    # correlation_id is already in thread-local — auto-injected
    retriever_log.info("fetching docs", query=query[:50], k=5)
    docs = ["doc1", "doc2"]  # simulate retrieval
    retriever_log.info("docs fetched", count=len(docs))
    return docs


# --- Agent 3: LLM Caller ---
llm_log = AgentLogger("llm-caller")

def call_llm(docs):
    llm_log.info("calling llm", model="gpt-4o", doc_count=len(docs))
    answer = "42"  # simulate LLM response
    llm_log.info("llm responded", tokens=128, latency_ms=210)
    return answer


handle_request("What is the meaning of life?")
```

**Output** (all three agents share the same `correlation_id`):

```json
{"timestamp":"2026-03-24T08:00:00Z","level":"INFO","name":"router","message":"request received","correlation_id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","query":"What is the meaning of life?"}
{"timestamp":"2026-03-24T08:00:00Z","level":"INFO","name":"retriever","message":"fetching docs","correlation_id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","query":"What is the meaning of life?","k":5}
{"timestamp":"2026-03-24T08:00:00Z","level":"INFO","name":"retriever","message":"docs fetched","correlation_id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","count":2}
{"timestamp":"2026-03-24T08:00:00Z","level":"INFO","name":"llm-caller","message":"calling llm","correlation_id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","model":"gpt-4o","doc_count":2}
{"timestamp":"2026-03-24T08:00:00Z","level":"INFO","name":"llm-caller","message":"llm responded","correlation_id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","tokens":128,"latency_ms":210}
{"timestamp":"2026-03-24T08:00:00Z","level":"INFO","name":"router","message":"request complete","correlation_id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","answer_len":2}
```

---

## Components

### `AgentLogger`

```python
from agent_logger import AgentLogger

logger = AgentLogger(
    name="my-agent",
    level="INFO",          # DEBUG | INFO | WARNING | ERROR | CRITICAL
    output="stdout",       # "stdout" | "stderr" | "/path/to/file.log"
    json_format=True,      # False = plain text
)

logger.info("model called", model="gpt-4o", tokens=512, latency_ms=340)
# {"timestamp":"...","level":"INFO","name":"my-agent","message":"model called",
#  "correlation_id":null,"model":"gpt-4o","tokens":512,"latency_ms":340}
```

### `ContextLogger` — bound fields

```python
ctx = logger.with_context(agent="router", env="prod")
ctx.info("started")          # agent + env injected automatically
ctx2 = ctx.bind(request_id="r-001")  # immutable — returns new logger
ctx2.info("processing")
```

### `CorrelationContext` — thread-local ID management

```python
from agent_logger import CorrelationContext

cid = CorrelationContext.generate()    # generates UUID4
CorrelationContext.set(cid)            # set for current thread
print(CorrelationContext.get())        # read from anywhere in same thread

# Context manager (auto-clears):
with CorrelationContext.scope(cid):
    ...  # all logs here include this cid
```

### `LogSampler` — probabilistic sampling

```python
from agent_logger import LogSampler

sampler = LogSampler(rate=0.1)          # log only 10% of records
sampled_logger = sampler.wrap(logger)   # SampledLogger
sampled_logger.debug("high volume")     # ~10% chance of appearing
```

### `RedactingFilter` — auto-redact secrets

```python
from agent_logger import AgentLogger, RedactingFilter

rf = RedactingFilter()   # default: api_key, token, password, secret, authorization
# or: RedactingFilter(fields=["my_secret"])

logger = AgentLogger("secure-agent", redacting_filter=rf)
logger.info("auth call", api_key="sk-abc123", model="gpt-4")
# {"api_key":"***REDACTED***","model":"gpt-4",...}
```

---

## API Reference

| Class | Key Methods |
|-------|-------------|
| `AgentLogger` | `info/debug/warning/error/critical(msg, **kw)`, `with_context(**kw)`, `set_correlation_id(id)`, `get_correlation_id()` |
| `ContextLogger` | Same log methods + `bind(**kw) -> ContextLogger` |
| `CorrelationContext` | `set(id)`, `get()`, `generate()`, `clear()`, `scope(id)` (context manager) |
| `LogSampler` | `should_log() -> bool`, `wrap(logger) -> SampledLogger` |
| `RedactingFilter` | `filter(record: dict) -> dict` |

---

## Running Tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
# 40 tests, all pass
```

---

## License

MIT © Darshankumar Joshi
