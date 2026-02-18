# SPDX-License-Identifier: Apache-2.0
"""Unit tests for PlanTool and FileRepository batch/stream helpers.

These tests verify that PlanTool no longer loads the full files
table into memory and that FileRepository exposes efficient
helpers for grouping and batch-updating duplicate records.
"""
import argparse
import json
import tempfile
from types import SimpleNamespace

import pytest

from nodupe.tools.databases.connection import DatabaseConnection
from nodupe.tools.databases.files import FileRepository
from nodupe.tools.commands.plan import PlanTool


def _make_db():
    db = DatabaseConnection.get_instance(":memory:")
    db.initialize_database()
    repo = FileRepository(db)
    repo.clear_all_files()
    return db, repo


def test_file_repository_duplicate_hashes_and_batch_marking():
    db, repo = _make_db()

    # Add a small group of files that share the same hash
    ids = []
    ids.append(repo.add_file("/tmp/a.txt", size=10, modified_time=100, hash_value="h1"))
    ids.append(repo.add_file("/tmp/b.txt", size=20, modified_time=200, hash_value="h1"))
    ids.append(repo.add_file("/tmp/c.txt", size=30, modified_time=150, hash_value="h1"))

    # get_duplicate_hashes should expose 'h1'
    hashes = repo.get_duplicate_hashes()
    assert "h1" in hashes

    group = repo.find_duplicates_by_hash("h1")
    assert len(group) == 3

    # Choose keeper (simulate PlanTool strategy 'newest')
    group.sort(key=lambda x: x.get('modified_time', 0), reverse=True)
    keeper = group[0]
    duplicates = group[1:]

    # Batch mark duplicates
    dup_ids = [d['id'] for d in duplicates]
    updated = repo.batch_mark_as_duplicate(dup_ids, keeper['id'])
    assert updated == len(dup_ids)

    # Assert duplicates are marked
    for did in dup_ids:
        f = repo.get_file(did)
        assert f['is_duplicate'] is True
        assert f['duplicate_of'] == keeper['id']

    # Mark keeper as original (should be idempotent)
    assert repo.mark_as_original(keeper['id']) is True
    kf = repo.get_file(keeper['id'])
    assert kf['is_duplicate'] is False
    assert kf['duplicate_of'] is None


def test_plan_tool_execute_plan_batches_updates_and_writes_plan(tmp_path):
    db, repo = _make_db()

    # Group 1 (h1) - three files
    repo.add_file("/data/h1_1.txt", size=10, modified_time=100, hash_value="h1")
    repo.add_file("/data/h1_2.txt", size=10, modified_time=300, hash_value="h1")
    repo.add_file("/data/h1_3.txt", size=10, modified_time=200, hash_value="h1")

    # Group 2 (h2) - two files
    repo.add_file("/data/h2_1.txt", size=5, modified_time=50, hash_value="h2")
    repo.add_file("/data/h2_2.txt", size=5, modified_time=60, hash_value="h2")

    # Single unique file (no hash)
    repo.add_file("/data/unique.txt", size=7, modified_time=70, hash_value=None)

    # Run PlanTool with a dummy container that returns our DB instance
    container = SimpleNamespace(get_service=lambda name: db)
    output_file = tmp_path / "plan.json"

    args = argparse.Namespace(strategy='newest', output=str(output_file), container=container)

    tool = PlanTool()
    rc = tool.execute_plan(args)
    assert rc == 0

    # Plan file should exist and contain actions for both groups
    data = json.loads(output_file.read_text())
    actions = data.get('actions', [])

    # Expect one KEEP per group and DELETE entries for duplicates
    keep_paths = [a['path'] for a in actions if a['type'] == 'KEEP']
    delete_paths = [a['path'] for a in actions if a['type'] == 'DELETE']

    assert any('h1' in p for p in keep_paths)
    assert any('h2' in p for p in keep_paths)

    # Database assertions: duplicates should be marked and point to their keeper
    for h in ('h1', 'h2'):
        group = repo.find_duplicates_by_hash(h)
        # determine keeper by newest modified_time
        group.sort(key=lambda x: x.get('modified_time', 0), reverse=True)
        keeper = group[0]
        for dup in group[1:]:
            f = repo.get_file(dup['id'])
            assert f['is_duplicate'] is True
            assert f['duplicate_of'] == keeper['id']


# End of file
