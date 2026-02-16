"""Tests for FileWalker module."""

import pytest
import tempfile
import os
from pathlib import Path
from nodupe.tools.scanner_engine.walker import FileWalker, create_file_walker
from nodupe.tools.scanner_engine.file_info import FileInfo

class TestFileWalker:
    """Test FileWalker class."""

    def test_file_walker_initialization(self):
        """Test FileWalker initialization."""
        walker = FileWalker()
        assert isinstance(walker, FileWalker)

    def test_create_file_walker(self):
        """Test create_file_walker factory function."""
        walker = create_file_walker()
        assert isinstance(walker, FileWalker)

    def test_walk_basic_functionality(self, tmp_path):
        """Test basic file walking functionality."""
        # Create test directory structure
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "subdir" / "file2.txt"
        test_file3 = tmp_path / "subdir" / "file3.log"

        test_file1.write_text("content1")
        test_file2.parent.mkdir()
        test_file2.write_text("content2")
        test_file3.write_text("content3")

        walker = FileWalker()
        results = walker.walk(str(tmp_path))

        # Should find all files
        assert len(results) == 3

        # Check that we have the expected files
        file_paths = [r['path'] for r in results]
        assert any('file1.txt' in path for path in file_paths)
        assert any('file2.txt' in path for path in file_paths)
        assert any('file3.log' in path for path in file_paths)

    def test_walk_with_file_filter(self, tmp_path):
        """Test file walking with filter."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.log"
        test_file3 = tmp_path / "file3.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")
        test_file3.write_text("content3")

        # Filter for .txt files only - file_filter receives file_info dict
        def txt_filter(file_info):
            return file_info['path'].endswith('.txt')

        walker = FileWalker()
        results = walker.walk(str(tmp_path), file_filter=txt_filter)

        # Should only find .txt files
        assert len(results) == 2
        for result in results:
            assert result['path'].endswith('.txt')

    def test_walk_with_progress_callback(self, tmp_path):
        """Test file walking with progress callback."""
        # Create enough test files to potentially trigger progress updates
        for i in range(50):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text(f"content{i}")

        progress_updates = []

        def progress_callback(progress):
            progress_updates.append(progress)

        walker = FileWalker()
        results = walker.walk(str(tmp_path), on_progress=progress_callback)

        # Should have found all files
        assert len(results) == 50

        # Progress updates are sent every 100ms, so for fast systems they might not be sent
        # If we got progress updates, verify they have the expected structure
        if len(progress_updates) > 0:
            for update in progress_updates:
                assert 'files_processed' in update
                assert 'directories_processed' in update
                assert 'errors_encountered' in update
                assert 'elapsed_time' in update
                assert 'files_per_second' in update

    def test_walk_empty_directory(self, tmp_path):
        """Test walking empty directory."""
        walker = FileWalker()
        results = walker.walk(str(tmp_path))

        # Should return empty list for empty directory
        assert len(results) == 0

    def test_walk_nonexistent_directory(self):
        """Test walking nonexistent directory."""
        walker = FileWalker()
        # FileWalker handles nonexistent directories gracefully, so it won't raise an exception
        # Instead, it should return empty results
        results = walker.walk("/nonexistent/directory/path")
        assert len(results) == 0

    def test_walk_statistics(self, tmp_path):
        """Test statistics collection during walking."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "subdir" / "file2.txt"

        test_file1.write_text("content1")
        test_file2.parent.mkdir()
        test_file2.write_text("content2")

        walker = FileWalker()
        results = walker.walk(str(tmp_path))

        # Get statistics
        stats = walker.get_statistics()

        # Should have statistics
        assert 'total_files' in stats
        assert 'total_directories' in stats
        assert 'total_errors' in stats
        assert 'total_time' in stats

        # Should have found 2 files
        assert stats['total_files'] == 2
        assert stats['total_directories'] >= 1  # At least the root directory

    def test_walk_file_info_collection(self, tmp_path):
        """Test that file information is properly collected."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "test content for file info"
        test_file.write_text(test_content)

        walker = FileWalker()
        results = walker.walk(str(tmp_path))

        # Should have one result
        assert len(results) == 1

        result = results[0]

        # Check that we have basic file info
        assert 'path' in result
        assert 'relative_path' in result
        assert 'size' in result
        assert 'modified_time' in result
        assert 'name' in result
        assert 'extension' in result

        # File path should be absolute
        assert Path(result['path']).is_absolute()

        # File size should match
        assert result['size'] == len(test_content.encode())

    def test_walk_large_directory_structure(self, tmp_path):
        """Test walking larger directory structure."""
        # Create nested directory structure
        for i in range(5):
            dir_path = tmp_path / f"dir_{i}"
            dir_path.mkdir()

            for j in range(3):
                file_path = dir_path / f"file_{j}.txt"
                file_path.write_text(f"content {i}-{j}")

        walker = FileWalker()
        results = walker.walk(str(tmp_path))

        # Should find all files (5 dirs * 3 files each)
        assert len(results) == 15

    def test_walk_with_special_characters(self, tmp_path):
        """Test walking with files containing special characters."""
        # Create files with special characters
        test_file1 = tmp_path / "file with spaces.txt"
        test_file2 = tmp_path / "file-with-dashes.txt"
        test_file3 = tmp_path / "file_with_underscores.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")
        test_file3.write_text("content3")

        walker = FileWalker()
        results = walker.walk(str(tmp_path))

        # Should find all files
        assert len(results) == 3

        # Check that special characters are preserved
        file_paths = [r['path'] for r in results]
        assert any('file with spaces.txt' in path for path in file_paths)
        assert any('file-with-dashes.txt' in path for path in file_paths)
        assert any('file_with_underscores.txt' in path for path in file_paths)

    def test_walk_reset_counters(self, tmp_path):
        """Test that counters can be reset between walks."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")

        walker = FileWalker()

        # First walk
        results1 = walker.walk(str(tmp_path))
        stats1 = walker.get_statistics()

        # Reset counters
        walker._reset_counters()

        # Second walk
        results2 = walker.walk(str(tmp_path))
        stats2 = walker.get_statistics()

        # Both walks should have same results
        assert len(results1) == len(results2) == 2
        assert stats1['total_files'] == stats2['total_files'] == 2
