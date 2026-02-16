"""Tests for FileInfo module."""

import tempfile
from pathlib import Path

import pytest

from nodupe.tools.scanner_engine.file_info import FileInfo


class TestFileInfo:
    """Test FileInfo class."""

    def test_file_info_initialization(self):
        """Test FileInfo initialization."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = temp_file.name

        try:
            file_info = FileInfo(Path(temp_path))
            assert isinstance(file_info, FileInfo)
        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_get_info_basic(self):
        """Test getting basic file information."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_content = b"test content for file info"
            temp_file.write(test_content)
            temp_path = temp_file.name

        try:
            file_info = FileInfo(Path(temp_path))
            info = file_info.get_info()

            # Check that we have basic file info - actual structure is simpler
            assert 'path' in info
            assert 'size' in info
            assert 'mtime' in info
            assert 'ctime' in info
            assert 'is_file' in info
            assert 'is_dir' in info
            assert 'is_symlink' in info

            # File path should be the temp file path
            assert str(Path(temp_path)) in info['path']

            # File size should match
            assert info['size'] == len(test_content)

            # Modified time should be a float
            assert isinstance(info['mtime'], float)

            # Should be a file, not a directory
            assert info['is_file'] is True
            assert info['is_dir'] is False

        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_get_info_different_file_types(self):
        """Test getting info for different file types."""
        test_cases = [
            ".txt",
            ".log",
            ".json",
            ".csv",
            ".bin",
            ".dat"
        ]

        for extension in test_cases:
            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                temp_file.write(b"test content")
                temp_path = temp_file.name

            try:
                file_info = FileInfo(Path(temp_path))
                info = file_info.get_info()

                # Basic file info should be present
                assert 'path' in info
                assert 'size' in info
                assert 'mtime' in info
                assert info['is_file'] is True

            finally:
                # Clean up
                Path(temp_path).unlink()

    def test_get_info_empty_file(self):
        """Test getting info for empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write nothing
            temp_path = temp_file.name

        try:
            file_info = FileInfo(Path(temp_path))
            info = file_info.get_info()

            assert info['size'] == 0
            assert info['is_file'] is True

        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_get_info_large_file(self):
        """Test getting info for large file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Create 1MB file
            large_content = b"X" * (1024 * 1024)
            temp_file.write(large_content)
            temp_path = temp_file.name

        try:
            file_info = FileInfo(Path(temp_path))
            info = file_info.get_info()

            assert info['size'] == len(large_content)
            assert info['is_file'] is True

        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_get_info_nonexistent_file(self):
        """Test getting info for nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.txt")

        file_info = FileInfo(nonexistent_path)
        with pytest.raises(FileNotFoundError):  # Should raise FileNotFoundError
            file_info.get_info()

    def test_get_info_directory(self):
        """Test getting info for directory instead of file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)

            file_info = FileInfo(dir_path)
            info = file_info.get_info()

            # Should work for directories too
            assert info['is_dir'] is True
            assert info['is_file'] is False

    def test_get_info_special_characters(self):
        """Test getting info for files with special characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with special characters
            test_cases = [
                "file with spaces.txt",
                "file-with-dashes.txt",
                "file_with_underscores.txt",
                "file.with.dots.txt",
                "file[with]brackets.txt"
            ]

            for filename in test_cases:
                file_path = Path(temp_dir) / filename
                file_path.write_text("test content")

                file_info = FileInfo(file_path)
                info = file_info.get_info()

                assert info['size'] > 0
                assert info['is_file'] is True
                assert filename in info['path']

    def test_get_info_binary_file(self):
        """Test getting info for binary file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as temp_file:
            # Write binary data
            binary_data = bytes(range(256))  # 0-255
            temp_file.write(binary_data)
            temp_path = temp_file.name

        try:
            file_info = FileInfo(Path(temp_path))
            info = file_info.get_info()

            assert info['size'] == len(binary_data)
            assert info['is_file'] is True
            assert '.bin' in info['path']

        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_get_info_multiple_calls(self):
        """Test that multiple calls to get_info return consistent results."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = temp_file.name

        try:
            file_info = FileInfo(Path(temp_path))

            # Get info multiple times
            info1 = file_info.get_info()
            info2 = file_info.get_info()
            info3 = file_info.get_info()

            # All should be the same
            assert info1 == info2 == info3

        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_get_info_file_modification(self):
        """Test that file info reflects file modifications."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"original")
            temp_path = temp_file.name

        try:
            file_info = FileInfo(Path(temp_path))
            original_info = file_info.get_info()

            # Modify the file with different sized content
            with open(temp_path, 'wb') as f:
                f.write(b"modified content that is longer")

            modified_info = file_info.get_info()

            # File size should be different
            assert original_info['size'] != modified_info['size']
            assert original_info['size'] < modified_info['size']  # Original should be smaller

            # Modified time might be different (depends on system)
            # We can't reliably test this as some systems may not update mtime immediately

        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_get_info_different_files(self):
        """Test that different files have different info."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple files with different sized content
            file1 = Path(temp_dir) / "file1.txt"
            file2 = Path(temp_dir) / "file2.txt"

            file1.write_text("short")
            file2.write_text("this is much longer content")

            file_info1 = FileInfo(file1)
            file_info2 = FileInfo(file2)

            info1 = file_info1.get_info()
            info2 = file_info2.get_info()

            # Should have different file paths
            assert info1['path'] != info2['path']

            # Should have different file sizes (different content)
            assert info1['size'] != info2['size']
            assert info1['size'] < info2['size']  # First file should be smaller

    def test_get_info_file_extensions(self):
        """Test file type detection based on extensions."""
        extensions = [
            '.txt', '.log', '.json', '.csv', '.xml', '.html', '.css', '.js',
            '.py', '.java', '.c', '.cpp', '.h', '.bin', '.dat', '.zip',
            '.tar', '.gz', '.pdf', '.jpg', '.png', '.gif'
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for extension in extensions:
                file_path = Path(temp_dir) / f"test{extension}"
                file_path.write_text("test content")

                file_info = FileInfo(file_path)
                info = file_info.get_info()

                # Basic file info should be present
                assert info['is_file'] is True
                assert extension in info['path']

    def test_get_info_performance(self):
        """Test performance of getting file info."""
        import time

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = temp_file.name

        try:
            file_info = FileInfo(Path(temp_path))

            # Time multiple calls
            start_time = time.time()
            for _ in range(100):
                file_info.get_info()
            end_time = time.time()

            # Should be fast (less than 1 second for 100 calls)
            elapsed = end_time - start_time
            assert elapsed < 1.0

        finally:
            # Clean up
            Path(temp_path).unlink()
