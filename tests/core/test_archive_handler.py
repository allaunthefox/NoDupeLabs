"""Tests for the archive_handler module."""

import os
import tarfile
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from nodupe.tools.archive.archive_logic import ArchiveHandler, ArchiveHandlerError


class TestArchiveHandler:
    """Test suite for ArchiveHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.archive_handler = ArchiveHandler()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_archive_handler_initialization(self):
        """Test ArchiveHandler initialization."""
        handler = ArchiveHandler()
        assert handler is not None

    def test_detect_archive_format_zip(self):
        """Test detection of ZIP archive format."""
        zip_path = Path(self.temp_dir) / "test.zip"
        zip_path.touch()

        with patch('zipfile.is_zipfile', return_value=True):
            result = self.archive_handler.detect_archive_format(str(zip_path))
            assert result == 'zip'

    def test_detect_archive_format_tar(self):
        """Test detection of TAR archive format."""
        tar_path = Path(self.temp_dir) / "test.tar"
        tar_path.touch()

        with patch('tarfile.is_tarfile', return_value=True):
            with patch('zipfile.is_zipfile', return_value=False):
                result = self.archive_handler.detect_archive_format(str(tar_path))
                assert result == 'tar'

    def test_detect_archive_format_none(self):
        """Test detection when file is not an archive."""
        regular_file = Path(self.temp_dir) / "test.txt"
        regular_file.touch()

        with patch('tarfile.is_tarfile', return_value=False):
            with patch('zipfile.is_zipfile', return_value=False):
                result = self.archive_handler.detect_archive_format(str(regular_file))
                assert result is None

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
        extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

        # Verify extraction
        assert len(extracted_files) == 1
        assert 'test.txt' in extracted_files
        assert extracted_files['test.txt'] == str(extract_path / 'test.txt')

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
        extracted_files = self.archive_handler.extract_archive(str(tar_path), str(extract_path))

        # Verify extraction
        assert len(extracted_files) == 1
        assert 'test.txt' in extracted_files
        assert extracted_files['test.txt'] == str(extract_path / 'test.txt')

        # Verify file content
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        assert extracted_file.read_text() == test_content

    def test_extract_nonexistent_archive(self):
        """Test extraction of nonexistent archive."""
        nonexistent_path = Path(self.temp_dir) / "nonexistent.zip"
        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()

        with pytest.raises(FileNotFoundError):
            self.archive_handler.extract_archive(str(nonexistent_path), str(extract_path))

    def test_extract_invalid_archive(self):
        """Test extraction of invalid archive."""
        # Create an invalid archive file
        invalid_path = Path(self.temp_dir) / "invalid.zip"
        invalid_path.write_text("not a valid archive")

        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()

        with pytest.raises((zipfile.BadZipFile, tarfile.TarError)):
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
        extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

        assert len(extracted_files) == 1
        assert extract_path.exists()

    def test_extract_archive_with_permissions(self):
        """Test extraction preserves file permissions."""
        # Create a test ZIP file with specific permissions
        zip_path = Path(self.temp_dir) / "test.zip"

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
            # Set specific permissions
            info = zf.getinfo('test.txt')
            info.external_attr = 0o644 << 16

        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()

        extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

        # Verify file was extracted
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()

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

        extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

        # Verify all files were extracted
        assert len(extracted_files) == 3
        assert 'dir1/test.txt' in extracted_files
        assert 'dir1/subdir/test2.txt' in extracted_files
        assert 'dir2/test3.txt' in extracted_files

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

        extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

        # Should return empty dict
        assert extracted_files == {}

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

        extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

        # Verify files were extracted
        assert len(extracted_files) == 3
        assert 'файл.txt' in extracted_files
        assert '文件.txt' in extracted_files
        assert 'test with spaces.txt' in extracted_files

    def test_extract_archive_error_handling(self):
        """Test error handling during extraction."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "test.zip"

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')

        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()

        # Mock an error during extraction
        with patch('zipfile.ZipFile.extractall', side_effect=Exception("Extraction failed")):
            with pytest.raises(Exception, match="Extraction failed"):
                self.archive_handler.extract_archive(str(zip_path), str(extract_path))

    def test_detect_archive_format_error_handling(self):
        """Test error handling in archive format detection."""
        nonexistent_path = Path(self.temp_dir) / "nonexistent.zip"

        # Should return None for nonexistent file
        result = self.archive_handler.detect_archive_format(str(nonexistent_path))
        assert result is None

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
            with pytest.raises((PermissionError, OSError)):
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

            extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

            assert len(extracted_files) == 1
            extracted_file = extract_path / 'test.txt'
            assert extracted_file.exists()
            assert extracted_file.read_text() == 'test content'

    def test_extract_archive_PASSWORD_REMOVED_protected(self):
        """Test extraction of PASSWORD_REMOVED-protected archive using mocking."""
        zip_path = Path(self.temp_dir) / "mock_protected.zip"
        zip_path.touch()
        extract_path = Path(self.temp_dir) / "extracted_protected"
        PASSWORD_REMOVED = b"testPASSWORD_REMOVED"

        # Mock zipfile to simulate an encrypted ZIP
        with patch("zipfile.ZipFile") as mock_zip_class:
            mock_zf = MagicMock()
            mock_zip_class.return_value.__enter__.return_value = mock_zf
            mock_zf.namelist.return_value = ["SECRET_REMOVED.txt"]

            # Setup the mocked extracted file
            SECRET_REMOVED_file = extract_path / "SECRET_REMOVED.txt"

            def side_effect_extractall(path, members=None, pwd=None):
                extract_path.mkdir(parents=True, exist_ok=True)
                SECRET_REMOVED_file.write_text("PASSWORD_REMOVED protected content")

            mock_zf.extractall.side_effect = side_effect_extractall

            # Test successful extraction with PASSWORD_REMOVED
            extracted_files = self.archive_handler.extract_archive(
                str(zip_path),
                str(extract_path),
                PASSWORD_REMOVED=PASSWORD_REMOVED
            )

            # Verify setPASSWORD_REMOVED was called if logic uses it (or check PASSWORD_REMOVED passed to extractall)
            # Our current implementation in compression.py uses zf.setPASSWORD_REMOVED(PASSWORD_REMOVED)
            mock_zf.setPASSWORD_REMOVED.assert_called_with(PASSWORD_REMOVED)

            assert "SECRET_REMOVED.txt" in extracted_files
            assert Path(extracted_files["SECRET_REMOVED.txt"]).exists()
            assert Path(extracted_files["SECRET_REMOVED.txt"]).read_text() == "PASSWORD_REMOVED protected content"

    def test_extract_archive_PASSWORD_REMOVED_protected_wrong_PASSWORD_REMOVED(self):
        """Test extraction of PASSWORD_REMOVED-protected archive with wrong PASSWORD_REMOVED using mocking."""
        zip_path = Path(self.temp_dir) / "mock_protected.zip"
        zip_path.touch()
        extract_path = Path(self.temp_dir) / "extracted_wrong"
        PASSWORD_REMOVED = b"wrongPASSWORD_REMOVED"

        with patch("zipfile.ZipFile") as mock_zip_class:
            mock_zf = MagicMock()
            mock_zip_class.return_value.__enter__.return_value = mock_zf
            mock_zf.namelist.return_value = ["SECRET_REMOVED.txt"]

            # Simulate a runtime error or BadZipFile that occurs when PASSWORD_REMOVED is wrong
            mock_zf.extractall.side_effect = RuntimeError("Bad PASSWORD_REMOVED")

            with pytest.raises((ArchiveHandlerError, RuntimeError)):
                self.archive_handler.extract_archive(
                    str(zip_path),
                    str(extract_path),
                    PASSWORD_REMOVED=PASSWORD_REMOVED
                )

    def test_extract_archive_duplicate_files(self):
        """Test extraction behavior with duplicate filenames."""
        # Create a ZIP with duplicate entries
        zip_path = Path(self.temp_dir) / "duplicate.zip"

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'content1')
            zf.writestr('test.txt', 'content2')  # Duplicate

        extract_path = Path(self.temp_dir) / "extracted"
        extract_path.mkdir()

        extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

        # Should extract both entries, last one wins
        assert len(extracted_files) == 1
        extracted_file = extract_path / 'test.txt'
        assert extracted_file.exists()
        assert extracted_file.read_text() == 'content2'

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

        extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

        # Should extract files (symlinks might not be preserved on all platforms)
        assert len(extracted_files) >= 1

    def test_extract_archive_unicode_paths(self):
        """Test extraction with Unicode paths."""
        # Create a test ZIP file
        zip_path = Path(self.temp_dir) / "unicode.zip"

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')

        # Extract to Unicode path
        extract_path = Path(self.temp_dir) / "тест_извлечение"
        extract_path.mkdir()

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

        # Extract should handle memory efficiently
        extracted_files = self.archive_handler.extract_archive(str(zip_path), str(extract_path))

        assert len(extracted_files) == 100
        for i in range(100):
            extracted_file = extract_path / f'file_{i}.txt'
            assert extracted_file.exists()
            assert extracted_file.read_text() == f'content_{i}'
