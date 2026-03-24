"""Tests for CorrelationContext."""

import threading
import uuid

import pytest

from agent_logger import CorrelationContext


class TestCorrelationContext:
    def setup_method(self):
        CorrelationContext.clear()

    def teardown_method(self):
        CorrelationContext.clear()

    # --- basic set / get ---

    def test_get_returns_none_when_not_set(self):
        assert CorrelationContext.get() is None

    def test_set_and_get(self):
        CorrelationContext.set("req-001")
        assert CorrelationContext.get() == "req-001"

    def test_clear_removes_id(self):
        CorrelationContext.set("req-001")
        CorrelationContext.clear()
        assert CorrelationContext.get() is None

    # --- generate ---

    def test_generate_returns_valid_uuid4(self):
        cid = CorrelationContext.generate()
        parsed = uuid.UUID(cid, version=4)
        assert str(parsed) == cid

    def test_generate_does_not_set(self):
        CorrelationContext.generate()
        assert CorrelationContext.get() is None

    # --- scope context manager ---

    def test_scope_sets_id_inside(self):
        with CorrelationContext.scope("req-scope-1"):
            assert CorrelationContext.get() == "req-scope-1"

    def test_scope_clears_after_exit(self):
        with CorrelationContext.scope("req-scope-2"):
            pass
        assert CorrelationContext.get() is None

    def test_scope_restores_previous(self):
        CorrelationContext.set("outer")
        with CorrelationContext.scope("inner"):
            assert CorrelationContext.get() == "inner"
        assert CorrelationContext.get() == "outer"

    def test_scope_clears_even_on_exception(self):
        try:
            with CorrelationContext.scope("err-scope"):
                raise ValueError("boom")
        except ValueError:
            pass
        assert CorrelationContext.get() is None

    # --- thread isolation ---

    def test_thread_local_isolation(self):
        results = {}

        def worker(name, cid):
            CorrelationContext.set(cid)
            import time; time.sleep(0.01)
            results[name] = CorrelationContext.get()

        threads = [
            threading.Thread(target=worker, args=(f"t{i}", f"cid-{i}"))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for i in range(5):
            assert results[f"t{i}"] == f"cid-{i}"
