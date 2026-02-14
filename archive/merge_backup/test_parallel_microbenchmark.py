"""
Micro-benchmark to measure process-pool small-item workload overhead for tuning.

This test intentionally prints timing measurements (no performance assertions) so it can
be run standalone to gather stable metrics for the batching/chunksize heuristics.
"""
from time import perf_counter
import statistics
import os

from nodupe.core.parallel import Parallel


def _work(x: int) -> int:
    # Small, deterministic CPU work to make per-item cost non-trivial while remaining quick.
    s = x
    for i in range(10):
        s += (i * (x + 1)) % 7
    return s


def test_microbenchmark_process_pool_small_items():
    items = list(range(200))  # small-item workload to stress IPC/pickling overhead
    workers = min(4, max(1, os.cpu_count() or 1))
    runs = 5
    times = []

    for _ in range(runs):
        t0 = perf_counter()
        # Exercise the process-pool code path with prefer_batches=True so heuristics are used.
        list(Parallel.map_parallel_unordered(_work, items, workers=workers, use_processes=True, prefer_batches=True))
        times.append(perf_counter() - t0)

    median = statistics.median(times)
    print(
        f"microbenchmark: items={len(items)}, workers={workers}, runs={runs}, "
        f"times={[round(t, 4) for t in times]}, median={median:.4f}s"
    )

    # Test should always pass; this exists to collect stable timing data, not enforce a threshold.
    assert True
