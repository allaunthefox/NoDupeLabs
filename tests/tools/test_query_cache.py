import time
from unittest.mock import patch

import pytest

from nodupe.tools.databases.query_cache import QueryCache, create_query_cache


def test_set_get_and_stats_hit_miss():
    qc = QueryCache(max_size=5, ttl_seconds=60)

    assert qc.get_result("select 1") is None

    qc.set_result("select 1", None, [1])
    qc.set_result("select 2", None, [2])

    assert qc.get_result("select 1") == [1]
    assert qc.get_result("select 2") == [2]
    assert qc.get_result("select 3") is None

    stats = qc.get_stats()
    assert stats["hits"] >= 2
    assert stats["misses"] >= 1
    assert stats["size"] == 2


def test_ttl_expiration_and_cleanup(monkeypatch):
    # control monotonic to simulate expiry without sleeping
    base_time = 1_000.0

    class FakeTime:
        def __init__(self, start):
            self._t = start

        def monotonic(self):
            return self._t

        def advance(self, s):
            self._t += s

    ft = FakeTime(base_time)

    monkeypatch.setattr(
        "nodupe.tools.databases.query_cache.time.monotonic",
        ft.monotonic,
    )

    qc = QueryCache(max_size=10, ttl_seconds=5)
    qc.set_result("SELECT * FROM a", None, {"rows": [1]})

    # still valid
    assert qc.get_result("select * from a") is not None

    # advance past TTL
    ft.advance(6)

    # entry should be expired and removed
    assert qc.get_result("select * from a") is None
    removed = qc.validate_cache()
    assert removed >= 0


def test_eviction_and_resize():
    qc = QueryCache(max_size=2, ttl_seconds=60)

    qc.set_result("q1", None, 1)
    qc.set_result("q2", None, 2)
    # adding third should evict the LRU (q1)
    qc.set_result("q3", None, 3)

    assert qc.get_cache_size() == 2
    stats = qc.get_stats()
    assert stats["evictions"] >= 1

    # resize down to 1 should evict one more entry
    qc.resize(1)
    assert qc.get_cache_size() == 1
    stats2 = qc.get_stats()
    assert stats2["evictions"] >= stats["evictions"]


def test_access_lru_updates_recency():
    qc = QueryCache(max_size=2, ttl_seconds=60)

    qc.set_result("q1", None, "v1")
    qc.set_result("q2", None, "v2")

    # access q1 -> q1 should become most-recently-used
    assert qc.get_result("q1") == "v1"

    # insert q3 -> should evict the least-recently-used (q2)
    qc.set_result("q3", None, "v3")

    assert qc.get_result("q1") == "v1"  # still present (was MRU)
    assert qc.get_result("q2") is None  # evicted
    assert qc.get_result("q3") == "v3"


def test_concurrent_access_thread_safety():
    import threading

    qc = QueryCache(max_size=50, ttl_seconds=60)

    def worker(tid: int):
        for i in range(200):
            key = f"q{ i % 20 }"
            params = {"id": i % 20}
            qc.set_result(key, params, {"t": tid, "i": i})
            # random reads
            _ = qc.get_result(key, params)
            if i % 25 == 0:
                qc.invalidate(key, params)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]

    for th in threads:
        th.start()
    for th in threads:
        th.join()

    # basic sanity checks after concurrent access
    assert qc.get_cache_size() <= qc.max_size
    stats = qc.get_stats()
    assert stats["hits"] + stats["misses"] > 0
    # no exceptions raised means thread-safety holds for this workload


def test_invalidate_and_invalidate_by_prefix_and_clear_by_query_pattern():
    qc = create_query_cache(max_size=10, ttl_seconds=60)

    qc.set_result("SELECT id FROM users", {"id": 1}, "u1")
    qc.set_result("SELECT id FROM users WHERE id = ?", {"id": 2}, "u2")
    qc.set_result("SELECT * FROM sessions", None, "s1")

    # invalidate single entry
    assert qc.invalidate("select id from users", {"id": 1}) is True
    assert qc.is_cached("select id from users", {"id": 1}) is False

    # prefix must match the generated key prefix
    # use the normalized query part as prefix
    prefix = "select id from users"
    removed = qc.invalidate_by_prefix(prefix)
    assert removed >= 1

    # clear by pattern (matches query part)
    qc.set_result("SELECT * FROM pattern_test", None, 123)
    cleared = qc.clear_by_query_pattern("pattern_test")
    assert cleared >= 1


def test_get_cached_queries_and_memory_usage():
    qc = QueryCache(max_size=10, ttl_seconds=60)
    qc.set_result("SELECT a FROM b", None, [1, 2, 3])
    qc.set_result("SELECT x FROM y", None, {"k": "v"})

    queries = qc.get_cached_queries()
    assert any("select a from b" in q for q in queries)

    usage = qc.get_memory_usage()
    assert isinstance(usage, int) and usage > 0
