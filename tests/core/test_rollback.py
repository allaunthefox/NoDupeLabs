"""Tests for rollback system."""

import shutil
import tempfile
from pathlib import Path

import pytest

from nodupe.tools.maintenance import (
    Operation,
    RollbackManager,
    Snapshot,
    SnapshotFile,
    SnapshotManager,
    TransactionLog,
)


class TestSnapshotManager:
    """Tests for SnapshotManager."""

    def test_create_snapshot(self, tmp_path):
        """Test creating a snapshot."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        mgr = SnapshotManager(str(tmp_path / ".nodupe"))
        snapshot = mgr.create_snapshot([str(test_file)])

        assert snapshot is not None
        assert snapshot.snapshot_id is not None
        assert len(snapshot.files) == 1
        assert snapshot.files[0].path == str(test_file)

    def test_list_snapshots(self, tmp_path):
        """Test listing snapshots."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        mgr = SnapshotManager(str(tmp_path / ".nodupe"))
        mgr.create_snapshot([str(test_file)])

        snapshots = mgr.list_snapshots()
        assert len(snapshots) == 1

    def test_delete_snapshot(self, tmp_path):
        """Test deleting a snapshot."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        mgr = SnapshotManager(str(tmp_path / ".nodupe"))
        snapshot = mgr.create_snapshot([str(test_file)])

        success = mgr.delete_snapshot(snapshot.snapshot_id)
        assert success is True

        snapshots = mgr.list_snapshots()
        assert len(snapshots) == 0


class TestTransactionLog:
    """Tests for TransactionLog."""

    def test_begin_commit_transaction(self, tmp_path):
        """Test transaction begin and commit."""
        log = TransactionLog(str(tmp_path / ".nodupe"))

        tx_id = log.begin_transaction()
        assert tx_id is not None

        log.log_operation(Operation("delete", "/test/path"))

        commit_id = log.commit_transaction()
        assert commit_id == tx_id

    def test_list_transactions(self, tmp_path):
        """Test listing transactions."""
        log = TransactionLog(str(tmp_path / ".nodupe"))

        tx_id = log.begin_transaction()
        log.commit_transaction()

        transactions = log.list_transactions()
        assert len(transactions) == 1
        assert transactions[0]["transaction_id"] == tx_id


class TestRollbackManager:
    """Tests for RollbackManager."""

    def test_execute_with_protection_success(self, tmp_path):
        """Test protected execution on success."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original")

        snapshot_mgr = SnapshotManager(str(tmp_path / ".nodupe"))
        tx_log = TransactionLog(str(tmp_path / ".nodupe"))
        manager = RollbackManager(snapshot_mgr, tx_log)

        def operation():
            test_file.write_text("modified")
            return "success"

        result = manager.execute_with_protection([str(test_file)], operation)
        assert result == "success"
        assert test_file.read_text() == "modified"

    def test_list_snapshots(self, tmp_path):
        """Test listing snapshots via manager."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        snapshot_mgr = SnapshotManager(str(tmp_path / ".nodupe"))
        tx_log = TransactionLog(str(tmp_path / ".nodupe"))
        manager = RollbackManager(snapshot_mgr, tx_log)

        manager.snapshots.create_snapshot([str(test_file)])

        snapshots = manager.list_snapshots()
        assert len(snapshots) == 1

    def test_list_transactions(self, tmp_path):
        """Test listing transactions via manager."""
        snapshot_mgr = SnapshotManager(str(tmp_path / ".nodupe"))
        tx_log = TransactionLog(str(tmp_path / ".nodupe"))
        manager = RollbackManager(snapshot_mgr, tx_log)

        tx_log.begin_transaction()
        tx_log.commit_transaction()

        transactions = manager.list_transactions()
        assert len(transactions) == 1
