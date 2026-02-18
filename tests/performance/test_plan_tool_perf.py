# SPDX-License-Identifier: Apache-2.0
"""Performance and integration tests for PlanTool (DB-streaming path).

These tests generate synthetic databases with many duplicate-hash groups and
measure PlanTool's runtime and peak memory while executing `execute_plan()`.

Thresholds are configurable via pytest markers on the test function, for example:

@pytest.mark.plantool_thresholds(time=4.0, memory=150)
@pytest.mark.performance
def test_...(...)

If `psutil` is not available the memory assertions are skipped (fallback).
"""
from types import SimpleNamespace
import argparse
import time
import json
import os
import tempfile

import pytest

from nodupe.tools.databases.connection import DatabaseConnection
from nodupe.tools.databases.files import FileRepository
from nodupe.tools.commands.plan import PlanTool

from tests.utils.database import generate_files_with_duplicates
from tests.utils.performance import measure_memory_usage, benchmark_function_performance, PSUTIL_AVAILABLE


def _make_db():
    db = DatabaseConnection.get_instance(":memory:")
    db.initialize_database()
    repo = FileRepository(db)
    repo.clear_all_files()
    return db, repo


@pytest.mark.performance
@pytest.mark.parametrize(
    "total_files,avg_group_size,expected_time_sec,expected_mem_mb",
    [
        (10_000, 5, 2.0, 75),   # medium (CI-friendly)
    ],
)
def test_plan_tool_runtime_and_memory_medium(tmp_path, request, total_files, avg_group_size, expected_time_sec, expected_mem_mb):
    """Create ~10k-file dataset, run PlanTool, assert runtime and memory stay within thresholds."""
    db, repo = _make_db()

    # Generate dataset (many duplicate groups)
    stats = generate_files_with_duplicates(repo, total_files=total_files, avg_group_size=avg_group_size)
    assert stats["total_files"] == total_files

    # Prepare PlanTool args using a container that returns our DB instance
    container = SimpleNamespace(get_service=lambda name: db)
    output_file = tmp_path / "plan.json"
    args = argparse.Namespace(strategy='newest', output=str(output_file), container=container)

    tool = PlanTool()

    # Time the execution
    t0 = time.time()
    rc = tool.execute_plan(args)
    elapsed = time.time() - t0

    assert rc == 0
    assert elapsed <= expected_time_sec, f"PlanTool took too long: {elapsed:.2f}s > {expected_time_sec}s"

    # Measure memory increase when re-running (memory check uses helper which may fallback)
    mem = measure_memory_usage(lambda: tool.execute_plan(args), iterations=1)

    if PSUTIL_AVAILABLE:
        mem_mb = mem['total_memory_used'] / 1024 / 1024
        assert mem_mb <= expected_mem_mb, f"Memory increase too large: {mem_mb:.2f}MB > {expected_mem_mb}MB"
    else:
        pytest.skip("psutil not available; skipping memory assertion")


@pytest.mark.performance
@pytest.mark.plantool_thresholds(time=8.0, memory=250)
def test_plan_tool_benchmark_large(tmp_path, request):
    """Larger benchmark (50k rows) — marked performance. Thresholds can be overridden
    by applying @pytest.mark.plantool_thresholds(time=..., memory=...).
    """
    marker = request.node.get_closest_marker('plantool_thresholds')
    if marker:
        max_time = marker.kwargs.get('time', marker.args[0] if marker.args else 8.0)
        max_mem = marker.kwargs.get('memory', marker.args[1] if len(marker.args) > 1 else 250)
    else:
        max_time, max_mem = 8.0, 250

    total_files = 50_000
    avg_group_size = 5

    db, repo = _make_db()

    # Insert dataset in reasonable time
    stats = generate_files_with_duplicates(repo, total_files=total_files, avg_group_size=avg_group_size)
    assert stats['total_files'] == total_files

    container = SimpleNamespace(get_service=lambda name: db)
    output_file = tmp_path / "plan_large.json"
    args = argparse.Namespace(strategy='newest', output=str(output_file), container=container)
    tool = PlanTool()

    # Measure execution time (single run)
    bench = benchmark_function_performance(lambda: tool.execute_plan(args), iterations=1, warmup_iterations=0)
    elapsed = bench['average_time']

    assert elapsed <= max_time, f"PlanTool too slow on {total_files} rows: {elapsed:.2f}s > {max_time}s"

    # Memory assertion (skip if psutil missing)
    mem = measure_memory_usage(lambda: tool.execute_plan(args), iterations=1)
    if PSUTIL_AVAILABLE:
        mem_mb = mem['total_memory_used'] / 1024 / 1024
        assert mem_mb <= max_mem, f"PlanTool memory increase too large: {mem_mb:.2f}MB > {max_mem}MB"
    else:
        pytest.skip("psutil not available; skipping memory assertion")

    # Basic correctness: ensure plan file was written and contains expected keys
    assert os.path.exists(str(output_file))
    data = json.loads(output_file.read_text())
    assert 'metadata' in data and 'actions' in data
    assert data['metadata']['stats']['total_groups'] > 0


# End of file
