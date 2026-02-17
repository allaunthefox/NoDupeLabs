"""Property-based tests for compression module using Hypothesis."""
import pytest
from hypothesis import HealthCheck, Verbosity, assume, given, settings, strategies as st

from nodupe.tools.compression_standard.engine_logic import Compression, CompressionError


binary_data = st.binary(min_size=0, max_size=10_000)
compression_formats = st.sampled_from(["gzip", "bz2", "lzma"])


# 1. Round-Trip Invariant (All Formats)
@given(st.tuples(binary_data, compression_formats))
@settings(verbosity=Verbosity.quiet)
def test_roundtrip_compress_decompress(data_fmt):
    """Round-trip compression/decompression should preserve data exactly."""
    data, fmt = data_fmt
    compressed = Compression.compress_data(data, fmt)
    decompressed = Compression.decompress_data(compressed, fmt)
    assert decompressed == data


# 2. Compression Ratio Sanity Property
@given(st.tuples(binary_data, compression_formats))
@settings(verbosity=Verbosity.quiet)
def test_compressed_data_is_valid(data_fmt):
    """Compressed data should be valid and decompress to original size."""
    data, fmt = data_fmt
    compressed = Compression.compress_data(data, fmt)
    assert len(compressed) >= 0

    decompressed = Compression.decompress_data(compressed, fmt)
    assert len(decompressed) == len(data)


# 3. Corrupted Data Property
@given(binary_data)
@settings(verbosity=Verbosity.quiet, max_examples=100)
def test_corrupted_data_fails(data):
    """Corrupted compressed data should fail to decompress."""
    compressed = Compression.compress_data(data, "gzip")

    if len(compressed) == 0:
        assume(False)

    corrupted = bytearray(compressed)
    corrupted[0] ^= 0xFF  # flip bits

    with pytest.raises(Exception):
        Compression.decompress_data(bytes(corrupted), "gzip")


# 4. File Roundtrip Property
@given(binary_data)
@settings(verbosity=Verbosity.quiet, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_file_roundtrip(tmp_path, data):
    """File-based compression/decompression should preserve data exactly."""
    file = tmp_path / "file.bin"
    file.write_bytes(data)

    compressed = Compression.compress_file(file, format="gzip")
    decompressed = Compression.decompress_file(compressed)

    assert decompressed.read_bytes() == data


# 5. Path Traversal Fuzzing
@given(st.text(min_size=1, max_size=20))
@settings(verbosity=Verbosity.quiet, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_zip_extraction_never_escapes(tmp_path, name):
    """Zip extraction should never escape the target directory."""
    zip_path = tmp_path / "test.zip"

    # Force malicious path
    malicious_name = f"../../{name}"

    import zipfile
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(malicious_name, "data")

    with pytest.raises(CompressionError):
        Compression.decompress_file(zip_path, format="zip")
