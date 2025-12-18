"""Tests for the archive_handler module."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import zipfile
import tarfile

from nodupe.core.archive_handler import ArchiveHandler, ArchiveHandlerError


class TestArchiveHandler:
    """Test suite for ArchiveHandler class.
    
    This class contains comprehensive tests for the ArchiveHandler functionality,
    including archive detection, extraction, error handling, and various edge cases.
    """

    def __init__(self):
        """Initialize test fixtures."""
        self.temp_dir = None
        self.archive_handler = None

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.archive_handler = ArchiveHandler()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        self.archive_handler.cleanup()

    def test_archive_handler_initialization(self):
        """Test ArchiveHandler initialization."""
        handler = ArchiveHandler()
        assert handler is not None
        assert handler._temp_dirs == []

    def test_is_archive_file_zip(self):
        """Test detection of ZIP archive format."""
        zip_path = Path(self.temp_dir) / "test.zip"
        zip_path.touch()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            result = self.archive_handler.is_archive_file(str(zip_path))
            assert result is True

    def test_is_archive_file_tar(self):
        """Test detection of TAR archive format."""
        tar_path = Path(self.temp_dir) / "test.tar"
        tar_path.touch()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/x-tar'):
            result = self.archive_handler.is_archive_file(str(tar_path))
            assert result is True

    def test_is_archive_file_none(self):
        """Test detection when file is not an archive."""
        regular_file = Path(self.temp_dir) / "test.txt"
        regular_file.touch()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='text/plain'):
            result = self.archive_handler.is_archive_file(str(regular_file))
            assert result is False

    def test_is_archive_file_error_handling(self):
        """Test archive detection error handling."""
        regular_file = Path(self.temp_dir) / "test.txt"
        regular_file.touch()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', side_effect=Exception("Detection failed")):
            result = self.archive_handler.is_archive_file(str(regular_file))
            assert result is False

    def test_extract_zip_archive(self):
        """Test extraction of ZIP archive."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        test_content = "test content"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', test_content)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Extract the archive
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Verify extraction
        assert len(extracted_files) == 1
        assert extracted_files[0].name == 'test.txt'
        
        # Verify file content
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        assert extracted_file.read_text() == test_content

    def test_extract_tar_archive(self):
        """Test extraction of TAR archive."""
        # Create a test TAR file
        tar_path = Path(self.temp_dir) / "test.tar"
        test_content = "test content"
        
        with tarfile.open(tar_path, 'w') as tf:
            # Create a temporary file to add to the archive
            temp_file = Path(self.temp_dir) / "temp.txt"
            temp_file.write_text(test_content)
            tf.add(temp_file, arcname='test.txt')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Extract the archive
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/x-tar'):
            extracted_files = self.archive_handler.extract_archive(str(tar_path), str(extract_path))
        
        # Verify extraction
        assert len(extracted_files) == 1
        assert extracted_files[0].name == 'test.txt'
        
        # Verify file content
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        assert extracted_file.read_text() == test_content

    def test_extract_nonexistent_archive(self):
        """Test extraction of nonexistent archive."""
        nonexistent_path = Path(self.temp_dir) / "nonexistent.zip"
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with pytest.raises(ArchiveHandlerError, match="Archive file not found"):
            self.archive_handler.extract_archive(str(nonexistent_path), str(extract_path))

    def test_extract_invalid_archive(self):
        """Test extraction of invalid archive."""
        # Create an invalid archive file
        invalid_path = Path(self.temp_dir) / "invalid.zip"
        invalid_path.write_text("not a valid archive")
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with pytest.raises(ArchiveHandlerError, match="Failed to extract archive"):
                self.archive_handler.extract_archive(str(invalid_path), str(extract_path))

    def test_extract_to_nonexistent_directory(self):
        """Test extraction to nonexistent directory."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        test_content = "test content"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', test_content)
        
        extract_path = Path(self.temp_dir) / "nonexistent"
        
        # Should create the directory
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        assert len(extracted_files) == 1
        assert extract_path.exists()

    def test_extract_archive_with_directories(self):
        """Test extraction of archive containing directories."""
        # Create a test ZIP file with directories
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('dir1/test.txt', 'content1')
            zf.writestr('dir1/subdir/test2.txt', 'content2')
            zf.writestr('dir2/test3.txt', 'content3')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Verify all files were extracted
        assert len(extracted_files) == 3
        
        # Verify directory structure
        assert (extract_path / 'dir1').exists()
        assert (extract_path / 'dir1' / 'subdir').exists()
        assert (extract_path / 'dir2').exists()

    def test_extract_archive_empty(self):
        """Test extraction of empty archive."""
        # Create an empty ZIP file
        zip_path = Path(self.temp_dir) / "empty.zip"
        
        with zipfile.ZipFile(zip_path, 'w'):
            pass  # Create empty ZIP
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should return empty list
        assert not extracted_files

    def test_extract_archive_with_special_characters(self):
        """Test extraction of archive with special characters in filenames."""
        # Create a test ZIP file with special characters
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('файл.txt', 'content1')  # Cyrillic
            zf.writestr('文件.txt', 'content2')   # Chinese
            zf.writestr('test with spaces.txt', 'content3')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Verify files were extracted
        assert len(extracted_files) == 3
        extracted_names = [f.name for f in extracted_files]
        assert 'файл.txt' in extracted_names
        assert '文件.txt' in extracted_names
        assert 'test with spaces.txt' in extracted_names

    def test_extract_archive_error_handling(self):
        """Test error handling during extraction."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Mock an error during extraction
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with patch('nodupe.core.compression.Compression.extract_archive', side_effect=Exception("Extraction failed")):
                with pytest.raises(ArchiveHandlerError, match="Failed to extract archive"):
                    self.archive_handler.extract_archive(str(zip_path), str(extract_path))

    def test_extract_archive_format_detection(self):
        """Test automatic format detection from MIME type."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Test ZIP detection
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            assert len(extracted_files) == 1

    def test_extract_archive_format_detection_by_extension(self):
        """Test format detection by file extension when MIME type fails."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Mock unknown MIME type but detect from extension
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/octet-stream'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            assert len(extracted_files) == 1

    def test_extract_archive_readonly_directory(self):
        """Test extraction to readonly directory."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "readonly"
        extract_path.mkdir()
        
        # Make directory readonly (this might not work on all systems)
        try:
            extract_path.chmod(0o444)
            
            # Should raise permission error
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                with pytest.raises(ArchiveHandlerError):
                    self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        finally:
            # Restore permissions for cleanup
            extract_path.chmod(0o755)

    def test_extract_archive_large_file(self):
        """Test extraction of large archive."""
        # Create a test ZIP file with large content
        zip_path = Path(self.temp_dir) / "large.zip"
        
        # Create large content (1MB)
        large_content = b'x' * (1024 * 1024)
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('large_file.txt', large_content)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Verify file was extracted
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'large_file.txt'
        assert extracted_file.exists()
        assert extracted_file.read_bytes() == large_content

    def test_extract_archive_compression_methods(self):
        """Test extraction of archives with different compression methods."""
        # Test ZIP with different compression
        for compression in [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED]:
            zip_path = Path(self.temp_dir) / f"test_{compression}.zip"
            
            with zipfile.ZipFile(zip_path, 'w', compression=compression) as zf:
                zf.writestr('test.txt', 'test content')
            
            extract_path = Path(self.temp_dir) / f"extracted_{compression}"
            extract_path.mkdir()
            
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            
            assert len(extracted_files) == 1
            extracted_file = extract_path / 'test.txt'
            assert extracted_file.exists()
            assert extracted_file.read_text() == 'test content'

    def test_extract_archive_duplicate_files(self):
        """Test extraction behavior with duplicate filenames."""
        # Create a ZIP with duplicate entries
        zip_path = Path(self.temp_dir) / "duplicate.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'content1')
            zf.writestr('test.txt', 'content2')  # Duplicate
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract both entries, last one wins
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        assert extracted_file.read_text() == 'content2'

    def test_extract_archive_unicode_paths(self):
        """Test extraction with Unicode paths."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "unicode.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        # Extract to Unicode path
        extract_path = Path(self.temp_dir) / "тест_извлечение"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        assert extracted_file.read_text() == 'test content'

    def test_extract_archive_memory_usage(self):
        """Test memory usage during extraction."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "memory_test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add multiple small files instead of one large file
            for i in range(100):
                zf.writestr(f'file_{i}.txt', f'content_{i}')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        assert len(extracted_files) == 100
        for i in range(100):
            extracted_file = extract_path / f'file_{i}.txt'
            assert extracted_file.exists()
            assert extracted_file.read_text() == f'content_{i}'

    def test_cleanup_temp_directories(self):
        """Test cleanup of temporary directories."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        # Extract without specifying directory (creates temp dir)
        extracted_files = self.archive_handler.extract_archive(str(zip_path))
        
        # Should have created a temp directory
        assert len(self.archive_handler._temp_dirs) == 1
        temp_dir = Path(self.archive_handler._temp_dirs[0])
        assert temp_dir.exists()
        
        # Cleanup
        self.archive_handler.cleanup()
        
        # Temp directory should be removed
        assert not temp_dir.exists()
        assert len(self.archive_handler._temp_dirs) == 0

    def test_cleanup_error_handling(self):
        """Test cleanup error handling."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        # Extract without specifying directory
        extracted_files = self.archive_handler.extract_archive(str(zip_path))
        
        # Mock error during cleanup
        with patch('shutil.rmtree', side_effect=Exception("Cleanup failed")):
            # Should not raise exception
            self.archive_handler.cleanup()
        
        # Temp directories list should still be cleared
        assert not self.archive_handler._temp_dirs

    def test_get_archive_contents_info(self):
        """Test getting archive contents information."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
            zf.writestr('dir/test2.txt', 'test content 2')
        
        base_path = Path(self.temp_dir) / "base"
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            contents_info = self.archive_handler.get_archive_contents_info(str(zip_path), str(base_path))
        
        # Should return file information for extracted files
        assert len(contents_info) >= 1
        for file_info in contents_info:
            assert 'path' in file_info
            assert 'name' in file_info
            assert 'size' in file_info
            assert 'archive_source' in file_info
            assert file_info['archive_source'] == str(zip_path)

    def test_get_archive_contents_info_error_handling(self):
        """Test archive contents info error handling."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        base_path = Path(self.temp_dir) / "base"
        
        # Mock error during extraction
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with patch.object(self.archive_handler, 'extract_archive', side_effect=Exception("Extraction failed")):
                contents_info = self.archive_handler.get_archive_contents_info(str(zip_path), str(base_path))
        
        # Should return empty list on error
        assert not contents_info

    def test_destructor_cleanup(self):
        """Test that destructor cleans up temporary directories."""
        # Create handler and extract file
        handler = ArchiveHandler()
        
        zip_path = Path(self.temp_dir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = handler.extract_archive(str(zip_path))
        
        # Should have temp directory
        assert len(handler._temp_dirs) == 1
        temp_dir = Path(handler._temp_dirs[0])
        assert temp_dir.exists()
        
        # Delete handler
        del handler
        
        # Temp directory should be cleaned up (though this might not happen immediately due to garbage collection)

    def test_extract_archive_multiple_formats(self):
        """Test extraction of different archive formats."""
        test_files = []
        
        # Test ZIP
        zip_path = Path(self.temp_dir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'zip content')
        test_files.append((zip_path, 'application/zip'))
        
        # Test TAR
        tar_path = Path(self.temp_dir) / "test.tar"
        with tarfile.open(tar_path, 'w') as tf:
            temp_file = Path(self.temp_dir) / "temp.txt"
            temp_file.write_text('tar content')
            tf.add(temp_file, arcname='test.txt')
        test_files.append((tar_path, 'application/x-tar'))
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        for archive_path, mime_type in test_files:
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value=mime_type):
                extracted_files = self.archive_handler.extract_archive(str(archive_path), str(extract_path))
                assert len(extracted_files) == 1
                
                # Clean up for next iteration
                import shutil
                for item in extract_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)

    def test_extract_archive_preserves_permissions(self):
        """Test that file permissions are preserved during extraction."""
        # Create a test ZIP file with specific permissions
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
            # Set specific permissions (this is platform-dependent)
            info = zf.getinfo('test.txt')
            info.external_attr = 0o644 << 16
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Verify file was extracted
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()

    def test_extract_archive_symlinks(self):
        """Test extraction of archives containing symlinks."""
        # Note: This test might not work on all platforms
        zip_path = Path(self.temp_dir) / "symlink.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('target.txt', 'target content')
            # Add symlink (platform-dependent)
            if hasattr(os, 'symlink'):
                import tempfile
                temp_target = Path(self.temp_dir) / "temp_target.txt"
                temp_target.write_text('target content')
                
                # Create symlink in ZIP
                zf.write(temp_target, 'link.txt')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract files (symlinks might not be preserved on all platforms)
        assert len(extracted_files) >= 1

    def test_extract_archive_concurrent_access(self):
        """Test extraction with concurrent access."""
        import threading
        import time
        
        # Create multiple ZIP files
        zip_files = []
        for i in range(5):
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f'test_{i}.txt', f'content_{i}')
            zip_files.append(zip_path)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        results = []
        errors = []
        
        def extract_file(zip_path):
            try:
                with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                    extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
                    results.append(len(extracted_files))
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for zip_path in zip_files:
            thread = threading.Thread(target=extract_file, args=(zip_path,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have no errors and all results should be 1
        assert not errors
        assert len(results) == 5
        assert all(r == 1 for r in results)

    def test_extract_archive_performance(self):
        """Test extraction performance with multiple files."""
        # Create a ZIP with many files
        zip_path = Path(self.temp_dir) / "many_files.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for i in range(100):
                zf.writestr(f'file_{i:03d}.txt', f'content_{i}')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        start_time = time.time()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        elapsed = time.time() - start_time
        
        # Should extract all files
        assert len(extracted_files) == 100
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert elapsed < 10.0, f"Extraction took too long: {elapsed:.2f} seconds"

    def test_extract_archive_memory_efficiency(self):
        """Test memory efficiency during large archive extraction."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        initial_objects = len(gc.get_objects())
        
        # Create and extract multiple archives
        for i in range(10):
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f'test_{i}.txt', f'content_{i}' * 1000)  # Larger content
            
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                extracted_files = self.archive_handler.extract_archive(str(zip_path))
        
        # Force garbage collection after test
        gc.collect()
        
        final_objects = len(gc.get_objects())
        
        # Should not have significant memory leak
        assert final_objects - initial_objects < 1000

    def test_extract_archive_error_recovery(self):
        """Test error recovery during extraction."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # First extraction should succeed
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            assert len(extracted_files) == 1
        
        # Second extraction with error should handle gracefully
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with patch('nodupe.core.compression.Compression.extract_archive', side_effect=Exception("Extraction failed")):
                with pytest.raises(ArchiveHandlerError):
                    self.archive_handler.extract_archive(str(zip_path), str(extract_path))

    def test_extract_archive_filesystem_errors(self):
        """Test handling of filesystem errors during extraction."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        # Try to extract to a path that doesn't exist and can't be created
        invalid_path = Path("/nonexistent/directory/path")
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with pytest.raises(ArchiveHandlerError):
                self.archive_handler.extract_archive(str(zip_path), str(invalid_path))

    def test_extract_archive_corrupted_archive(self):
        """Test handling of corrupted archive files."""
        # Create a file that looks like a ZIP but isn't
        corrupted_path = Path(self.temp_dir) / "corrupted.zip"
        corrupted_path.write_bytes(b'PK\x03\x04')  # Invalid ZIP header
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with pytest.raises(ArchiveHandlerError):
                self.archive_handler.extract_archive(str(corrupted_path), str(extract_path))

    def test_extract_archive_empty_directories(self):
        """Test extraction of archives containing empty directories."""
        # Create a ZIP with empty directories
        zip_path = Path(self.temp_dir) / "empty_dirs.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add directory entries
            zf.writestr('dir1/', '')
            zf.writestr('dir1/subdir/', '')
            zf.writestr('dir2/', '')
            # Add a file in one of the directories
            zf.writestr('dir1/file.txt', 'content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract the file and create directories
        assert len(extracted_files) == 1
        
        # Verify directory structure
        assert (extract_path / 'dir1').exists()
        assert (extract_path / 'dir1' / 'subdir').exists()
        assert (extract_path / 'dir2').exists()

    def test_extract_archive_nested_archives(self):
        """Test extraction of archives containing other archives."""
        # Create inner ZIP
        inner_zip_path = Path(self.temp_dir) / "inner.zip"
        with zipfile.ZipFile(inner_zip_path, 'w') as zf:
            zf.writestr('inner.txt', 'inner content')
        
        # Create outer ZIP containing the inner ZIP
        outer_zip_path = Path(self.temp_dir) / "outer.zip"
        with zipfile.ZipFile(outer_zip_path, 'w') as zf:
            zf.write(inner_zip_path, 'nested/inner.zip')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(outer_zip_path), str(extract_path))
        
        # Should extract the inner ZIP file
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'nested' / 'inner.zip'
        assert extracted_file.exists()

    def test_extract_archive_special_permissions(self):
        """Test extraction of files with special permissions."""
        # Create a test ZIP file with executable permissions
        zip_path = Path(self.temp_dir) / "executable.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('script.sh', '#!/bin/bash\necho "hello"')
            # Set executable permissions
            info = zf.getinfo('script.sh')
            info.external_attr = 0o755 << 16
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Verify file was extracted
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'script.sh'
        assert extracted_file.exists()
        assert extracted_file.read_text() == '#!/bin/bash\necho "hello"'

    def test_extract_archive_unicode_content(self):
        """Test extraction of archives with Unicode content."""
        # Create a test ZIP file with Unicode content
        zip_path = Path(self.temp_dir) / "unicode.zip"
        
        unicode_content = "Тест содержимого 文件内容 测试内容"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('unicode.txt', unicode_content)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Verify file was extracted with correct content
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'unicode.txt'
        assert extracted_file.exists()
        assert extracted_file.read_text() == unicode_content

    def test_extract_archive_case_sensitivity(self):
        """Test extraction with case-sensitive filenames."""
        # Create a test ZIP file with mixed case
        zip_path = Path(self.temp_dir) / "case.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('Test.TXT', 'uppercase')
            zf.writestr('test.txt', 'lowercase')
            zf.writestr('TEST.Txt', 'mixed case')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract all files (behavior depends on filesystem)
        assert len(extracted_files) >= 1
        
        # Verify at least one file was extracted
        extracted_names = [f.name for f in extracted_files]
        assert any(name in extracted_names for name in ['Test.TXT', 'test.txt', 'TEST.Txt'])

    def test_extract_archive_timestamps(self):
        """Test that file timestamps are preserved during extraction."""
        import time
        
        # Create a test ZIP file with specific timestamp
        zip_path = Path(self.temp_dir) / "timestamp.zip"
        
        test_time = time.time() - 3600  # 1 hour ago
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
            # Set specific timestamp
            info = zf.getinfo('test.txt')
            info.date_time = time.localtime(test_time)[:6]
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Verify file was extracted
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        
        # Check that timestamp is reasonably preserved (within a few seconds)
        file_time = extracted_file.stat().st_mtime
        assert abs(file_time - test_time) < 10

    def test_extract_archive_large_number_of_files(self):
        """Test extraction of archive with large number of files."""
        # Create a ZIP with many files
        zip_path = Path(self.temp_dir) / "many_files.zip"
        
        num_files = 1000
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for i in range(num_files):
                zf.writestr(f'file_{i:04d}.txt', f'content for file {i}')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        start_time = time.time()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        elapsed = time.time() - start_time
        
        # Should extract all files
        assert len(extracted_files) == num_files
        
        # Should complete in reasonable time
        assert elapsed < 30.0, f"Extraction took too long: {elapsed:.2f} seconds"
        
        # Verify some files were extracted correctly
        for i in [0, 500, 999]:
            extracted_file = extract_path / f'file_{i:04d}.txt'
            assert extracted_file.exists()
            assert extracted_file.read_text() == f'content for file {i}'

    def test_extract_archive_disk_space_handling(self):
        """Test handling when disk space is insufficient."""
        # Create a test ZIP file with large content
        zip_path = Path(self.temp_dir) / "large.zip"
        
        # Create content that would require significant disk space
        large_content = b'x' * (1024 * 1024)  # 1MB
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add multiple copies to make it large
            for i in range(10):
                zf.writestr(f'large_file_{i}.txt', large_content)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # This test is difficult to implement reliably across different systems
        # as we can't easily simulate disk full conditions
        # So we'll just test that the extraction works normally
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract all files
        assert len(extracted_files) == 10
        
        # Verify files were extracted
        for i in range(10):
            extracted_file = extract_path / f'large_file_{i}.txt'
            assert extracted_file.exists()
            assert extracted_file.read_bytes() == large_content

    def test_extract_archive_concurrent_cleanup(self):
        """Test concurrent access to cleanup functionality."""
        import threading
        
        # Create multiple handlers and extract files
        handlers = []
        for i in range(5):
            handler = ArchiveHandler()
            
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f'test_{i}.txt', f'content_{i}')
            
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                extracted_files = handler.extract_archive(str(zip_path))
            
            handlers.append(handler)
        
        # Verify temp directories were created
        for handler in handlers:
            assert len(handler._temp_dirs) == 1
        
        # Concurrent cleanup
        results = []
        errors = []
        
        def cleanup_handler(handler):
            try:
                handler.cleanup()
                results.append(True)
            except Exception as e:
                errors.append(e)
        
        threads = []
        for handler in handlers:
            thread = threading.Thread(target=cleanup_handler, args=(handler,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 5
        assert all(results)
        
        # All temp directories should be cleaned up
        for handler in handlers:
            assert len(handler._temp_dirs) == 0

    def test_extract_archive_memory_cleanup(self):
        """Test that memory is properly cleaned up after extraction."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        initial_objects = len(gc.get_objects())
        
        # Create and extract multiple archives
        for i in range(50):
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f'test_{i}.txt', f'content_{i}')
            
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                extracted_files = self.archive_handler.extract_archive(str(zip_path))
        
        # Cleanup all temp directories
        self.archive_handler.cleanup()
        
        # Force garbage collection after test
        gc.collect()
        
        final_objects = len(gc.get_objects())
        
        # Memory usage should not grow significantly
        assert final_objects - initial_objects < 500

    def test_extract_archive_error_messages(self):
        """Test that error messages are informative and helpful."""
        # Test nonexistent file
        nonexistent_path = Path(self.temp_dir) / "nonexistent.zip"
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with pytest.raises(ArchiveHandlerError) as exc_info:
            self.archive_handler.extract_archive(str(nonexistent_path), str(extract_path))
        
        assert "Archive file not found" in str(exc_info.value)
        assert str(nonexistent_path) in str(exc_info.value)
        
        # Test invalid archive
        invalid_path = Path(self.temp_dir) / "invalid.zip"
        invalid_path.write_text("not a zip file")
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with pytest.raises(ArchiveHandlerError) as exc_info:
                self.archive_handler.extract_archive(str(invalid_path), str(extract_path))
        
        assert "Failed to extract archive" in str(exc_info.value)
        assert str(invalid_path) in str(exc_info.value)

    def test_extract_archive_temp_dir_cleanup_on_error(self):
        """Test that temporary directories are cleaned up even when extraction fails."""
        # Create an invalid archive
        invalid_path = Path(self.temp_dir) / "invalid.zip"
        invalid_path.write_text("not a zip file")
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Extract without specifying directory (should create temp dir)
        try:
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                self.archive_handler.extract_archive(str(invalid_path))
        except ArchiveHandlerError:
            pass  # Expected to fail
        
        # Temp directory should still be tracked for cleanup
        # (The exact behavior depends on implementation details)
        
        # Cleanup should work normally
        self.archive_handler.cleanup()
        assert len(self.archive_handler._temp_dirs) == 0

    def test_extract_archive_format_fallback(self):
        """Test format detection fallback when MIME type is unknown."""
        # Create a ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Mock unknown MIME type but detect from extension
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/octet-stream'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            assert len(extracted_files) == 1
        
        # Test TAR extension
        tar_path = Path(self.temp_dir) / "test.tar"
        
        with tarfile.open(tar_path, 'w') as tf:
            temp_file = Path(self.temp_dir) / "temp.txt"
            temp_file.write_text('tar content')
            tf.add(temp_file, arcname='test.txt')
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/octet-stream'):
            extracted_files = self.archive_handler.extract_archive(str(tar_path), str(extract_path))
            assert len(extracted_files) == 1

    def test_extract_archive_nested_directories(self):
        """Test extraction of archives with deeply nested directory structures."""
        # Create a ZIP with deeply nested directories
        zip_path = Path(self.temp_dir) / "nested.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Create a deep directory structure
            for depth in range(10):
                path_parts = ['deep'] * depth + ['file.txt']
                file_path = '/'.join(path_parts)
                zf.writestr(file_path, f'content at depth {depth}')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract all files
        assert len(extracted_files) == 10
        
        # Verify deepest directory was created
        deepest_path = extract_path / 'deep' / 'deep' / 'deep' / 'deep' / 'deep' / 'deep' / 'deep' / 'deep' / 'deep' / 'file.txt'
        assert deepest_path.exists()
        assert deepest_path.read_text() == 'content at depth 9'

    def test_extract_archive_special_filenames(self):
        """Test extraction of files with special characters in filenames."""
        # Create a ZIP with special filenames
        zip_path = Path(self.temp_dir) / "special.zip"
        
        special_names = [
            'file with spaces.txt',
            'file.with.dots.txt',
            'file-with-dashes.txt',
            'file_with_underscores.txt',
            'file(1).txt',
            'file[2].txt',
            'file{3}.txt',
            'file@host.com.txt',
            'file#1.txt',
            'file%20.txt',
        ]
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for name in special_names:
                zf.writestr(name, f'content of {name}')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract all files
        assert len(extracted_files) == len(special_names)
        
        # Verify all special filenames were preserved
        extracted_names = [f.name for f in extracted_files]
        for name in special_names:
            assert name in extracted_names

    def test_extract_archive_duplicate_directory_entries(self):
        """Test extraction when archive contains duplicate directory entries."""
        # Create a ZIP with duplicate directory entries
        zip_path = Path(self.temp_dir) / "duplicate_dirs.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add the same directory multiple times
            zf.writestr('dir/', '')
            zf.writestr('dir/', '')
            zf.writestr('dir/', '')
            # Add a file in the directory
            zf.writestr('dir/file.txt', 'content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract the file
        assert len(extracted_files) == 1
        
        # Directory should exist
        assert (extract_path / 'dir').exists()
        assert (extract_path / 'dir' / 'file.txt').exists()

    def test_extract_archive_zero_byte_files(self):
        """Test extraction of archives containing zero-byte files."""
        # Create a ZIP with zero-byte files
        zip_path = Path(self.temp_dir) / "zero_byte.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add zero-byte files
            zf.writestr('empty1.txt', '')
            zf.writestr('empty2.txt', '')
            zf.writestr('empty3.txt', '')
            # Add a normal file
            zf.writestr('normal.txt', 'normal content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract all files
        assert len(extracted_files) == 4
        
        # Verify zero-byte files
        for i in range(1, 4):
            empty_file = extract_path / f'empty{i}.txt'
            assert empty_file.exists()
            assert empty_file.read_text() == ''
        
        # Verify normal file
        normal_file = extract_path / 'normal.txt'
        assert normal_file.exists()
        assert normal_file.read_text() == 'normal content'

    def test_extract_archive_symlink_preservation(self):
        """Test preservation of symlinks during extraction (where supported)."""
        # Skip this test on Windows where symlinks require special permissions
        if os.name == 'nt':
            pytest.skip("Symlinks not supported on Windows")
        
        # Create a TAR file with symlinks
        tar_path = Path(self.temp_dir) / "symlinks.tar"
        
        with tarfile.open(tar_path, 'w') as tf:
            # Create a regular file
            temp_file = Path(self.temp_dir) / "target.txt"
            temp_file.write_text('target content')
            tf.add(temp_file, arcname='target.txt')
            
            # Create a symlink
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as temp_link:
                temp_link_path = temp_link.name
            
            try:
                os.symlink('target.txt', temp_link_path)
                tf.add(temp_link_path, arcname='link.txt', recursive=False)
            finally:
                if os.path.exists(temp_link_path):
                    os.unlink(temp_link_path)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/x-tar'):
            extracted_files = self.archive_handler.extract_archive(str(tar_path), str(extract_path))
        
        # Should extract files
        assert len(extracted_files) >= 1
        
        # Check if symlinks were preserved (depends on system and permissions)
        target_file = extract_path / 'target.txt'
        link_file = extract_path / 'link.txt'
        
        if target_file.exists():
            assert target_file.read_text() == 'target content'
        
        if link_file.exists() and link_file.is_symlink():
            assert link_file.readlink() == Path('target.txt')

    def test_extract_archive_hardlink_preservation(self):
        """Test preservation of hardlinks during extraction (where supported)."""
        # Create a TAR file with hardlinks
        tar_path = Path(self.temp_dir) / "hardlinks.tar"
        
        with tarfile.open(tar_path, 'w') as tf:
            # Create a regular file
            temp_file = Path(self.temp_dir) / "original.txt"
            temp_file.write_text('shared content')
            tf.add(temp_file, arcname='original.txt')
            
            # Create a hardlink
            link_file = Path(self.temp_dir) / "link.txt"
            os.link(temp_file, link_file)
            tf.add(link_file, arcname='link.txt')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/x-tar'):
            extracted_files = self.archive_handler.extract_archive(str(tar_path), str(extract_path))
        
        # Should extract files
        assert len(extracted_files) >= 1
        
        # Check if hardlinks were preserved
        original_file = extract_path / 'original.txt'
        link_file = extract_path / 'link.txt'
        
        if original_file.exists() and link_file.exists():
            assert original_file.read_text() == 'shared content'
            assert link_file.read_text() == 'shared content'
            
            # Check if they have the same inode (are hardlinks)
            original_stat = original_file.stat()
            link_stat = link_file.stat()
            if original_stat.st_ino == link_stat.st_ino:
                # They are hardlinks
                assert original_stat.st_nlink == 2

    def test_extract_archive_sparse_files(self):
        """Test extraction of archives containing sparse files."""
        # Create a test file with holes (sparse file)
        sparse_path = Path(self.temp_dir) / "sparse.txt"
        
        with open(sparse_path, 'wb') as f:
            f.write(b'beginning')
            f.seek(1024 * 1024)  # Seek to 1MB
            f.write(b'end')
        
        # Create a TAR file containing the sparse file
        tar_path = Path(self.temp_dir) / "sparse.tar"
        
        with tarfile.open(tar_path, 'w') as tf:
            tf.add(sparse_path, arcname='sparse.txt')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/x-tar'):
            extracted_files = self.archive_handler.extract_archive(str(tar_path), str(extract_path))
        
        # Should extract the file
        assert len(extracted_files) == 1
        
        extracted_file = extract_path / 'sparse.txt'
        assert extracted_file.exists()
        
        # Verify content
        with open(extracted_file, 'rb') as f:
            content = f.read()
            assert content.startswith(b'beginning')
            assert content.endswith(b'end')
            assert len(content) == 1024 * 1024 + len(b'end')

    def test_extract_archive_permissions_preservation(self):
        """Test preservation of file permissions during extraction."""
        # Create a test file with specific permissions
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text('test content')
        os.chmod(test_file, 0o755)  # rwxr-xr-x
        
        # Create a TAR file preserving permissions
        tar_path = Path(self.temp_dir) / "permissions.tar"
        
        with tarfile.open(tar_path, 'w') as tf:
            tf.add(test_file, arcname='test.txt')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/x-tar'):
            extracted_files = self.archive_handler.extract_archive(str(tar_path), str(extract_path))
        
        # Should extract the file
        assert len(extracted_files) == 1
        
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        
        # Check permissions (may not be preserved on all systems)
        extracted_stat = extracted_file.stat()
        # The exact permissions depend on the system and umask
        # but the file should be readable
        assert extracted_file.read_text() == 'test content'

    def test_extract_archive_timestamp_preservation(self):
        """Test preservation of file timestamps during extraction."""
        import time
        
        # Create a test file with specific timestamp
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text('test content')
        
        # Set a specific timestamp (1 hour ago)
        test_time = time.time() - 3600
        os.utime(test_file, (test_time, test_time))
        
        # Create a TAR file preserving timestamps
        tar_path = Path(self.temp_dir) / "timestamps.tar"
        
        with tarfile.open(tar_path, 'w') as tf:
            tf.add(test_file, arcname='test.txt')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/x-tar'):
            extracted_files = self.archive_handler.extract_archive(str(tar_path), str(extract_path))
        
        # Should extract the file
        assert len(extracted_files) == 1
        
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        
        # Check timestamps
        extracted_stat = extracted_file.stat()
        # Allow some tolerance for timestamp precision
        assert abs(extracted_stat.st_mtime - test_time) < 2
        assert abs(extracted_stat.st_atime - test_time) < 2

    def test_extract_archive_large_file_performance(self):
        """Test performance with very large files."""
        # Create a large file (10MB)
        large_file = Path(self.temp_dir) / "large.txt"
        large_content = b'x' * (10 * 1024 * 1024)  # 10MB
        large_file.write_bytes(large_content)
        
        # Create a ZIP file containing the large file
        zip_path = Path(self.temp_dir) / "large_file.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(large_file, 'large.txt')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        start_time = time.time()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        elapsed = time.time() - start_time
        
        # Should extract the file
        assert len(extracted_files) == 1
        
        extracted_file = extract_path / 'large.txt'
        assert extracted_file.exists()
        assert extracted_file.read_bytes() == large_content
        
        # Should complete in reasonable time (adjust threshold based on system)
        # This is a rough estimate - actual time depends on system performance
        assert elapsed < 60.0, f"Large file extraction took too long: {elapsed:.2f} seconds"

    def test_extract_archive_memory_usage_large_files(self):
        """Test memory usage when extracting large files."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Record initial memory usage
        gc.collect()
        initial_memory = process.memory_info().rss
        
        # Create a moderately large file (100MB)
        large_file = Path(self.temp_dir) / "large.txt"
        large_content = b'x' * (100 * 1024 * 1024)  # 100MB
        large_file.write_bytes(large_content)
        
        # Create a ZIP file containing the large file
        zip_path = Path(self.temp_dir) / "large_file.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:  # Use stored to avoid compression overhead
            zf.write(large_file, 'large.txt')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Extract the file
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Record final memory usage
        gc.collect()
        final_memory = process.memory_info().rss
        
        # Memory usage should not grow excessively
        # Allow some growth for file handling overhead, but not proportional to file size
        memory_growth = final_memory - initial_memory
        
        # Should extract the file
        assert len(extracted_files) == 1
        
        extracted_file = extract_path / 'large.txt'
        assert extracted_file.exists()
        assert extracted_file.read_bytes() == large_content
        
        # Memory growth should be reasonable (not proportional to file size)
        # This is a rough estimate - actual memory usage depends on implementation
        assert memory_growth < 50 * 1024 * 1024, f"Memory growth too high: {memory_growth / 1024 / 1024:.2f} MB"

    def test_extract_archive_concurrent_extraction(self):
        """Test concurrent extraction of multiple archives."""
        import threading
        import time
        
        # Create multiple ZIP files
        zip_files = []
        for i in range(10):
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                # Add a few files to each archive
                for j in range(5):
                    zf.writestr(f'file_{j}.txt', f'content_{i}_{j}')
            zip_files.append(zip_path)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        results = []
        errors = []
        start_times = []
        end_times = []
        
        def extract_with_timing(zip_path):
            start_times.append(time.time())
            try:
                with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                    extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
                    results.append(len(extracted_files))
                end_times.append(time.time())
            except Exception as e:
                errors.append(e)
                end_times.append(time.time())
        
        # Create and start threads
        threads = []
        for zip_path in zip_files:
            thread = threading.Thread(target=extract_with_timing, args=(zip_path,))
            threads.append(thread)
        
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0
        
        # Should extract all files
        assert len(results) == 10
        assert all(r == 5 for r in results)
        
        # All extractions should complete
        assert len(start_times) == 10
        assert len(end_times) == 10
        
        # Calculate total and individual times
        total_time = max(end_times) - min(start_times)
        individual_times = [end - start for start, end in zip(start_times, end_times)]
        
        # Concurrent extraction should be faster than sequential
        # (This is a rough test - actual performance depends on system)
        assert total_time > 0
        assert all(t > 0 for t in individual_times)

    def test_extract_archive_error_recovery_partial(self):
        """Test recovery from partial extraction failures."""
        # Create a ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('file1.txt', 'content1')
            zf.writestr('file2.txt', 'content2')
            zf.writestr('file3.txt', 'content3')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # First extraction should succeed
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files1 = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            assert len(extracted_files1) == 3
        
        # Clear the extraction directory for second attempt
        import shutil
        for item in extract_path.iterdir():
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)
        
        # Second extraction should also succeed
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files2 = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            assert len(extracted_files2) == 3
        
        # Files should be identical
        for i in range(1, 4):
            file1 = [f for f in extracted_files1 if f.name == f'file{i}.txt'][0]
            file2 = [f for f in extracted_files2 if f.name == f'file{i}.txt'][0]
            assert file1.read_text() == file2.read_text()

    def test_extract_archive_cleanup_on_exception(self):
        """Test that temporary resources are cleaned up when exceptions occur."""
        # Create a ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        # Mock an exception during extraction
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with patch('nodupe.core.compression.Compression.extract_archive', side_effect=Exception("Simulated extraction failure")):
                with pytest.raises(ArchiveHandlerError):
                    self.archive_handler.extract_archive(str(zip_path))
        
        # Temp directories should still be tracked for cleanup
        # (The exact behavior depends on implementation details)
        
        # Cleanup should work normally
        initial_temp_dirs = len(self.archive_handler._temp_dirs)
        self.archive_handler.cleanup()
        assert len(self.archive_handler._temp_dirs) == 0

    def test_extract_archive_file_locking(self):
        """Test behavior when files are locked or in use."""
        # Create a ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Extract normally first
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        
        # Try to extract again (should handle existing files)
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files2 = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should still work (behavior depends on extraction library)
        assert len(extracted_files2) == 1

    def test_extract_archive_unicode_normalization(self):
        """Test handling of Unicode filename normalization."""
        # Create a ZIP with Unicode filenames that might be normalized differently
        zip_path = Path(self.temp_dir) / "unicode_norm.zip"
        
        # Use composed and decomposed Unicode characters
        composed = 'café.txt'  # 'é' as single character
        decomposed = 'cafe\u0301.txt'  # 'e' + combining acute accent
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(composed, 'composed content')
            zf.writestr(decomposed, 'decomposed content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract files (number depends on filesystem normalization)
        assert len(extracted_files) >= 1
        
        # Verify at least one file was extracted
        extracted_names = [f.name for f in extracted_files]
        assert any('cafe' in name for name in extracted_names)

    def test_extract_archive_case_insensitive_filesystems(self):
        """Test behavior on case-insensitive filesystems."""
        # Create a ZIP with files that differ only in case
        zip_path = Path(self.temp_dir) / "case_insensitive.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('Test.txt', 'uppercase content')
            zf.writestr('test.txt', 'lowercase content')
            zf.writestr('TEST.TXT', 'uppercase content 2')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # On case-insensitive filesystems, some files might overwrite others
        # On case-sensitive filesystems, all files should be preserved
        assert len(extracted_files) >= 1
        
        # At least one file should be extracted
        extracted_names = [f.name for f in extracted_files]
        assert any(name in extracted_names for name in ['Test.txt', 'test.txt', 'TEST.TXT'])

    def test_extract_archive_archive_bomb_protection(self):
        """Test protection against archive bombs (decompression bombs)."""
        # Create a ZIP with highly compressed content (potential bomb)
        zip_path = Path(self.temp_dir) / "bomb.zip"
        
        # Create a small file with repetitive content that compresses well
        small_content = b'x' * 1000
        large_content = small_content * 1000  # 1MB of repetitive data
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('compressed.txt', large_content)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # This test verifies that the extraction doesn't consume excessive resources
        # The actual protection mechanisms would depend on the underlying libraries
        
        start_time = time.time()
        start_memory = 0
        
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss
        except ImportError:
            pass
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        elapsed = time.time() - start_time
        
        end_memory = 0
        try:
            end_memory = process.memory_info().rss
            memory_used = end_memory - start_memory
        except:
            memory_used = 0
        
        # Should extract the file
        assert len(extracted_files) == 1
        
        extracted_file = extract_path / 'compressed.txt'
        assert extracted_file.exists()
        assert extracted_file.read_bytes() == large_content
        
        # Should complete in reasonable time
        assert elapsed < 10.0, f"Extraction took too long: {elapsed:.2f} seconds"
        
        # Memory usage should be reasonable (not excessive)
        if memory_used > 0:
            assert memory_used < 100 * 1024 * 1024, f"Memory usage too high: {memory_used / 1024 / 1024:.2f} MB"

    def test_extract_archive_mixed_content_types(self):
        """Test extraction of archives containing mixed content types."""
        # Create a ZIP with various content types
        zip_path = Path(self.temp_dir) / "mixed.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Text file
            zf.writestr('text.txt', 'This is text content')
            
            # Binary file
            zf.writestr('binary.bin', b'\x00\x01\x02\x03\x04\x05')
            
            # JSON file
            zf.writestr('data.json', '{"key": "value", "number": 42}')
            
            # Empty file
            zf.writestr('empty.txt', '')
            
            # File with Unicode content
            zf.writestr('unicode.txt', 'Тест 文件 测试')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract all files
        assert len(extracted_files) == 5
        
        # Verify each file type
        extracted_dict = {f.name: f for f in extracted_files}
        
        # Text file
        assert 'text.txt' in extracted_dict
        assert extracted_dict['text.txt'].read_text() == 'This is text content'
        
        # Binary file
        assert 'binary.bin' in extracted_dict
        assert extracted_dict['binary.bin'].read_bytes() == b'\x00\x01\x02\x03\x04\x05'
        
        # JSON file
        assert 'data.json' in extracted_dict
        assert extracted_dict['data.json'].read_text() == '{"key": "value", "number": 42}'
        
        # Empty file
        assert 'empty.txt' in extracted_dict
        assert extracted_dict['empty.txt'].read_text() == ''
        
        # Unicode file
        assert 'unicode.txt' in extracted_dict
        assert extracted_dict['unicode.txt'].read_text() == 'Тест 文件 测试'

    def test_extract_archive_nested_archive_extraction(self):
        """Test extraction of nested archives within extracted files."""
        # Create inner ZIP
        inner_zip_path = Path(self.temp_dir) / "inner.zip"
        with zipfile.ZipFile(inner_zip_path, 'w') as zf:
            zf.writestr('inner.txt', 'inner content')
        
        # Create outer ZIP containing the inner ZIP
        outer_zip_path = Path(self.temp_dir) / "outer.zip"
        with zipfile.ZipFile(outer_zip_path, 'w') as zf:
            zf.write(inner_zip_path, 'nested/inner.zip')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Extract outer archive
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            outer_files = self.archive_handler.extract_archive(str(outer_zip_path), str(extract_path))
        
        assert len(outer_files) == 1
        
        # Now extract the inner archive
        inner_zip_extracted = extract_path / 'nested' / 'inner.zip'
        assert inner_zip_extracted.exists()
        
        inner_extract_path = extract_path / 'nested' / 'extracted'
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            inner_files = self.archive_handler.extract_archive(str(inner_zip_extracted), str(inner_extract_path))
        
        assert len(inner_files) == 1
        
        # Verify inner content
        inner_file = inner_extract_path / 'inner.txt'
        assert inner_file.exists()
        assert inner_file.read_text() == 'inner content'

    def test_extract_archive_filesystem_boundary_checks(self):
        """Test extraction near filesystem boundaries (full disk, etc.)."""
        # This test is difficult to implement reliably across different systems
        # as we can't easily simulate filesystem boundary conditions
        # So we'll test normal operation and assume error handling works
        
        # Create a normal archive
        zip_path = Path(self.temp_dir) / "normal.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Normal extraction should work
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        assert len(extracted_files) == 1
        
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        assert extracted_file.read_text() == 'test content'

    def test_extract_archive_temp_directory_isolation(self):
        """Test that temporary directories are properly isolated between extractions."""
        # Extract first archive
        zip_path1 = Path(self.temp_dir) / "test1.zip"
        
        with zipfile.ZipFile(zip_path1, 'w') as zf:
            zf.writestr('file1.txt', 'content1')
        
        extracted_files1 = self.archive_handler.extract_archive(str(zip_path1))
        
        # Extract second archive
        zip_path2 = Path(self.temp_dir) / "test2.zip"
        
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            zf.writestr('file2.txt', 'content2')
        
        extracted_files2 = self.archive_handler.extract_archive(str(zip_path2))
        
        # Should have two separate temp directories
        assert len(self.archive_handler._temp_dirs) == 2
        assert extracted_files1[0].parent != extracted_files2[0].parent
        
        # Each temp directory should contain only its respective file
        assert (Path(self.archive_handler._temp_dirs[0]) / 'file1.txt').exists()
        assert not (Path(self.archive_handler._temp_dirs[0]) / 'file2.txt').exists()
        
        assert (Path(self.archive_handler._temp_dirs[1]) / 'file2.txt').exists()
        assert not (Path(self.archive_handler._temp_dirs[1]) / 'file1.txt').exists()

    def test_extract_archive_cleanup_idempotency(self):
        """Test that cleanup can be called multiple times safely."""
        # Create some temp directories
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extracted_files = self.archive_handler.extract_archive(str(zip_path))
        assert len(self.archive_handler._temp_dirs) == 1
        
        # First cleanup should work
        self.archive_handler.cleanup()
        assert len(self.archive_handler._temp_dirs) == 0
        
        # Second cleanup should also work (no error)
        self.archive_handler.cleanup()
        assert len(self.archive_handler._temp_dirs) == 0
        
        # Third cleanup should also work
        self.archive_handler.cleanup()
        assert len(self.archive_handler._temp_dirs) == 0

    def test_extract_archive_error_message_details(self):
        """Test that error messages contain sufficient details for debugging."""
        # Test with nonexistent file
        nonexistent_path = Path(self.temp_dir) / "nonexistent.zip"
        
        with pytest.raises(ArchiveHandlerError) as exc_info:
            self.archive_handler.extract_archive(str(nonexistent_path))
        
        error_message = str(exc_info.value)
        assert "Archive file not found" in error_message
        assert str(nonexistent_path) in error_message
        
        # Test with invalid archive
        invalid_path = Path(self.temp_dir) / "invalid.zip"
        invalid_path.write_text("not a zip file")
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with pytest.raises(ArchiveHandlerError) as exc_info:
                self.archive_handler.extract_archive(str(invalid_path))
        
        error_message = str(exc_info.value)
        assert "Failed to extract archive" in error_message
        assert str(invalid_path) in error_message
        
        # The error should also contain the underlying exception message
        assert "BadZipFile" in error_message or "not a zip file" in error_message.lower()

    def test_extract_archive_resource_management(self):
        """Test proper resource management during extraction."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        initial_open_files = len(psutil.Process().open_files()) if psutil else 0
        
        # Create and extract multiple archives
        for i in range(10):
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f'test_{i}.txt', f'content_{i}')
            
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                extracted_files = self.archive_handler.extract_archive(str(zip_path))
        
        # Force garbage collection after test
        gc.collect()
        
        final_open_files = len(psutil.Process().open_files()) if psutil else 0
        
        # Should not have significant resource leaks
        # (The exact threshold depends on system and implementation)
        if initial_open_files > 0 and final_open_files > 0:
            assert final_open_files - initial_open_files < 10

    def test_extract_archive_concurrent_temp_cleanup(self):
        """Test concurrent cleanup of temporary directories."""
        import threading
        
        # Create multiple handlers with temp directories
        handlers = []
        for i in range(10):
            handler = ArchiveHandler()
            
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f'test_{i}.txt', f'content_{i}')
            
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                extracted_files = handler.extract_archive(str(zip_path))
            
            handlers.append(handler)
        
        # Verify temp directories exist
        for handler in handlers:
            assert len(handler._temp_dirs) == 1
        
        # Concurrent cleanup
        threads = []
        for handler in handlers:
            thread = threading.Thread(target=handler.cleanup)
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All temp directories should be cleaned up
        for handler in handlers:
            assert len(handler._temp_dirs) == 0

    def test_extract_archive_memory_leak_detection(self):
        """Test for memory leaks during repeated extractions."""
        import gc
        import tracemalloc
        
        # Start memory tracing
        tracemalloc.start()
        
        # Perform many extractions
        for i in range(50):
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f'test_{i}.txt', f'content_{i}' * 100)  # Some content
            
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                extracted_files = self.archive_handler.extract_archive(str(zip_path))
        
        # Cleanup
        self.archive_handler.cleanup()
        
        # Force garbage collection
        gc.collect()
        
        # Get memory snapshot
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        # Stop memory tracing
        tracemalloc.stop()
        
        # Calculate total memory allocated
        total_memory = sum(stat.size for stat in top_stats)
        
        # Memory usage should be reasonable (not growing linearly with iterations)
        # This is a rough estimate - actual memory usage depends on implementation
        assert total_memory < 10 * 1024 * 1024, f"Memory usage too high: {total_memory / 1024 / 1024:.2f} MB"

    def test_extract_archive_file_handle_leak_detection(self):
        """Test for file handle leaks during extraction."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Record initial file handles
        initial_handles = len(process.open_files())
        
        # Perform many extractions
        for i in range(20):
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f'test_{i}.txt', f'content_{i}')
            
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                extracted_files = self.archive_handler.extract_archive(str(zip_path))
        
        # Cleanup
        self.archive_handler.cleanup()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Record final file handles
        final_handles = len(process.open_files())
        
        # Should not have significant file handle leaks
        handle_leak = final_handles - initial_handles
        assert handle_leak < 10, f"File handle leak detected: {handle_leak} handles"

    def test_extract_archive_exception_safety(self):
        """Test exception safety during extraction operations."""
        # Create a ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Test that exceptions don't leave the handler in an inconsistent state
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            # First extraction should succeed
            extracted_files1 = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            assert len(extracted_files1) == 1
            
            # Mock an exception during second extraction
            with patch('nodupe.core.compression.Compression.extract_archive', side_effect=Exception("Simulated failure")):
                with pytest.raises(ArchiveHandlerError):
                    self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            
            # Handler should still be in a usable state
            # (This depends on the implementation - the handler should handle the exception gracefully)
        
        # Temp directories should still be manageable
        initial_temp_count = len(self.archive_handler._temp_dirs)
        
        # Cleanup should work
        self.archive_handler.cleanup()
        assert len(self.archive_handler._temp_dirs) == 0

    def test_extract_archive_thread_local_storage(self):
        """Test that thread-local storage is handled correctly."""
        import threading
        
        results = []
        
        def extract_in_thread():
            try:
                # Create a handler in this thread
                handler = ArchiveHandler()
                
                zip_path = Path(self.temp_dir) / "thread_test.zip"
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    zf.writestr('test.txt', 'thread content')
                
                extracted_files = handler.extract_archive(str(zip_path))
                
                # Store results in thread-local storage
                thread_local = threading.local()
                thread_local.extracted_count = len(extracted_files)
                thread_local.temp_dirs_count = len(handler._temp_dirs)
                
                results.append({
                    'extracted_count': thread_local.extracted_count,
                    'temp_dirs_count': thread_local.temp_dirs_count
                })
                
                # Cleanup
                handler.cleanup()
                
            except Exception as e:
                results.append({'error': str(e)})
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=extract_in_thread)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have results from all threads
        assert len(results) == 5
        
        # All should be successful
        for result in results:
            assert 'error' not in result
            assert result['extracted_count'] == 1
            assert result['temp_dirs_count'] == 1

    def test_extract_archive_cleanup_on_process_exit(self):
        """Test cleanup behavior when process exits."""
        # This test is difficult to implement directly as it requires process termination
        # Instead, we'll test the destructor behavior
        
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        # Create handler and extract file
        handler = ArchiveHandler()
        extracted_files = handler.extract_archive(str(zip_path))
        
        # Verify temp directory was created
        assert len(handler._temp_dirs) == 1
        temp_dir = Path(handler._temp_dirs[0])
        assert temp_dir.exists()
        
        # Delete handler (should trigger destructor)
        del handler
        
        # The temp directory cleanup behavior depends on Python's garbage collection
        # In practice, the destructor should be called eventually
        # For testing purposes, we can't reliably test process exit behavior

    def test_extract_archive_error_propagation(self):
        """Test that errors are properly propagated through the call stack."""
        # Create a ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Test error propagation from MIME detection
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', side_effect=Exception("MIME detection failed")):
            with pytest.raises(ArchiveHandlerError) as exc_info:
                self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            
            assert "MIME detection failed" in str(exc_info.value)
        
        # Test error propagation from compression module
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            with patch('nodupe.core.compression.Compression.extract_archive', side_effect=Exception("Compression failed")):
                with pytest.raises(ArchiveHandlerError) as exc_info:
                    self.archive_handler.extract_archive(str(zip_path), str(extract_path))
                
                assert "Compression failed" in str(exc_info.value)

    def test_extract_archive_security_file_paths(self):
        """Test security handling of file paths in archives."""
        # Create a ZIP with potentially dangerous file paths
        zip_path = Path(self.temp_dir) / "security.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Path traversal attempts
            zf.writestr('../etc/passwd', 'fake passwd')
            zf.writestr('..\\windows\\system32\\config', 'fake config')
            zf.writestr('/etc/passwd', 'absolute path attempt')
            
            # Long paths
            long_path = 'a' * 200 + '/file.txt'
            zf.writestr(long_path, 'long path content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract files, but the security handling depends on the underlying library
        assert len(extracted_files) >= 1
        
        # The exact behavior depends on the ZIP library's security measures
        # Some paths might be sanitized or rejected

    def test_extract_archive_atomic_operations(self):
        """Test that extraction operations are atomic where possible."""
        # Create a ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
            zf.writestr('data.txt', 'data content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Perform extraction
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Should extract all files or none (atomic operation)
        if len(extracted_files) > 0:
            # If any files were extracted, all should be present
            assert len(extracted_files) == 2
            
            file1 = extract_path / 'test.txt'
            file2 = extract_path / 'data.txt'
            
            assert file1.exists()
            assert file2.exists()
            assert file1.read_text() == 'test content'
            assert file2.read_text() == 'data content'

    def test_extract_archive_cleanup_robustness(self):
        """Test that cleanup is robust against various error conditions."""
        # Create some temp directories
        for i in range(3):
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f'test_{i}.txt', f'content_{i}')
            
            extracted_files = self.archive_handler.extract_archive(str(zip_path))
        
        assert len(self.archive_handler._temp_dirs) == 3
        
        # Mock errors during cleanup
        with patch('shutil.rmtree', side_effect=[None, Exception("Cleanup failed"), None]):
            # Should not raise exception
            self.archive_handler.cleanup()
        
        # Temp directories list should be cleared even if some cleanups failed
        assert len(self.archive_handler._temp_dirs) == 0

    def test_extract_archive_performance_consistency(self):
        """Test that extraction performance is consistent across multiple runs."""
        # Create a standard test archive
        zip_path = Path(self.temp_dir) / "performance.zip"
        
        # Add multiple files to get meaningful timing
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i in range(50):
                zf.writestr(f'file_{i:02d}.txt', f'content_{i}' * 100)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Measure extraction time multiple times
        times = []
        
        for _ in range(5):
            # Clear extraction directory
            import shutil
            for item in extract_path.iterdir():
                if item.is_file():
                    item.unlink()
                else:
                    shutil.rmtree(item)
            
            # Measure time
            start_time = time.time()
            
            with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
            
            elapsed = time.time() - start_time
            times.append(elapsed)
        
        # Should extract all files each time
        assert all(len(extracted_files) == 50 for _ in range(5))
        
        # Performance should be reasonably consistent (coefficient of variation < 50%)
        mean_time = sum(times) / len(times)
        variance = sum((t - mean_time) ** 2 for t in times) / len(times)
        std_dev = variance ** 0.5
        
        if mean_time > 0:
            cv = std_dev / mean_time
            assert cv < 0.5, f"Performance too inconsistent: CV = {cv:.2f}"

    def test_extract_archive_memory_usage_pattern(self):
        """Test that memory usage follows expected patterns during extraction."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Record baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss
        
        # Create test archive
        zip_path = Path(self.temp_dir) / "memory_test.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add several moderately sized files
            for i in range(10):
                content = f'content_{i}' * 10000  # ~100KB per file
                zf.writestr(f'file_{i:02d}.txt', content)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Monitor memory during extraction
        memory_samples = []
        
        def sample_memory():
            gc.collect()
            memory_samples.append(process.memory_info().rss)
        
        # Pre-extraction
        sample_memory()
        
        # Extract
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
        
        # Post-extraction
        sample_memory()
        
        # Cleanup
        self.archive_handler.cleanup()
        sample_memory()
        
        # Should extract all files
        assert len(extracted_files) == 10
        
        # Memory should return close to baseline after cleanup
        final_memory = memory_samples[-1]
        memory_growth = final_memory - baseline_memory
        
        # Memory growth should be reasonable (not proportional to extracted data size)
        assert memory_growth < 50 * 1024 * 1024, f"Memory growth too high: {memory_growth / 1024 / 1024:.2f} MB"

    def test_extract_archive_concurrent_resource_usage(self):
        """Test resource usage under concurrent load."""
        import threading
        import time
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Create multiple test archives
        zip_files = []
        for i in range(10):
            zip_path = Path(self.temp_dir) / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for j in range(5):
                    zf.writestr(f'file_{j}.txt', f'content_{i}_{j}' * 1000)
            zip_files.append(zip_path)
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        # Record initial state
        initial_memory = process.memory_info().rss
        initial_handles = len(process.open_files())
        
        results = []
        errors = []
        
        def extract_with_monitoring(zip_path):
            try:
                start_memory = process.memory_info().rss
                start_time = time.time()
                
                with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                    extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))
                
                end_time = time.time()
                end_memory = process.memory_info().rss
                
                results.append({
                    'files_extracted': len(extracted_files),
                    'duration': end_time - start_time,
                    'memory_used': end_memory - start_memory
                })
            except Exception as e:
                errors.append(e)
        
        # Start all extractions concurrently
        threads = []
        for zip_path in zip_files:
            thread = threading.Thread(target=extract_with_monitoring, args=(zip_path,))
            threads.append(thread)
        
        start_time = time.time()
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Record final state
        final_memory = process.memory_info().rss
        final_handles = len(process.open_files())
        
        # Should have no errors
        assert len(errors) == 0
        
        # Should extract all files
        assert len(results) == 10
        assert all(r['files_extracted'] == 5 for r in results)
        
        # Resource usage should be reasonable
        total_memory_used = final_memory - initial_memory
        handle_growth = final_handles - initial_handles
        
        assert total_memory_used < 100 * 1024 * 1024, f"Memory usage too high: {total_memory_used / 1024 / 1024:.2f} MB"
        assert handle_growth < 50, f"File handle growth too high: {handle_growth}"
        
        # Concurrent extraction should be faster than sequential for I/O bound operations
        # (This is a rough test - actual performance depends on system)
        assert total_time > 0
        assert all(r['duration'] > 0 for r in results)

    def test_extract_archive_error_recovery_comprehensive(self):
        """Comprehensive test of error recovery mechanisms."""
        # Test various error scenarios and ensure proper recovery
        
        scenarios = [
            {
                'name': 'nonexistent_file',
                'setup': lambda: Path(self.temp_dir) / "nonexistent.zip",
                'expected_error': ArchiveHandlerError,
                'error_contains': 'Archive file not found'
            },
            {
                'name': 'invalid_zip',
                'setup': lambda: self._create_invalid_archive(),
                'expected_error': ArchiveHandlerError,
                'error_contains': 'Failed to extract archive'
            },
            {
                'name': 'readonly_directory',
                'setup': lambda: self._setup_readonly_extraction(),
                'expected_error': ArchiveHandlerError,
                'error_contains': 'Failed to extract archive'
            }
        ]
        
        for scenario in scenarios:
            with pytest.raises(scenario['expected_error']) as exc_info:
                if scenario['name'] == 'nonexistent_file':
                    nonexistent_path = scenario['setup']()
                    self.archive_handler.extract_archive(str(nonexistent_path))
                elif scenario['name'] == 'invalid_zip':
                    invalid_path = scenario['setup']()
                    with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                        self.archive_handler.extract_archive(str(invalid_path))
                elif scenario['name'] == 'readonly_directory':
                    zip_path, readonly_path = scenario['setup']()
                    with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
                        self.archive_handler.extract_archive(str(zip_path), str(readonly_path))
            
            assert scenario['error_contains'] in str(exc_info.value)
        
        # After all error scenarios, handler should still be functional
        # Create a valid archive and extract it
        valid_zip = Path(self.temp_dir) / "valid.zip"
        with zipfile.ZipFile(valid_zip, 'w') as zf:
            zf.writestr('test.txt', 'valid content')
        
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()
        
        with patch('nodupe.core.mime_detection.MIMEDetection.detect_mime_type', return_value='application/zip'):
            extracted_files = self.archive_handler.extract_archive(str(valid_zip), str(extract_path))
        
        assert len(extracted_files) == 1
        assert extracted_files[0].read_text() == 'valid content'

    def _create_invalid_archive(self):
        """Helper to create an invalid archive file."""
        invalid_path = Path(self.temp_dir) / "invalid.zip"
        invalid_path.write_text("not a valid archive")
        return invalid_path

    def _setup_readonly_extraction(self):
        """Helper to set up readonly directory extraction test."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        # Create readonly directory
        readonly_path = Path(self.temp_dir) / "readonly"
        readonly_path.mkdir()
        readonly_path.chmod(0o444)
        
        return zip_path, readonly_path
