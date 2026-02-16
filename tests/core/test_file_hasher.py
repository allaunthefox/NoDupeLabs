"""Tests for FileHasher module."""

import hashlib
import tempfile
from pathlib import Path

import pytest

from nodupe.tools.hashing.hasher_logic import FileHasher, create_file_hasher


class TestFileHasher:
    """Test FileHasher class."""

    def test_file_hasher_initialization(self):
        """Test FileHasher initialization."""
        hasher = FileHasher()
        assert isinstance(hasher, FileHasher)
        assert hasher.get_algorithm() == 'sha256'
        assert hasher.get_buffer_size() == 65536

    def test_create_file_hasher(self):
        """Test create_file_hasher factory function."""
        hasher = create_file_hasher()
        assert isinstance(hasher, FileHasher)

    def test_create_file_hasher_with_custom_params(self):
        """Test create_file_hasher with custom parameters."""
        hasher = create_file_hasher(algorithm='md5', buffer_size=32768)
        assert hasher.get_algorithm() == 'md5'
        assert hasher.get_buffer_size() == 32768

    def test_set_and_get_algorithm(self):
        """Test setting and getting hash algorithm."""
        hasher = FileHasher()

        # Test setting algorithm
        hasher.set_algorithm('md5')
        assert hasher.get_algorithm() == 'md5'

        hasher.set_algorithm('sha512')
        assert hasher.get_algorithm() == 'sha512'

    def test_set_and_get_buffer_size(self):
        """Test setting and getting buffer size."""
        hasher = FileHasher()

        # Test setting buffer size
        hasher.set_buffer_size(32768)
        assert hasher.get_buffer_size() == 32768

        hasher.set_buffer_size(131072)
        assert hasher.get_buffer_size() == 131072

    def test_get_available_algorithms(self):
        """Test getting available algorithms."""
        hasher = FileHasher()
        algorithms = hasher.get_available_algorithms()

        # Should have standard algorithms
        assert 'sha256' in algorithms
        assert 'md5' in algorithms
        assert 'sha1' in algorithms
        assert 'sha512' in algorithms

    def test_hash_string(self):
        """Test hashing strings."""
        hasher = FileHasher()
        test_string = "test string to hash"

        # Test with different algorithms
        sha256_hash = hasher.hash_string(test_string)
        assert isinstance(sha256_hash, str)
        assert len(sha256_hash) > 0

        # Test with MD5
        hasher.set_algorithm('md5')
        md5_hash = hasher.hash_string(test_string)
        assert isinstance(md5_hash, str)
        assert len(md5_hash) > 0

        # Hashes should be different for different algorithms
        assert sha256_hash != md5_hash

    def test_hash_bytes(self):
        """Test hashing bytes."""
        hasher = FileHasher()
        test_bytes = b"test bytes to hash"

        hash_result = hasher.hash_bytes(test_bytes)
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0

    def test_hash_file(self, tmp_path):
        """Test hashing files."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "test content for hashing"
        test_file.write_text(test_content)

        hasher = FileHasher()
        file_hash = hasher.hash_file(str(test_file))

        assert isinstance(file_hash, str)
        assert len(file_hash) > 0

        # Verify hash is consistent
        file_hash2 = hasher.hash_file(str(test_file))
        assert file_hash == file_hash2

    def test_hash_file_with_progress(self, tmp_path):
        """Test hashing files with progress callback."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        progress_updates = []

        def progress_callback(progress):
            progress_updates.append(progress)

        hasher = FileHasher()
        file_hash = hasher.hash_file(str(test_file), on_progress=progress_callback)

        assert isinstance(file_hash, str)
        assert len(file_hash) > 0
        assert len(progress_updates) > 0

    def test_hash_files_multiple(self, tmp_path):
        """Test hashing multiple files."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.txt"
        test_file3 = tmp_path / "file3.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")
        test_file3.write_text("content3")

        hasher = FileHasher()
        file_paths = [str(test_file1), str(test_file2), str(test_file3)]

        results = hasher.hash_files(file_paths)

        # hash_files returns a dictionary mapping file paths to hashes
        assert isinstance(results, dict)
        assert len(results) == 3

        for file_path, hash_value in results.items():
            assert file_path in file_paths
            assert isinstance(hash_value, str)
            assert len(hash_value) > 0

    def test_hash_files_with_progress(self, tmp_path):
        """Test hashing multiple files with progress."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")

        progress_updates = []

        def progress_callback(progress):
            progress_updates.append(progress)

        hasher = FileHasher()
        file_paths = [str(test_file1), str(test_file2)]

        results = hasher.hash_files(file_paths, on_progress=progress_callback)

        assert len(results) == 2
        assert len(progress_updates) > 0

    def test_verify_hash(self, tmp_path):
        """Test hash verification."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "test content for verification"
        test_file.write_text(test_content)

        hasher = FileHasher()

        # Get the actual hash
        actual_hash = hasher.hash_file(str(test_file))

        # Verify with correct hash
        assert hasher.verify_hash(str(test_file), actual_hash) is True

        # Verify with incorrect hash
        assert hasher.verify_hash(str(test_file), "incorrect_hash") is False

    def test_hash_consistency(self, tmp_path):
        """Test that hashing is consistent."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "consistent test content"
        test_file.write_text(test_content)

        hasher = FileHasher()

        # Hash multiple times
        hash1 = hasher.hash_file(str(test_file))
        hash2 = hasher.hash_file(str(test_file))
        hash3 = hasher.hash_file(str(test_file))

        # All should be the same
        assert hash1 == hash2 == hash3

    def test_hash_different_algorithms(self, tmp_path):
        """Test hashing with different algorithms."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hasher = FileHasher()

        # Test different algorithms
        algorithms_to_test = ['md5', 'sha1', 'sha256', 'sha512']

        hashes = {}
        for algo in algorithms_to_test:
            hasher.set_algorithm(algo)
            hashes[algo] = hasher.hash_file(str(test_file))

        # All hashes should be different
        hash_values = list(hashes.values())
        assert len(set(hash_values)) == len(hash_values)  # All unique

        # All should be valid hex strings
        for hash_val in hash_values:
            assert all(c in '0123456789abcdef' for c in hash_val.lower())

    def test_hash_large_file(self, tmp_path):
        """Test hashing large files."""
        # Create large test file (1MB)
        test_file = tmp_path / "large_test.txt"
        large_content = "X" * (1024 * 1024)  # 1MB
        test_file.write_text(large_content)

        hasher = FileHasher()
        file_hash = hasher.hash_file(str(test_file))

        assert isinstance(file_hash, str)
        assert len(file_hash) > 0

    def test_hash_empty_file(self, tmp_path):
        """Test hashing empty files."""
        # Create empty test file
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        hasher = FileHasher()
        file_hash = hasher.hash_file(str(test_file))

        assert isinstance(file_hash, str)
        assert len(file_hash) > 0

    def test_hash_nonexistent_file(self):
        """Test hashing nonexistent file."""
        hasher = FileHasher()

        with pytest.raises(Exception):  # Should raise some kind of error
            hasher.hash_file("/nonexistent/file.txt")

    def test_hash_directory(self, tmp_path):
        """Test hashing directory instead of file."""
        hasher = FileHasher()

        with pytest.raises(Exception):  # Should raise some kind of error
            hasher.hash_file(str(tmp_path))

    def test_buffer_size_impact(self, tmp_path):
        """Test that buffer size affects performance (conceptually)."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content for buffer testing")

        hasher1 = FileHasher(buffer_size=4096)  # Small buffer
        hasher2 = FileHasher(buffer_size=131072)  # Large buffer

        # Both should produce the same hash
        hash1 = hasher1.hash_file(str(test_file))
        hash2 = hasher2.hash_file(str(test_file))

        assert hash1 == hash2

    def test_hash_files_empty_list(self):
        """Test hashing empty file list."""
        hasher = FileHasher()
        results = hasher.hash_files([])

        # hash_files returns a dictionary
        assert isinstance(results, dict)
        assert len(results) == 0

    def test_hash_files_nonexistent_file(self):
        """Test hashing file list with nonexistent file."""
        hasher = FileHasher()
        file_paths = ["/nonexistent/file.txt"]

        # hash_files doesn't raise exceptions for nonexistent files - it just skips them
        results = hasher.hash_files(file_paths)
        assert isinstance(results, dict)
        assert len(results) == 0  # No files were processed

    def test_hash_files_mixed_valid_invalid(self, tmp_path):
        """Test hashing file list with mix of valid and invalid files."""
        # Create valid file
        test_file = tmp_path / "valid.txt"
        test_file.write_text("valid content")

        hasher = FileHasher()
        file_paths = [str(test_file), "/nonexistent/file.txt"]

        # hash_files doesn't raise exceptions - it processes valid files and skips invalid ones
        results = hasher.hash_files(file_paths)
        assert isinstance(results, dict)
        assert len(results) == 1  # Only the valid file was processed
        assert str(test_file) in results
