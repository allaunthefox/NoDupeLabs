import gzip
import zipfile

import pytest

from nodupe.tools.compression_standard.engine_logic import Compression, CompressionError


def test_compress_decompress_data_all_formats():
    data = b"hello world"

    for fmt in ["gzip", "bz2", "lzma"]:
        compressed = Compression.compress_data(data, fmt)
        decompressed = Compression.decompress_data(compressed, fmt)
        assert decompressed == data


def test_invalid_format_data():
    with pytest.raises(CompressionError):
        Compression.compress_data(b"x", "invalid")

    with pytest.raises(CompressionError):
        Compression.decompress_data(b"x", "invalid")


def test_compress_data_exception(monkeypatch):
    monkeypatch.setattr(gzip, "compress", lambda *a, **k: (_ for _ in ()).throw(Exception("boom")))
    with pytest.raises(CompressionError):
        Compression.compress_data(b"x", "gzip")


def test_file_compression_and_removal(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("hello")

    output = Compression.compress_file(file, format="gzip", remove_original=True)
    assert output.exists()
    assert not file.exists()


def test_file_not_found():
    with pytest.raises(CompressionError):
        Compression.compress_file("missing.txt")


def test_decompress_file(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("hello")

    compressed = Compression.compress_file(file, format="gzip")
    decompressed = Compression.decompress_file(compressed, remove_compressed=True)

    assert decompressed.exists()
    assert not compressed.exists()


def test_decompress_auto_detect_failure(tmp_path):
    file = tmp_path / "file.unknown"
    file.write_text("data")

    with pytest.raises(CompressionError):
        Compression.decompress_file(file)


def test_zip_compression(tmp_path):
    file = tmp_path / "a.txt"
    file.write_text("data")

    zip_path = Compression.compress_file(file, format="zip")
    assert zip_path.exists()


def test_zip_path_traversal(tmp_path):
    zip_path = tmp_path / "evil.zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../evil.txt", "bad")

    with pytest.raises(CompressionError):
        Compression.decompress_file(zip_path, format="zip")


def test_get_ratio():
    assert Compression.get_compression_ratio(100, 50) == 2.0
    assert Compression.get_compression_ratio(100, 0) == 0.0


def test_estimate_size_branches():
    assert Compression.estimate_compressed_size(100, "gzip", "text") == 30
    assert Compression.estimate_compressed_size(100, "gzip", "unknown") == 50
    assert Compression.estimate_compressed_size(100, "unknown", "text") == 50
    assert Compression.estimate_compressed_size(100, "tar.gz", "text") == 30
