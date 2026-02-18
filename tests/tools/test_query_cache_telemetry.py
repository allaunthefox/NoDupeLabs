# SPDX-License-Identifier: Apache-2.0
"""Tests for QueryCache metrics export and telemetry registry."""
from nodupe.tools.databases.query_cache import QueryCache
from nodupe.tools import telemetry


def test_query_cache_export_metrics_and_registry():
    qc = QueryCache(max_size=10, ttl_seconds=1)
    qc.set_result("q1", result={"v": 1})
    assert qc.get_result("q1") == {"v": 1}
    # force TTL expiry
    import time
    time.sleep(1.05)
    assert qc.get_result("q1") is None

    # exercise counters
    qc.set_result("q2", result=2)
    _ = qc.get_result("q2")
    metrics = qc.export_metrics_prometheus(prefix="nodupe_query_cache_", labels={"cache": "t1"})
    assert "nodupe_query_cache_hits_total" in metrics
    assert "nodupe_query_cache_ttl_expiries_total" in metrics

    # register in telemetry and collect
    telemetry.register_query_cache("main", qc)
    collected = telemetry.collect_metrics()
    assert "cache=\"main\"" in collected
    telemetry.unregister_query_cache("main")
