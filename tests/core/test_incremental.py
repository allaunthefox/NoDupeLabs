"""Test incremental module functionality."""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from nodupe.tools.scanner_engine.incremental import Incremental


class TestIncremental:
    """Test Incremental class functionality."""

    temp_dir: str
    scan_path: str

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.scan_path = self.temp_dir

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_checkpoint_file_constant(self):
        """Test CHECKPOINT_FILE constant."""
        assert Incremental.CHECKPOINT_FILE == ".nodupe_checkpoint.json"

    def test_save_checkpoint(self):
        """Test saving checkpoint."""
        processed_files = {
            "file1.txt": {"hash": "abc123", "size": 100},
            "file2.txt": {"hash": "def456", "size": 200}
        }
        metadata = {"version": "1.0", "scan_type": "full"}

        Incremental.save_checkpoint(self.scan_path, processed_files, metadata)

        checkpoint_file = Path(self.scan_path) / Incremental.CHECKPOINT_FILE
        assert checkpoint_file.exists()

        with open(checkpoint_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["scan_path"] == self.scan_path
        assert data["processed_files"] == processed_files
        assert data["metadata"] == metadata
        assert "timestamp" in data

        # Verify timestamp format
        datetime.fromisoformat(data["timestamp"])

    def test_save_checkpoint_no_metadata(self):
        """Test saving checkpoint without metadata."""
        processed_files = {"file1.txt": {"hash": "abc123"}}

        Incremental.save_checkpoint(self.scan_path, processed_files)

        checkpoint_file = Path(self.scan_path) / Incremental.CHECKPOINT_FILE
        assert checkpoint_file.exists()

        with open(checkpoint_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["scan_path"] == self.scan_path
        assert data["processed_files"] == processed_files
        assert data["metadata"] == {}

    def test_load_checkpoint_exists(self):
        """Test loading existing checkpoint."""
        # Create a checkpoint file
        checkpoint_data = {
            "scan_path": self.scan_path,
            "processed_files": {"file1.txt": {"hash": "abc123"}},
            "timestamp": "2023-01-01T00:00:00",
            "metadata": {"version": "1.0"}
        }

        checkpoint_file = Path(self.scan_path) / Incremental.CHECKPOINT_FILE
        with open(checkpoint_file, 'w', encoding="utf-8") as f:
            json.dump(checkpoint_data, f)

        # Load the checkpoint
        loaded = Incremental.load_checkpoint(self.scan_path)
        assert loaded == checkpoint_data

    def test_load_checkpoint_not_exists(self):
        """Test loading non-existent checkpoint."""
        result = Incremental.load_checkpoint(self.scan_path)
        assert result is None

    def test_get_remaining_files_no_checkpoint(self):
        """Test getting remaining files when no checkpoint exists."""
        all_files = ["file1.txt", "file2.txt", "file3.txt"]
        remaining = Incremental.get_remaining_files(self.scan_path, all_files)
        assert remaining == all_files

    def test_get_remaining_files_with_checkpoint(self):
        """Test getting remaining files with existing checkpoint."""
        # Create checkpoint with some processed files
        processed_files = {
            "file1.txt": {"hash": "abc123"},
            "file3.txt": {"hash": "def456"}
        }

        checkpoint_data = {
            "scan_path": self.scan_path,
            "processed_files": processed_files,
            "timestamp": "2023-01-01T00:00:00",
            "metadata": {}
        }

        checkpoint_file = Path(self.scan_path) / Incremental.CHECKPOINT_FILE
        with open(checkpoint_file, 'w', encoding="utf-8") as f:
            json.dump(checkpoint_data, f)

        # Test with all files
        all_files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]
        remaining = Incremental.get_remaining_files(self.scan_path, all_files)

        expected_remaining = ["file2.txt", "file4.txt"]
        assert remaining == expected_remaining

    def test_get_remaining_files_empty_checkpoint(self):
        """Test getting remaining files with empty checkpoint."""
        checkpoint_data = {
            "scan_path": self.scan_path,
            "processed_files": {},
            "timestamp": "2023-01-01T00:00:00",
            "metadata": {}
        }

        checkpoint_file = Path(self.scan_path) / Incremental.CHECKPOINT_FILE
        with open(checkpoint_file, 'w', encoding="utf-8") as f:
            json.dump(checkpoint_data, f)

        all_files = ["file1.txt", "file2.txt"]
        remaining = Incremental.get_remaining_files(self.scan_path, all_files)
        assert remaining == all_files

    def test_update_checkpoint_existing(self):
        """Test updating existing checkpoint."""
        # Create initial checkpoint
        initial_files = {"file1.txt": {"hash": "abc123"}}
        Incremental.save_checkpoint(self.scan_path, initial_files)

        # Update with new files
        new_files = {
            "file2.txt": {
                "hash": "def456"}, "file3.txt": {
                "hash": "ghi789"}}
        Incremental.update_checkpoint(self.scan_path, new_files)

        # Load and verify
        updated = Incremental.load_checkpoint(self.scan_path)
        assert "file1.txt" in updated["processed_files"]
        assert "file2.txt" in updated["processed_files"]
        assert "file3.txt" in updated["processed_files"]
        assert updated["processed_files"]["file1.txt"] == {"hash": "abc123"}
        assert updated["processed_files"]["file2.txt"] == {"hash": "def456"}

        # Verify timestamp was updated
        datetime.fromisoformat(updated["timestamp"])
        assert "timestamp" in updated

    def test_update_checkpoint_new(self):
        """Test updating non-existent checkpoint (creates new one)."""
        new_files = {"file1.txt": {"hash": "abc123"}}
        Incremental.update_checkpoint(self.scan_path, new_files)

        # Verify new checkpoint was created
        checkpoint = Incremental.load_checkpoint(self.scan_path)
        assert checkpoint is not None
        assert checkpoint["processed_files"] == new_files
        assert checkpoint["scan_path"] == self.scan_path
        assert "timestamp" in checkpoint

    def test_cleanup_checkpoint_exists(self):
        """Test cleaning up existing checkpoint."""
        # Create checkpoint
        Incremental.save_checkpoint(
            self.scan_path, {
                "file1.txt": {
                    "hash": "abc123"}})

        # Clean up
        result = Incremental.cleanup_checkpoint(self.scan_path)
        assert result is True

        # Verify file was removed
        checkpoint_file = Path(self.scan_path) / Incremental.CHECKPOINT_FILE
        assert not checkpoint_file.exists()

    def test_cleanup_checkpoint_not_exists(self):
        """Test cleaning up non-existent checkpoint."""
        result = Incremental.cleanup_checkpoint(self.scan_path)
        assert result is False


class TestIncrementalEdgeCases:
    """Test incremental edge cases."""

    temp_dir: str
    scan_path: str

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.scan_path = self.temp_dir

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_checkpoint_empty_files(self):
        """Test saving checkpoint with empty processed files."""
        Incremental.save_checkpoint(self.scan_path, {})

        checkpoint_file = Path(self.scan_path) / Incremental.CHECKPOINT_FILE
        assert checkpoint_file.exists()

        with open(checkpoint_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["processed_files"] == {}

    def test_get_remaining_files_empty_list(self):
        """Test getting remaining files with empty file list."""
        remaining = Incremental.get_remaining_files(self.scan_path, [])
        assert remaining == []

    def test_update_checkpoint_empty_files(self):
        """Test updating checkpoint with empty files."""
        # Create initial checkpoint
        Incremental.save_checkpoint(
            self.scan_path, {
                "file1.txt": {
                    "hash": "abc123"}})

        # Update with empty files
        Incremental.update_checkpoint(self.scan_path, {})

        # Verify original files are still there
        updated = Incremental.load_checkpoint(self.scan_path)
        assert "file1.txt" in updated["processed_files"]

    def test_checkpoint_file_permissions(self):
        """Test checkpoint file creation with proper permissions."""
        Incremental.save_checkpoint(
            self.scan_path, {
                "file1.txt": {
                    "hash": "abc123"}})

        checkpoint_file = Path(self.scan_path) / Incremental.CHECKPOINT_FILE
        assert checkpoint_file.exists()

        # Verify file is readable
        with open(checkpoint_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["processed_files"]["file1.txt"]["hash"] == "abc123"


class TestIncrementalIntegration:
    """Test incremental integration scenarios."""

    temp_dir: str
    scan_path: str

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.scan_path = self.temp_dir

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_incremental_workflow(self):
        """Test complete incremental scanning workflow."""
        # Initial scan - no checkpoint exists
        all_files = ["file1.txt", "file2.txt", "file3.txt"]
        remaining = Incremental.get_remaining_files(self.scan_path, all_files)
        assert remaining == all_files

        # Process some files and save checkpoint
        processed_files = {
            "file1.txt": {"hash": "abc123", "size": 100},
            "file2.txt": {"hash": "def456", "size": 200}
        }
        Incremental.save_checkpoint(self.scan_path, processed_files)

        # Second scan - should only get remaining files
        remaining = Incremental.get_remaining_files(self.scan_path, all_files)
        assert remaining == ["file3.txt"]

        # Process remaining file and update checkpoint
        new_processed_files = {"file3.txt": {"hash": "ghi789", "size": 300}}
        Incremental.update_checkpoint(self.scan_path, new_processed_files)

        # Third scan - no files should remain
        remaining = Incremental.get_remaining_files(self.scan_path, all_files)
        assert remaining == []

        # Clean up
        result = Incremental.cleanup_checkpoint(self.scan_path)
        assert result is True

    def test_incremental_with_metadata(self):
        """Test incremental scanning with metadata."""
        # Save checkpoint with metadata
        processed_files = {"file1.txt": {"hash": "abc123"}}
        metadata = {
            "scan_version": "1.0",
            "scan_type": "incremental",
            "user": "test_user"
        }
        Incremental.save_checkpoint(self.scan_path, processed_files, metadata)

        # Load and verify metadata
        checkpoint = Incremental.load_checkpoint(self.scan_path)
        assert checkpoint["metadata"] == metadata

        # Update checkpoint and verify metadata is preserved
        new_files = {"file2.txt": {"hash": "def456"}}
        Incremental.update_checkpoint(self.scan_path, new_files)

        updated = Incremental.load_checkpoint(self.scan_path)
        assert updated["metadata"] == metadata
        assert "file1.txt" in updated["processed_files"]
        assert "file2.txt" in updated["processed_files"]

    def test_incremental_error_handling(self):
        """Test incremental error handling."""
        # Test with invalid JSON in checkpoint file
        checkpoint_file = Path(self.scan_path) / Incremental.CHECKPOINT_FILE
        with open(checkpoint_file, 'w', encoding="utf-8") as f:
            f.write("invalid json content")

        # Should handle JSON decode error gracefully
        result = Incremental.load_checkpoint(self.scan_path)
        assert result is None

        # Should still be able to save new checkpoint
        Incremental.save_checkpoint(
            self.scan_path, {
                "file1.txt": {
                    "hash": "abc123"}})
        new_checkpoint = Incremental.load_checkpoint(self.scan_path)
        assert new_checkpoint is not None
