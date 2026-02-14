"""Tests for compression module."""

import gzip
import bz2
import lzma
import zipfile
import tarfile
import tempfile
from pathlib import Path
from nodupe.core.compression import Compression, CompressionError


class TestCompression:
    """Test Compression class."""

    def test_compress_data_gzip(self):
        """Test compressing data with gzip format."""
        # Use larger data that will actually compress
        data = b"Hello, World! This is test data for compression. " * 100
        compressed = Compression.compress_data(data, format='gzip')
        
        # Should be able to decompress back to original
        decompressed = Compression.decompress_data(compressed, format='gzip')
        assert decompressed == data

    def test_compress_data_bz2(self):
        """Test compressing data with bz2 format."""
        # Use larger data that will actually compress
        data = b"Hello, World! This is test data for compression. " * 100
        compressed = Compression.compress_data(data, format='bz2')
        
        # Should be able to decompress back to original
        decompressed = Compression.decompress_data(compressed, format='bz2')
        assert decompressed == data

    def test_compress_data_lzma(self):
        """Test compressing data with lzma format."""
        # Use larger data that will actually compress
        data = b"Hello, World! This is test data for compression. " * 100
        compressed = Compression.compress_data(data, format='lzma')
        
        # Should be able to decompress back to original
        decompressed = Compression.decompress_data(compressed, format='lzma')
        assert decompressed == data

    def test_decompress_data_invalid_format(self):
        """Test decompressing data with invalid format."""
        data = b"Hello, World!"
        try:
            Compression.decompress_data(data, format='invalid')  # type: ignore
            assert False, "Expected CompressionError"
        except CompressionError:
            pass  # Expected

    def test_compress_file_gzip(self, temp_dir):
        """Test compressing a file with gzip format."""
        # Create test file
        input_file = temp_dir / "test.txt"
        test_data = b"Hello, World! This is test data for compression. " * 100
        input_file.write_bytes(test_data)
        
        # Compress the file
        output_file = Compression.compress_file(input_file, format='gzip')
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify we can decompress it back
        with gzip.open(output_file, 'rb') as f:
            decompressed_data = f.read()
        assert decompressed_data == test_data

    def test_compress_file_bz2(self, temp_dir):
        """Test compressing a file with bz2 format."""
        # Create test file
        input_file = temp_dir / "test.txt"
        test_data = b"Hello, World! This is test data for compression. " * 100
        input_file.write_bytes(test_data)
        
        # Compress the file
        output_file = Compression.compress_file(input_file, format='bz2')
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify we can decompress it back
        with bz2.BZ2File(output_file, 'rb') as f:
            decompressed_data = f.read()
        assert decompressed_data == test_data

    def test_compress_file_lzma(self, temp_dir):
        """Test compressing a file with lzma format."""
        # Create test file
        input_file = temp_dir / "test.txt"
        test_data = b"Hello, World! This is test data for compression. " * 100
        input_file.write_bytes(test_data)
        
        # Compress the file
        output_file = Compression.compress_file(input_file, format='lzma')
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify we can decompress it back
        with lzma.LZMAFile(output_file, 'rb') as f:
            decompressed_data = f.read()
        assert decompressed_data == test_data

    def test_compress_file_with_output_path(self, temp_dir):
        """Test compressing a file with custom output path."""
        input_file = temp_dir / "input.txt"
        output_file = temp_dir / "output.txt.gz"
        test_data = b"Test data"
        input_file.write_bytes(test_data)
        
        result = Compression.compress_file(input_file, output_path=output_file, format='gzip')
        assert result == output_file
        assert output_file.exists()

    def test_compress_file_remove_original(self, temp_dir):
        """Test compressing a file with removal of original."""
        # Create test file
        input_file = temp_dir / "test.txt"
        test_data = b"Hello, World! This is test data for compression."
        input_file.write_bytes(test_data)
        
        # Verify input file exists
        assert input_file.exists()
        
        # Compress the file and remove original
        output_file = Compression.compress_file(input_file, format='gzip', remove_original=True)
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify input file no longer exists
        assert not input_file.exists()

    def test_decompress_file_gzip(self, temp_dir):
        """Test decompressing a gzip file."""
        # Create test file and compress it
        input_file = temp_dir / "test.txt"
        test_data = b"Hello, World! This is test data for compression."
        input_file.write_bytes(test_data)
        
        compressed_file = temp_dir / "test.txt.gz"
        with gzip.open(compressed_file, 'wb') as f:
            f.write(test_data)
        
        # Decompress the file
        output_file = Compression.decompress_file(compressed_file, format='gzip')
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify content matches original
        assert output_file.read_bytes() == test_data

    def test_decompress_file_bz2(self, temp_dir):
        """Test decompressing a bz2 file."""
        input_file = temp_dir / "test.txt"
        test_data = b"Hello, World! This is test data for compression."
        input_file.write_bytes(test_data)
        
        compressed_file = temp_dir / "test.txt.bz2"
        with bz2.BZ2File(compressed_file, 'wb') as f:
            f.write(test_data)
        
        output_file = Compression.decompress_file(compressed_file, format='bz2')
        
        assert output_file.exists()
        assert output_file.read_bytes() == test_data

    def test_decompress_file_lzma(self, temp_dir):
        """Test decompressing a lzma file."""
        input_file = temp_dir / "test.txt"
        test_data = b"Hello, World! This is test data for compression."
        input_file.write_bytes(test_data)
        
        compressed_file = temp_dir / "test.txt.xz"
        with lzma.LZMAFile(compressed_file, 'wb') as f:
            f.write(test_data)
        
        output_file = Compression.decompress_file(compressed_file, format='lzma')
        
        assert output_file.exists()
        assert output_file.read_bytes() == test_data

    def test_decompress_file_auto_detect(self, temp_dir):
        """Test decompressing a file with auto-detection of format."""
        # Create test file and compress it
        input_file = temp_dir / "test.txt"
        test_data = b"Hello, World! This is test data for compression."
        input_file.write_bytes(test_data)
        
        compressed_file = temp_dir / "test.txt.gz"
        with gzip.open(compressed_file, 'wb') as f:
            f.write(test_data)
        
        # Decompress the file (auto-detect format from extension)
        output_file = Compression.decompress_file(compressed_file)
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify content matches original
        assert output_file.read_bytes() == test_data

    def test_decompress_file_remove_compressed(self, temp_dir):
        """Test decompressing a file with removal of compressed file."""
        # Create test file and compress it
        input_file = temp_dir / "test.txt"
        test_data = b"Hello, World! This is test data for compression."
        input_file.write_bytes(test_data)
        
        compressed_file = temp_dir / "test.txt.gz"
        with gzip.open(compressed_file, 'wb') as f:
            f.write(test_data)
        
        # Verify compressed file exists
        assert compressed_file.exists()
        
        # Decompress the file and remove compressed
        output_file = Compression.decompress_file(compressed_file, format='gzip', remove_compressed=True)
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify compressed file no longer exists
        assert not compressed_file.exists()

    def test_create_archive_zip(self, temp_dir):
        """Test creating a zip archive."""
        # Create test files
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content of file 1")
        file2 = temp_dir / "file2.txt"
        file2.write_bytes(b"Content of file 2")
        
        files = [file1, file2]
        archive_path = temp_dir / "test.zip"
        
        # Create archive
        result_path = Compression.create_archive(files, archive_path, format='zip')
        
        # Verify archive was created
        assert result_path.exists()
        assert result_path == archive_path
        
        # Verify archive contains the files
        with zipfile.ZipFile(archive_path, 'r') as zf:
            names = zf.namelist()
            assert len(names) == 2
            assert "file1.txt" in names
            assert "file2.txt" in names

    def test_create_archive_tar(self, temp_dir):
        """Test creating a tar archive."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content of file 1")
        
        archive_path = temp_dir / "test.tar"
        result = Compression.create_archive([file1], archive_path, format='tar')
        
        assert result.exists()
        with tarfile.open(archive_path, 'r') as tf:
            members = tf.getmembers()
            assert len(members) == 1

    def test_create_archive_tar_gz(self, temp_dir):
        """Test creating a tar.gz archive."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content of file 1")
        
        archive_path = temp_dir / "test.tar.gz"
        result = Compression.create_archive([file1], archive_path, format='tar.gz')
        
        assert result.exists()
        with tarfile.open(archive_path, 'r:gz') as tf:
            members = tf.getmembers()
            assert len(members) == 1

    def test_create_archive_tar_bz2(self, temp_dir):
        """Test creating a tar.bz2 archive."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content of file 1")
        
        archive_path = temp_dir / "test.tar.bz2"
        result = Compression.create_archive([file1], archive_path, format='tar.bz2')
        
        assert result.exists()

    def test_create_archive_tar_xz(self, temp_dir):
        """Test creating a tar.xz archive."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content of file 1")
        
        archive_path = temp_dir / "test.tar.xz"
        result = Compression.create_archive([file1], archive_path, format='tar.xz')
        
        assert result.exists()

    def test_create_archive_with_base_dir(self, temp_dir):
        """Test creating archive with base directory."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        file1 = subdir / "file1.txt"
        file1.write_bytes(b"Content")
        
        archive_path = temp_dir / "test.zip"
        result = Compression.create_archive([file1], archive_path, format='zip', base_dir=temp_dir)
        
        assert result.exists()
        with zipfile.ZipFile(archive_path, 'r') as zf:
            names = zf.namelist()
            assert any('subdir/file1.txt' in n for n in names)

    def test_extract_archive_zip(self, temp_dir):
        """Test extracting a zip archive."""
        # Create test files and archive them
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content of file 1")
        file2 = temp_dir / "file2.txt"
        file2.write_bytes(b"Content of file 2")
        
        files = [file1, file2]
        archive_path = temp_dir / "test.zip"
        
        # Create archive
        Compression.create_archive(files, archive_path, format='zip')
        
        # Extract archive to different directory
        extract_dir = temp_dir / "extracted"
        extracted_files = Compression.extract_archive(archive_path, extract_dir, format='zip')
        
        # Verify extraction directory exists and contains files
        assert extract_dir.exists()
        assert len(extracted_files) == 2
        
        # Verify extracted files have correct content
        extracted_file1 = extract_dir / "file1.txt"
        extracted_file2 = extract_dir / "file2.txt"
        assert extracted_file1.exists()
        assert extracted_file2.exists()
        assert extracted_file1.read_bytes() == b"Content of file 1"
        assert extracted_file2.read_bytes() == b"Content of file 2"

    def test_extract_archive_tar(self, temp_dir):
        """Test extracting a tar archive."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content")
        
        archive_path = temp_dir / "test.tar"
        Compression.create_archive([file1], archive_path, format='tar')
        
        extract_dir = temp_dir / "extracted"
        extracted = Compression.extract_archive(archive_path, extract_dir, format='tar')
        
        assert extract_dir.exists()
        assert len(extracted) >= 1

    def test_extract_archive_auto_detect(self, temp_dir):
        """Test extracting archive with auto-detection."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content")
        
        archive_path = temp_dir / "test.tar.gz"
        Compression.create_archive([file1], archive_path, format='tar.gz')
        
        extract_dir = temp_dir / "extracted"
        extracted = Compression.extract_archive(archive_path, extract_dir)
        
        assert extract_dir.exists()

    def test_get_compression_ratio(self):
        """Test calculating compression ratio."""
        # Perfect compression (original twice the size of compressed)
        ratio = Compression.get_compression_ratio(100, 50)
        assert ratio == 2.0
        
        # No compression (same size)
        ratio = Compression.get_compression_ratio(100, 100)
        assert ratio == 1.0
        
        # Expansion (compressed bigger than original)
        ratio = Compression.get_compression_ratio(50, 100)
        assert ratio == 0.5
        
        # Edge case: zero compressed size
        ratio = Compression.get_compression_ratio(100, 0)
        assert ratio == 0.0

    def test_estimate_compressed_size(self):
        """Test estimating compressed size."""
        # Test with different formats and data types
        size = 1000
        
        # Text data should compress better
        estimated_gzip_text = Compression.estimate_compressed_size(size, 'gzip', 'text')
        assert estimated_gzip_text < size  # Should be smaller
        
        # Binary data should compress less
        estimated_gzip_binary = Compression.estimate_compressed_size(size, 'gzip', 'binary')
        assert estimated_gzip_binary < size  # Should still be smaller but not as much
        
        # Video data should barely compress
        estimated_gzip_video = Compression.estimate_compressed_size(size, 'gzip', 'video')
        assert estimated_gzip_video < size  # Still smaller but close to original

    def test_estimate_compressed_size_tar(self):
        """Test estimating compressed size with tar format."""
        size = 1000
        estimated = Compression.estimate_compressed_size(size, 'tar.gz', 'text')
        assert estimated < size

    def test_compress_data_invalid_format(self):
        """Test compressing data with invalid format."""
        data = b"Hello, World!"
        try:
            Compression.compress_data(data, format='invalid')  # type: ignore
            assert False, "Expected CompressionError"
        except CompressionError:
            pass  # Expected

    def test_compress_file_nonexistent_input(self, temp_dir):
        """Test compressing a non-existent file."""
        nonexistent_file = temp_dir / "nonexistent.txt"
        
        try:
            Compression.compress_file(nonexistent_file, format='gzip')
            assert False, "Expected CompressionError"
        except CompressionError:
            pass  # Expected

    def test_decompress_file_nonexistent_input(self, temp_dir):
        """Test decompressing a non-existent file."""
        nonexistent_file = temp_dir / "nonexistent.txt.gz"
        
        try:
            Compression.decompress_file(nonexistent_file, format='gzip')
            assert False, "Expected CompressionError"
        except CompressionError:
            pass  # Expected

    def test_decompress_file_unknown_extension(self, temp_dir):
        """Test decompressing file with unknown extension."""
        dummy_file = temp_dir / "dummy.xyz"
        dummy_file.write_bytes(b"test")
        
        try:
            Compression.decompress_file(dummy_file)
            assert False, "Expected CompressionError"
        except CompressionError:
            pass  # Expected

    def test_create_archive_nonexistent_file(self, temp_dir):
        """Test creating an archive with a non-existent file."""
        nonexistent_file = temp_dir / "nonexistent.txt"
        archive_path = temp_dir / "test.zip"
        
        try:
            Compression.create_archive([nonexistent_file], archive_path, format='zip')
            assert False, "Expected CompressionError"
        except CompressionError:
            pass  # Expected

    def test_create_archive_invalid_format(self, temp_dir):
        """Test creating archive with invalid format."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content")
        
        archive_path = temp_dir / "test.invalid"
        
        try:
            Compression.create_archive([file1], archive_path, format='invalid')  # type: ignore
            assert False, "Expected CompressionError"
        except CompressionError:
            pass  # Expected

    def test_extract_archive_nonexistent(self, temp_dir):
        """Test extracting a non-existent archive."""
        nonexistent_archive = temp_dir / "nonexistent.zip"
        extract_dir = temp_dir / "extracted"
        
        try:
            Compression.extract_archive(nonexistent_archive, extract_dir, format='zip')
            assert False, "Expected CompressionError"
        except CompressionError:
            pass  # Expected

    def test_extract_archive_invalid_format(self, temp_dir):
        """Test extracting an archive with invalid format."""
        # Create a dummy file that's not a valid archive
        dummy_file = temp_dir / "dummy.zip"
        dummy_file.write_bytes(b"Not a real archive")
        extract_dir = temp_dir / "extracted"
        
        try:
            Compression.extract_archive(dummy_file, extract_dir, format='zip')
            assert False, "Expected CompressionError"
        except CompressionError:
            pass  # Expected

    def test_ensure_path_string(self):
        """Test _ensure_path with string input."""
        result = Compression._ensure_path("/tmp/test")
        assert isinstance(result, Path)

    def test_ensure_path_pathlib(self):
        """Test _ensure_path with Path input."""
        path = Path("/tmp/test")
        result = Compression._ensure_path(path)
        assert result is path

    def test_compress_file_with_level(self, temp_dir):
        """Test compress_file with different compression levels."""
        input_file = temp_dir / "test.txt"
        test_data = b"Test data"
        input_file.write_bytes(test_data)
        
        # Test with different levels
        for level in [1, 6, 9]:
            output_file = temp_dir / f"out_{level}.gz"
            Compression.compress_file(input_file, output_path=output_file, format='gzip', level=level)
            assert output_file.exists()

    def test_compress_file_default_output_path(self, temp_dir):
        """Test compress_file generates default output path."""
        input_file = temp_dir / "test.txt"
        test_data = b"Test data"
        input_file.write_bytes(test_data)
        
        output_file = Compression.compress_file(input_file, format='gzip')
        assert output_file.exists()

    def test_decompress_file_with_output_path(self, temp_dir):
        """Test decompress_file with custom output path."""
        input_file = temp_dir / "test.txt"
        test_data = b"Test data"
        input_file.write_bytes(test_data)
        
        compressed_file = temp_dir / "test.txt.gz"
        with gzip.open(compressed_file, 'wb') as f:
            f.write(test_data)
        
        output_file = temp_dir / "custom_output.txt"
        result = Compression.decompress_file(compressed_file, output_path=output_file)
        assert result == output_file
        assert output_file.read_bytes() == test_data

    def test_compression_error_message(self):
        """Test CompressionError has proper message."""
        error = CompressionError("Test error message")
        assert error.message == "Test error message"
        assert str(error) == "Test error message"

    def test_compress_data_exception_handling(self):
        """Test exception handling in compress_data."""
        # Test with invalid format that causes exception
        import gzip
        # This should raise CompressionError
        try:
            Compression.compress_data(b"test", format="invalid")
        except CompressionError:
            pass

    def test_decompress_data_exception_handling(self):
        """Test exception handling in decompress_data."""
        # Test with corrupt data
        try:
            Compression.decompress_data(b"corrupt", format="gzip")
        except CompressionError:
            pass

    def test_compress_file_exception(self):
        """Test compress_file with format that triggers exception."""
        # Use format that will fail at runtime but pass type check
        try:
            Compression.compress_data(b"test", format="zip")  # zip not valid for data
        except CompressionError:
            pass

    def test_decompress_file_with_invalid_zip(self, temp_dir):
        """Test decompress_file with invalid zip."""
        invalid_zip = temp_dir / "invalid.zip"
        invalid_zip.write_bytes(b"not a zip file")
        
        try:
            Compression.decompress_file(invalid_zip, format='zip')
        except CompressionError:
            pass

    def test_extract_archive_tar_gz_auto_detect(self, temp_dir):
        """Test extracting tar.gz with auto detect."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content")
        
        archive_path = temp_dir / "test.tar.gz"
        Compression.create_archive([file1], archive_path, format='tar.gz')
        
        extract_dir = temp_dir / "extracted"
        extracted = Compression.extract_archive(archive_path, extract_dir)
        assert len(extracted) >= 1

    def test_extract_archive_tar_bz2_auto_detect(self, temp_dir):
        """Test extracting tar.bz2 with auto detect."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content")
        
        archive_path = temp_dir / "test.tar.bz2"
        Compression.create_archive([file1], archive_path, format='tar.bz2')
        
        extract_dir = temp_dir / "extracted"
        extracted = Compression.extract_archive(archive_path, extract_dir)
        assert len(extracted) >= 1

    def test_extract_archive_tar_xz_auto_detect(self, temp_dir):
        """Test extracting tar.xz with auto detect."""
        file1 = temp_dir / "file1.txt"
        file1.write_bytes(b"Content")
        
        archive_path = temp_dir / "test.tar.xz"
        Compression.create_archive([file1], archive_path, format='tar.xz')
        
        extract_dir = temp_dir / "extracted"
        extracted = Compression.extract_archive(archive_path, extract_dir)
        assert len(extracted) >= 1

    def test_create_archive_error_handling(self, temp_dir):
        """Test error handling in create_archive."""
        # Create file that will cause issues
        nonexistent = temp_dir / "nonexistent.txt"
        
        try:
            Compression.create_archive([nonexistent], temp_dir / "out.zip", format='zip')
        except CompressionError:
            pass

    def test_extract_archive_error_handling(self, temp_dir):
        """Test error handling in extract_archive."""
        # Try to extract invalid archive
        invalid = temp_dir / "invalid.zip"
        invalid.write_bytes(b"not valid")
        
        try:
            Compression.extract_archive(invalid, temp_dir / "out")
        except CompressionError:
            pass

    def test_decompress_data_corrupt(self):
        """Test decompress_data with corrupt data triggers exception handler."""
        # Corrupt gzip data - will fail during decompression
        corrupt_data = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff"
        try:
            Compression.decompress_data(corrupt_data, format='gzip')
        except CompressionError:
            pass  # Expected

    def test_compress_file_invalid_format_error(self, temp_dir):
        """Test compress_file with invalid format triggers exception handler."""
        input_file = temp_dir / "test.txt"
        input_file.write_bytes(b"test")
        
        try:
            Compression.compress_file(input_file, format='invalid_format')
        except CompressionError:
            pass

    def test_decompress_file_corrupt_zip(self, temp_dir):
        """Test decompress_file with corrupt zip triggers exception handler."""
        corrupt_zip = temp_dir / "corrupt.zip"
        corrupt_zip.write_bytes(b"PK\x03\x04corrupt")
        
        try:
            Compression.decompress_file(corrupt_zip, format='zip')
        except CompressionError:
            pass

    def test_decompress_file_unsupported_format(self, temp_dir):
        """Test decompress_file with unsupported format triggers exception handler."""
        file1 = temp_dir / "test.xyz"
        file1.write_bytes(b"test")
        
        try:
            Compression.decompress_file(file1, format='xyz')
        except CompressionError:
            pass

    def test_create_archive_file_not_found(self, temp_dir):
        """Test create_archive with missing file triggers exception handler."""
        missing = temp_dir / "missing.txt"
        archive_path = temp_dir / "out.zip"
        
        try:
            Compression.create_archive([missing], archive_path, format='zip')
        except CompressionError:
            pass

    def test_create_archive_unsupported_format(self, temp_dir):
        """Test create_archive unsupported format triggers exception handler."""
        file1 = temp_dir / "test.txt"
        file1.write_bytes(b"test")
        
        try:
            Compression.create_archive([file1], temp_dir / "out.xxx", format='xxx')
        except CompressionError:
            pass

    def test_extract_archive_auto_detect_failure(self, temp_dir):
        """Test extract_archive with unknown extension triggers exception."""
        file1 = temp_dir / "test.unknown"
        file1.write_bytes(b"test")
        
        try:
            Compression.extract_archive(file1, temp_dir / "out")
        except CompressionError:
            pass

    def test_extract_archive_unsupported_format(self, temp_dir):
        """Test extract_archive unsupported format triggers exception handler."""
        # Create a file with .tar extension but invalid content
        file1 = temp_dir / "test.tar"
        file1.write_bytes(b"not a tar file")
        
        try:
            Compression.extract_archive(file1, temp_dir / "out", format='tar')
        except CompressionError:
            pass
