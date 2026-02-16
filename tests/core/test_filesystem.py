"""Tests for filesystem module."""

from pathlib import Path

import pytest

from nodupe.tools.os_filesystem.filesystem import Filesystem, FilesystemError


class TestFilesystem:
    """Test Filesystem class."""

    def test_safe_read(self, tmp_path):
        """Test safe file reading."""
        test_file = tmp_path / "test.txt"
        test_data = b"Hello, World!"
        test_file.write_bytes(test_data)

        data = Filesystem.safe_read(test_file)
        assert data == test_data

    def test_safe_read_nonexistent(self, tmp_path):
        """Test reading nonexistent file."""
        with pytest.raises(FilesystemError):
            Filesystem.safe_read(tmp_path / "nonexistent.txt")

    def test_safe_read_directory(self, tmp_path):
        """Test reading directory instead of file."""
        with pytest.raises(FilesystemError):
            Filesystem.safe_read(tmp_path)

    def test_safe_read_size_limit(self, tmp_path):
        """Test reading with size limit."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"X" * 1000)

        # Should succeed
        Filesystem.safe_read(test_file, max_size=2000)

        # Should fail
        with pytest.raises(FilesystemError):
            Filesystem.safe_read(test_file, max_size=500)

    def test_safe_write(self, tmp_path):
        """Test safe file writing."""
        test_file = tmp_path / "test.txt"
        test_data = b"Hello, World!"

        Filesystem.safe_write(test_file, test_data)

        assert test_file.exists()
        assert test_file.read_bytes() == test_data

    def test_safe_write_atomic(self, tmp_path):
        """Test atomic file writing."""
        test_file = tmp_path / "test.txt"
        test_data = b"Atomic write test"

        Filesystem.safe_write(test_file, test_data, atomic=True)

        assert test_file.exists()
        assert test_file.read_bytes() == test_data

    def test_safe_write_non_atomic(self, tmp_path):
        """Test non-atomic file writing."""
        test_file = tmp_path / "test.txt"
        test_data = b"Non-atomic write test"

        Filesystem.safe_write(test_file, test_data, atomic=False)

        assert test_file.exists()
        assert test_file.read_bytes() == test_data

    def test_safe_write_creates_parent_dir(self, tmp_path):
        """Test that safe_write creates parent directories."""
        test_file = tmp_path / "subdir" / "test.txt"
        test_data = b"Test"

        Filesystem.safe_write(test_file, test_data)

        assert test_file.exists()
        assert test_file.read_bytes() == test_data

    def test_validate_path(self, tmp_path):
        """Test path validation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Should succeed
        assert Filesystem.validate_path(test_file, must_exist=True)

    def test_validate_path_nonexistent(self, tmp_path):
        """Test validation of nonexistent path."""
        with pytest.raises(FilesystemError):
            Filesystem.validate_path(tmp_path / "nonexistent.txt", must_exist=True)

    def test_get_size(self, tmp_path):
        """Test getting file size."""
        test_file = tmp_path / "test.txt"
        test_data = b"Hello, World!"
        test_file.write_bytes(test_data)

        size = Filesystem.get_size(test_file)
        assert size == len(test_data)

    def test_get_size_nonexistent(self, tmp_path):
        """Test getting size of nonexistent file."""
        with pytest.raises(FilesystemError):
            Filesystem.get_size(tmp_path / "nonexistent.txt")

    def test_list_directory(self, tmp_path):
        """Test listing directory contents."""
        # Create test files
        (tmp_path / "file1.txt").write_text("test1")
        (tmp_path / "file2.txt").write_text("test2")
        (tmp_path / "file3.log").write_text("test3")

        # List all files
        files = Filesystem.list_directory(tmp_path)
        assert len(files) == 3

        # List with pattern
        txt_files = Filesystem.list_directory(tmp_path, pattern="*.txt")
        assert len(txt_files) == 2

    def test_list_directory_nonexistent(self, tmp_path):
        """Test listing nonexistent directory."""
        with pytest.raises(FilesystemError):
            Filesystem.list_directory(tmp_path / "nonexistent")

    def test_ensure_directory(self, tmp_path):
        """Test ensuring directory exists."""
        test_dir = tmp_path / "subdir" / "nested"

        Filesystem.ensure_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directory_existing(self, tmp_path):
        """Test ensuring existing directory."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()

        # Should not raise error
        Filesystem.ensure_directory(test_dir)

        assert test_dir.exists()

    def test_remove_file(self, tmp_path):
        """Test file removal."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        Filesystem.remove_file(test_file)

        assert not test_file.exists()

    def test_remove_file_nonexistent(self, tmp_path):
        """Test removing nonexistent file."""
        # Should not raise error with missing_ok=True (default)
        Filesystem.remove_file(tmp_path / "nonexistent.txt")

        # Should raise error with missing_ok=False
        with pytest.raises(FilesystemError):
            Filesystem.remove_file(tmp_path / "nonexistent.txt", missing_ok=False)

    def test_copy_file(self, tmp_path):
        """Test file copying."""
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("test content")

        Filesystem.copy_file(src, dst)

        assert dst.exists()
        assert dst.read_text() == "test content"

    def test_copy_file_nonexistent_source(self, tmp_path):
        """Test copying nonexistent file."""
        with pytest.raises(FilesystemError):
            Filesystem.copy_file(tmp_path / "nonexistent.txt", tmp_path / "dest.txt")

    def test_copy_file_existing_dest(self, tmp_path):
        """Test copying to existing destination."""
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("source")
        dst.write_text("dest")

        # Should fail without overwrite
        with pytest.raises(FilesystemError):
            Filesystem.copy_file(src, dst, overwrite=False)

        # Should succeed with overwrite
        Filesystem.copy_file(src, dst, overwrite=True)
        assert dst.read_text() == "source"

    def test_move_file(self, tmp_path):
        """Test file moving."""
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("test content")

        Filesystem.move_file(src, dst)

        assert not src.exists()
        assert dst.exists()
        assert dst.read_text() == "test content"

    def test_move_file_nonexistent_source(self, tmp_path):
        """Test moving nonexistent file."""
        with pytest.raises(FilesystemError):
            Filesystem.move_file(tmp_path / "nonexistent.txt", tmp_path / "dest.txt")

    def test_move_file_existing_dest(self, tmp_path):
        """Test moving to existing destination."""
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("source")
        dst.write_text("dest")

        # Should fail without overwrite
        with pytest.raises(FilesystemError):
            Filesystem.move_file(src, dst, overwrite=False)

        # Should succeed with overwrite
        Filesystem.move_file(src, dst, overwrite=True)
        assert not src.exists()
        assert dst.read_text() == "source"
