"""Tests for FileProcessor module."""

import tempfile
from pathlib import Path

import pytest

from nodupe.tools.scanner_engine.processor import FileProcessor, create_file_processor
from nodupe.tools.scanner_engine.walker import FileWalker


class TestFileProcessor:
    """Test FileProcessor class."""

    def test_file_processor_initialization(self):
        """Test FileProcessor initialization."""
        processor = FileProcessor()
        assert isinstance(processor, FileProcessor)

    def test_create_file_processor(self):
        """Test create_file_processor factory function."""
        processor = create_file_processor()
        assert isinstance(processor, FileProcessor)

    def test_create_file_processor_with_walker(self):
        """Test create_file_processor with custom walker."""
        walker = FileWalker()
        processor = create_file_processor(file_walker=walker)
        assert isinstance(processor, FileProcessor)

    def test_process_files_basic(self, tmp_path):
        """Test basic file processing."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Should process files and return results
        assert isinstance(results, list)
        assert len(results) == 2

        for result in results:
            assert 'path' in result
            assert 'size' in result
            assert 'hash' in result
            assert 'extension' in result

    def test_process_files_with_filter(self, tmp_path):
        """Test file processing with filter."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.log"
        test_file3 = tmp_path / "file3.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")
        test_file3.write_text("content3")

        # Filter for .txt files only - file_info uses 'path' not 'file_path'
        def txt_filter(file_info):
            return file_info['path'].endswith('.txt')

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path), file_filter=txt_filter)

        # Should only process .txt files
        assert len(results) == 2
        for result in results:
            assert result['path'].endswith('.txt')

    def test_process_files_empty_directory(self, tmp_path):
        """Test processing empty directory."""
        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Should return empty list for empty directory
        assert isinstance(results, list)
        assert len(results) == 0

    def test_detect_duplicates(self, tmp_path):
        """Test duplicate detection."""
        # Create test files with same content (should be duplicates)
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.txt"
        test_file3 = tmp_path / "file3.txt"  # Different content

        content1 = "duplicate content"
        content2 = "different content"

        test_file1.write_text(content1)
        test_file2.write_text(content1)  # Same as file1
        test_file3.write_text(content2)  # Different

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Detect duplicates - returns same list with duplicate info added
        duplicates = processor.detect_duplicates(results)

        # Should return the same list with duplicate info
        assert isinstance(duplicates, list)
        assert len(duplicates) == 3  # All files are returned

        # Check that duplicates are marked correctly
        duplicate_files = [f for f in duplicates if f.get('is_duplicate', False)]
        original_files = [f for f in duplicates if not f.get('is_duplicate', False)]

        assert len(duplicate_files) == 1  # One file should be marked as duplicate
        assert len(original_files) == 2  # Two files should be originals (one is the original of the duplicate)

        # Check that the duplicate points to the original
        for dup_file in duplicate_files:
            assert 'duplicate_of' in dup_file
            assert dup_file['duplicate_of'] is not None

    def test_detect_duplicates_no_duplicates(self, tmp_path):
        """Test duplicate detection with no duplicates."""
        # Create test files with different content
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.txt"
        test_file3 = tmp_path / "file3.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")
        test_file3.write_text("content3")

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Detect duplicates - returns same list with duplicate info
        duplicates = processor.detect_duplicates(results)

        # Should return all files, but none should be marked as duplicates
        assert isinstance(duplicates, list)
        assert len(duplicates) == 3  # All files are returned

        # Check that no files are marked as duplicates
        duplicate_files = [f for f in duplicates if f.get('is_duplicate', False)]
        assert len(duplicate_files) == 0  # No duplicates

    def test_batch_process_files(self, tmp_path):
        """Test batch processing of files."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.txt"
        test_file3 = tmp_path / "file3.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")
        test_file3.write_text("content3")

        processor = FileProcessor()
        file_paths = [str(test_file1), str(test_file2), str(test_file3)]

        results = processor.batch_process_files(file_paths)

        # Should process all files
        assert isinstance(results, list)
        assert len(results) == 3

        for result in results:
            assert 'path' in result
            assert 'size' in result
            assert 'hash' in result

    def test_batch_process_files_empty_list(self):
        """Test batch processing with empty file list."""
        processor = FileProcessor()
        results = processor.batch_process_files([])

        # Should return empty list
        assert isinstance(results, list)
        assert len(results) == 0

    def test_hash_algorithm_configuration(self):
        """Test hash algorithm configuration."""
        processor = FileProcessor()

        # Test setting algorithm
        processor.set_hash_algorithm('md5')
        assert processor.get_hash_algorithm() == 'md5'

        processor.set_hash_algorithm('sha512')
        assert processor.get_hash_algorithm() == 'sha512'

    def test_hash_buffer_size_configuration(self):
        """Test hash buffer size configuration."""
        processor = FileProcessor()

        # Test setting buffer size
        processor.set_hash_buffer_size(32768)
        assert processor.get_hash_buffer_size() == 32768

        processor.set_hash_buffer_size(131072)
        assert processor.get_hash_buffer_size() == 131072

    def test_process_files_with_custom_hash_algorithm(self, tmp_path):
        """Test processing files with custom hash algorithm."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        processor = FileProcessor()
        processor.set_hash_algorithm('md5')

        results = processor.process_files(str(tmp_path))

        # Should use MD5 algorithm
        assert len(results) == 1
        assert results[0]['hash'] is not None
        assert len(results[0]['hash']) > 0
        # MD5 hash should be 32 characters
        assert len(results[0]['hash']) == 32

    def test_process_files_with_custom_buffer_size(self, tmp_path):
        """Test processing files with custom buffer size."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        processor = FileProcessor()
        processor.set_hash_buffer_size(32768)

        results = processor.process_files(str(tmp_path))

        # Should process successfully with custom buffer size
        assert len(results) == 1
        assert results[0]['hash'] is not None

    def test_process_files_with_large_files(self, tmp_path):
        """Test processing large files."""
        # Create large test files
        test_file1 = tmp_path / "large1.txt"
        test_file2 = tmp_path / "large2.txt"

        large_content = "X" * (1024 * 1024)  # 1MB

        test_file1.write_text(large_content)
        test_file2.write_text(large_content)  # Same content for duplicate detection

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Should process large files successfully
        assert len(results) == 2
        for result in results:
            assert result['size'] == len(large_content.encode())
            assert result['hash'] is not None

        # Should detect duplicates
        duplicates = processor.detect_duplicates(results)
        assert len(duplicates) == 2  # Both files returned

        # One should be marked as duplicate
        duplicate_files = [f for f in duplicates if f.get('is_duplicate', False)]
        assert len(duplicate_files) == 1  # One duplicate

    def test_process_files_with_special_characters(self, tmp_path):
        """Test processing files with special characters."""
        # Create files with special characters
        test_file1 = tmp_path / "file with spaces.txt"
        test_file2 = tmp_path / "file-with-dashes.txt"
        test_file3 = tmp_path / "file_with_underscores.txt"

        test_file1.write_text("content1")
        test_file2.write_text("content2")
        test_file3.write_text("content3")

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Should process all files
        assert len(results) == 3

        # Check that special characters are preserved
        file_paths = [r['path'] for r in results]
        assert any('file with spaces.txt' in path for path in file_paths)
        assert any('file-with-dashes.txt' in path for path in file_paths)
        assert any('file_with_underscores.txt' in path for path in file_paths)

    def test_process_files_error_handling(self):
        """Test error handling during file processing."""
        processor = FileProcessor()

        # Test with nonexistent directory - processor handles errors gracefully
        results = processor.process_files("/nonexistent/directory/path")
        assert isinstance(results, list)
        assert len(results) == 0  # No files processed

    def test_process_files_with_nested_directories(self, tmp_path):
        """Test processing files in nested directory structure."""
        # Create nested directory structure
        for i in range(3):
            dir_path = tmp_path / "level1" / f"level2_{i}"
            dir_path.mkdir(parents=True)

            for j in range(2):
                file_path = dir_path / f"file_{j}.txt"
                file_path.write_text(f"content {i}-{j}")

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Should find all files (3 dirs * 2 files each)
        assert len(results) == 6

    def test_process_files_with_mixed_file_types(self, tmp_path):
        """Test processing files with different types."""
        # Create files with different extensions
        test_file1 = tmp_path / "file.txt"
        test_file2 = tmp_path / "file.log"
        test_file3 = tmp_path / "file.json"
        test_file4 = tmp_path / "file.csv"

        test_file1.write_text("text content")
        test_file2.write_text("log content")
        test_file3.write_text('{"json": "content"}')
        test_file4.write_text("csv,content")

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Should process all file types
        assert len(results) == 4

        # Check that extensions are detected
        extensions = [r['extension'] for r in results]
        assert any('.txt' in ext for ext in extensions)
        assert any('.log' in ext for ext in extensions)
        assert any('.json' in ext for ext in extensions)
        assert any('.csv' in ext for ext in extensions)

    def test_process_files_with_empty_files(self, tmp_path):
        """Test processing empty files."""
        # Create empty files
        test_file1 = tmp_path / "empty1.txt"
        test_file2 = tmp_path / "empty2.txt"

        test_file1.write_text("")
        test_file2.write_text("")

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Should process empty files
        assert len(results) == 2
        for result in results:
            assert result['size'] == 0
            assert result['hash'] is not None

        # Empty files with same content should be duplicates
        duplicates = processor.detect_duplicates(results)
        # detect_duplicates returns the same list with duplicate info
        assert len(duplicates) == 2  # Both files returned

        # One should be marked as duplicate
        duplicate_files = [f for f in duplicates if f.get('is_duplicate', False)]
        assert len(duplicate_files) == 1  # One duplicate

    def test_process_files_with_binary_files(self, tmp_path):
        """Test processing binary files."""
        # Create binary files
        test_file1 = tmp_path / "binary1.bin"
        test_file2 = tmp_path / "binary2.bin"

        binary_content1 = bytes(range(256))  # 0-255
        binary_content2 = bytes(range(255, -1, -1))  # 255-0

        test_file1.write_bytes(binary_content1)
        test_file2.write_bytes(binary_content2)

        processor = FileProcessor()
        results = processor.process_files(str(tmp_path))

        # Should process binary files
        assert len(results) == 2
        for result in results:
            assert result['size'] > 0
            assert result['hash'] is not None

        # Different binary content should not be duplicates
        duplicates = processor.detect_duplicates(results)
        # detect_duplicates returns the same list
        assert len(duplicates) == 2  # Both files returned

        # Neither should be marked as duplicate
        duplicate_files = [f for f in duplicates if f.get('is_duplicate', False)]
        assert len(duplicate_files) == 0  # No duplicates
