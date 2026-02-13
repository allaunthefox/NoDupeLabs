"""Tests for compression module."""

import gzip
import bz2
import lzma
import zipfile
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

    def test_create_archive_nonexistent_file(self, temp_dir):
        """Test creating an archive with a non-existent file."""
        nonexistent_file = temp_dir / "nonexistent.txt"
        archive_path = temp_dir / "test.zip"
        
        try:
            Compression.create_archive([nonexistent_file], archive_path, format='zip')
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