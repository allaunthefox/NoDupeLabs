# SPDX-License-Identifier: Apache-2.0
"""Lightweight performance test for PlanTool to validate DB-streaming refactor.

This test is intentionally small in CI but can be scaled locally by setting
PERF_ROWS environment variable.
"""
import os
import time
import argparse

import pytest

from nodupe.tools.databases.connection import DatabaseConnection
from nodupe.tools.databases.files import FileRepository
from nodupe.tools.commands.plan import PlanTool


@pytest.mark.slow
def test_plan_tool_handles_large_dataset(tmp_path):
    rows = int(os.getenv("PERF_ROWS", "2000"))
    db = DatabaseConnection.get_instance(":memory:")
    db.initialize_database()
    repo = FileRepository(db)
    repo.clear_all_files()

    # Create duplicate groups (100 groups * rows_per_group)
    groups = 50
    per_group = max(1, rows // groups)
    for g in range(groups):
        h = f"hash_{g}"
        for i in range(per_group):
            repo.add_file(f"/tmp/{g}_{i}.txt", size=10, modified_time=i, hash_value=h)

    # Run PlanTool and ensure it completes quickly
    tool = PlanTool()
    output = tmp_path / "plan.json"
    args = argparse.Namespace(strategy='newest', output=str(output), container=type("C", (), {"get_service": lambda s: db}))

    start = time.monotonic()
    rc = tool.execute_plan(args)
    elapsed = time.monotonic() - start

    assert rc == 0
    # expect the operation to be reasonably fast for this dataset
    assert elapsed < 5.0
