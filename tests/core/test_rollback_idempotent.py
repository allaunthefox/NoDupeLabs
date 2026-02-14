"""Tests for idempotent backup in rollback system."""
import tempfile
from pathlib import Path

from nodupe.core.rollback import SnapshotManager


class TestIdempotentBackup:
    """Tests for idempotent backup functionality."""

    def test_idempotent_backup_same_content(self, tmp_path):
        """Test that backing up same content twice only copies once."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        mgr = SnapshotManager(str(tmp_path / ".nodupe"))

        # First snapshot
        snapshot1 = mgr.create_snapshot([str(test_file)])
        backup_path1 = snapshot1.files[0].backup_path

        # Second snapshot with same content - should be idempotent
        snapshot2 = mgr.create_snapshot([str(test_file)])
        backup_path2 = snapshot2.files[0].backup_path

        # Same backup path means no duplicate copy
        assert backup_path1 == backup_path2

        # Verify content exists
        assert Path(backup_path1).exists()

    def test_idempotent_backup_different_content(self, tmp_path):
        """Test that different content gets different backup."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        mgr = SnapshotManager(str(tmp_path / ".nodupe"))

        # First snapshot
        snapshot1 = mgr.create_snapshot([str(test_file)])
        backup_path1 = snapshot1.files[0].backup_path

        # Modify file
        test_file.write_text("different content")

        # Second snapshot with different content
        snapshot2 = mgr.create_snapshot([str(test_file)])
        backup_path2 = snapshot2.files[0].backup_path

        # Different backup path
        assert backup_path1 != backup_path2

        # Both should exist
        assert Path(backup_path1).exists()
        assert Path(backup_path2).exists()

    def test_restore_from_backup(self, tmp_path):
        """Test that restore works with the backup."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        mgr = SnapshotManager(str(tmp_path / ".nodupe"))

        # Create snapshot with backup
        snapshot = mgr.create_snapshot([str(test_file)])

        # Modify file
        test_file.write_text("modified content")
        assert test_file.read_text() == "modified content"

        # Restore from snapshot
        success = mgr.restore_snapshot(snapshot.snapshot_id)
        assert success is True

        # Content should be restored
        assert test_file.read_text() == "original content"
