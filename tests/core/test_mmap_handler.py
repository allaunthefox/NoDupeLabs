"""Tests for memory-mapped file handler module."""

import pytest
import mmap
from pathlib import Path
from nodupe.core.mmap_handler import MMAPHandler


class TestMMAPHandler:
    """Test MMAPHandler class."""

    def test_create_mmap(self, tmp_path):
        """Test memory-mapped file creation."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Hello, World!" * 100)

        mapped = MMAPHandler.create_mmap(str(test_file))
        assert mapped is not None
        assert len(mapped) > 0
        mapped.close()

    def test_create_mmap_empty_file(self, tmp_path):
        """Test memory-mapping empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        mapped = MMAPHandler.create_mmap(str(test_file))
        assert mapped is not None
        mapped.close()

    def test_mmap_context(self, tmp_path):
        """Test memory-mapped file context manager."""
        test_file = tmp_path / "test.txt"
        test_data = b"Hello, World!" * 100
        test_file.write_bytes(test_data)

        with MMAPHandler.mmap_context(str(test_file)) as mapped:
            assert mapped is not None
            assert len(mapped) == len(test_data)

    def test_read_chunk(self, tmp_path):
        """Test reading chunk from memory-mapped file."""
        test_file = tmp_path / "test.txt"
        test_data = b"Hello, World!" * 100
        test_file.write_bytes(test_data)

        with MMAPHandler.mmap_context(str(test_file)) as mapped:
            chunk = MMAPHandler.read_chunk(mapped, 0, 13)
            assert chunk == b"Hello, World!"

            # Test reading from different offset
            chunk2 = MMAPHandler.read_chunk(mapped, 13, 13)
            assert chunk2 == b"Hello, World!"

    def test_get_file_size(self, tmp_path):
        """Test getting file size from memory-mapped file."""
        test_file = tmp_path / "test.txt"
        test_data = b"Hello, World!"
        test_file.write_bytes(test_data)

        with MMAPHandler.mmap_context(str(test_file)) as mapped:
            size = MMAPHandler.get_file_size(mapped)
            assert size == len(test_data)

    def test_mmap_read_access(self, tmp_path):
        """Test memory-mapped file with read access."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test data")

        mapped = MMAPHandler.create_mmap(str(test_file), access_mode=mmap.ACCESS_READ)
        assert mapped is not None
        # Should be able to read
        data = mapped.read(4)
        assert data == b"Test"
        mapped.close()
