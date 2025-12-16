"""Tests for compression module."""

import pytest
import tempfile
from pathlib import Path
from nodupe.core.compression import Compression, CompressionError


class TestCompression:
    """Test Compression class."""

    def test_compress_data_gzip(self):
        """Test gzip compression."""
        data = b"Hello, World!" * 100
        compressed = Compression.compress_data(data, format='gzip', level=6)
        assert isinstance(compressed, bytes)
        assert len(compressed) < len(data)

    def test_compress_data_bz2(self):
        """Test bz2 compression."""
        data = b"Hello, World!" * 100
        compressed = Compression.compress_data(data, format='bz2', level=6)
        assert isinstance(compressed, bytes)
        assert len(compressed) < len(data)

    def test_compress_data_lzma(self):
        """Test lzma compression."""
        data = b"Hello, World!" * 100
        compressed = Compression.compress_data(data, format='lzma', level=6)
        assert isinstance(compressed, bytes)
        assert len(compressed) < len(data)

    def test_compress_data_invalid_format(self):
        """Test compression with invalid format."""
        with pytest.raises(CompressionError):
            Compression.compress_data(b"data", format='invalid')  # type: ignore

    def test_decompress_data_gzip(self):
        """Test gzip decompression."""
        data = b"Hello, World!" * 100
        compressed = Compression.compress_data(data, format='gzip')
        decompressed = Compression.decompress_data(compressed, format='gzip')
        assert decompressed == data

    def test_decompress_data_bz2(self):
        """Test bz2 decompression."""
        data = b"Hello, World!" * 100
        compressed = Compression.compress_data(data, format='bz2')
        decompressed = Compression.decompress_data(compressed, format='bz2')
        assert decompressed == data

    def test_decompress_data_lzma(self):
        """Test lzma decompression."""
        data = b"Hello, World!" * 100
        compressed = Compression.compress_data(data, format='lzma')
        decompressed = Compression.decompress_data(compressed, format='lzma')
        assert decompressed == data

    def test_decompress_data_invalid(self):
        """Test decompression with invalid data."""
        with pytest.raises(CompressionError):
            Compression.decompress_data(b"invalid compressed data", format='gzip')

    def test_compress_file(self, tmp_path):
        """Test file compression."""
        # Create test file
        input_file = tmp_path / "test.txt"
        input_file.write_text("Hello, World!" * 100)

        # Compress file
        output_file = Compression.compress_file(
            input_file,
            format='gzip'
        )

        assert output_file.exists()
        assert output_file.stat().st_size < input_file.stat().st_size

    def test_compress_file_with_output_path(self, tmp_path):
        """Test file compression with custom output path."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("Hello, World!" * 100)
        output_file = tmp_path / "compressed.gz"

        result = Compression.compress_file(
            input_file,
            output_path=output_file,
            format='gzip'
        )

        assert result == output_file
        assert output_file.exists()

    def test_compress_file_remove_original(self, tmp_path):
        """Test file compression with original removal."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("Hello, World!" * 100)

        Compression.compress_file(
            input_file,
            format='gzip',
            remove_original=True
        )

        assert not input_file.exists()

    def test_compress_file_nonexistent(self, tmp_path):
        """Test compression of nonexistent file."""
        with pytest.raises(CompressionError):
            Compression.compress_file(tmp_path / "nonexistent.txt")

    def test_decompress_file(self, tmp_path):
        """Test file decompression."""
        # Create and compress file
        input_file = tmp_path / "test.txt"
        original_data = "Hello, World!" * 100
        input_file.write_text(original_data)

        compressed_file = Compression.compress_file(input_file, format='gzip')

        # Decompress
        decompressed_file = Compression.decompress_file(compressed_file)

        assert decompressed_file.exists()
        assert decompressed_file.read_text() == original_data

    def test_decompress_file_auto_detect(self, tmp_path):
        """Test file decompression with auto-detect."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("Hello, World!" * 100)

        # Compress with .gz extension
        compressed = tmp_path / "test.txt.gz"
        Compression.compress_file(input_file, output_path=compressed, format='gzip')

        # Decompress without specifying format
        decompressed = Compression.decompress_file(compressed, format=None)
        assert decompressed.exists()

    def test_create_archive_zip(self, tmp_path):
        """Test ZIP archive creation."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("File 1")
        file2.write_text("File 2")

        # Create archive
        archive = tmp_path / "archive.zip"
        result = Compression.create_archive(
            [file1, file2],
            archive,
            format='zip'
        )

        assert result == archive
        assert archive.exists()

    def test_create_archive_tar_gz(self, tmp_path):
        """Test tar.gz archive creation."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("File 1")

        archive = tmp_path / "archive.tar.gz"
        Compression.create_archive([file1], archive, format='tar.gz')

        assert archive.exists()

    def test_extract_archive_zip(self, tmp_path):
        """Test ZIP archive extraction."""
        # Create archive
        file1 = tmp_path / "file1.txt"
        file1.write_text("File 1 content")

        archive = tmp_path / "archive.zip"
        Compression.create_archive([file1], archive, format='zip')

        # Extract to new directory
        extract_dir = tmp_path / "extracted"
        extracted_files = Compression.extract_archive(archive, extract_dir)

        assert len(extracted_files) > 0
        assert extract_dir.exists()

    def test_extract_archive_tar_gz(self, tmp_path):
        """Test tar.gz archive extraction."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("File 1")

        archive = tmp_path / "archive.tar.gz"
        Compression.create_archive([file1], archive, format='tar.gz')

        extract_dir = tmp_path / "extracted"
        Compression.extract_archive(archive, extract_dir)

        assert extract_dir.exists()

    def test_get_compression_ratio(self):
        """Test compression ratio calculation."""
        ratio = Compression.get_compression_ratio(1000, 500)
        assert ratio == 2.0

        ratio = Compression.get_compression_ratio(1000, 1000)
        assert ratio == 1.0

    def test_estimate_compressed_size(self):
        """Test compressed size estimation."""
        size = Compression.estimate_compressed_size(1000, format='gzip', data_type='text')
        assert 0 < size < 1000

        size = Compression.estimate_compressed_size(1000, format='bz2', data_type='text')
        assert 0 < size < 1000
