import os

from nodupe.scan.hasher import (
    _choose_executor_type as _choose_executor_type_for_test
)


def test_executor_choice_small_cpu(monkeypatch):
    # Simulate a 6-core / 12-thread system (logical CPUs = 12)
    monkeypatch.setattr(os, "cpu_count", lambda: 12)
    # For 12 logical CPUs heuristic prefers threads for modest worker counts
    assert _choose_executor_type_for_test("auto", 4) == "thread"
    # On a small/dev machine we prefer threads (<=16 logical CPUs)
    assert _choose_executor_type_for_test("auto", 6) == "thread"


def test_executor_choice_medium_cpu(monkeypatch):
    # Simulate a 12-core / 24-thread machine (logical CPUs = 24)
    monkeypatch.setattr(os, "cpu_count", lambda: 24)
    # For modest worker counts prefer threads
    assert _choose_executor_type_for_test("auto", 4) == "thread"
    # If workers are large relative to CPUs (>= cpu//2), auto should pick
    # processes
    assert _choose_executor_type_for_test("auto", 12) == "process"


def test_executor_choice_large_cpu(monkeypatch):
    # Simulate a 32-core / 64-thread system (logical CPUs = 64)
    monkeypatch.setattr(os, "cpu_count", lambda: 64)
    assert _choose_executor_type_for_test("auto", 40) == "process"


def test_executor_choice_gil_free_env(monkeypatch):
    # Even on a large machine, PYTHON_ENABLE_NOGIL should force threads
    monkeypatch.setattr(os, "cpu_count", lambda: 64)
    monkeypatch.setenv("PYTHON_ENABLE_NOGIL", "1")
    try:
        assert _choose_executor_type_for_test("auto", 8) == "thread"
    finally:
        monkeypatch.delenv("PYTHON_ENABLE_NOGIL", raising=False)
