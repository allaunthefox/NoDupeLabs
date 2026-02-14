"""Stress and hardening tests for compression module.

These tests validate:
- Large data handling (1KB - 2MB payloads)
- Concurrency safety (thread safety)
- Archive security (path traversal protection)
"""
import concurrent.futures
import tarfile
import io
import pytest
from hypothesis import given, settings, Verbosity, HealthCheck
from hypothesis import strategies as st

from nodupe.core.compression import Compression, CompressionError


# =============================================================================
# PHASE 2: Large Data Property Tests
# =============================================================================

large_binary = st.binary(min_size=1_000, max_size=2_000_000)
compression_formats = st.sampled_from(["gzip", "bz2", "lzma"])


@settings(max_examples=20, deadline=None, verbosity=Verbosity.quiet)
@given(st.tuples(large_binary, compression_formats))
def test_large_roundtrip(data_fmt):
    data, fmt = data_fmt
    """Verify roundtrip for large payloads (1KB - 2MB).
    
    This validates:
    - Reversibility invariant
    - Stability under large input
    - No silent truncation
    """
    compressed = Compression.compress_data(data, fmt)
    decompressed = Compression.decompress_data(compressed, fmt)
    assert decompressed == data, "Large data roundtrip failed"


# =============================================================================
# PHASE 3: Concurrency Stress Tests
# =============================================================================

def roundtrip(data, fmt):
    """Helper for concurrent execution."""
    c = Compression.compress_data(data, fmt)
    return Compression.decompress_data(c, fmt)


@settings(max_examples=10, deadline=None, verbosity=Verbosity.quiet)
@given(st.tuples(st.binary(min_size=10, max_size=50_000), compression_formats))
def test_thread_safety(data_fmt):
    """Verify thread safety and absence of shared state issues.
    
    This validates:
    - No race conditions
    - No shared-state corruption
    - Safe parallel execution
    """
    data, fmt = data_fmt
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(roundtrip, data, fmt) for _ in range(16)]
        results = [f.result() for f in futures]

    for result in results:
        assert result == data, "Thread safety check failed"


# =============================================================================
# PHASE 4: Tar Archive Fuzzing Tests
# =============================================================================

file_names = st.text(min_size=1, max_size=30).filter(
    lambda x: x and "/" not in x and "\\" not in x and "\x00" not in x
)


@settings(max_examples=30, deadline=None, verbosity=Verbosity.quiet, 
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(file_names)
def test_tar_traversal_blocked(tmp_path, name):
    """Verify path traversal attacks are blocked in tar archives.
    
    This validates:
    - Path traversal is rejected
    - Fuzzed filenames do not bypass validation
    """
    tar_path = tmp_path / "malicious.tar"

    # Create malicious tar with path traversal
    with tarfile.open(tar_path, "w") as tf:
        info = tarfile.TarInfo(name=f"../../{name}")
        data = b"x"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))

    # Should raise CompressionError due to path traversal
    with pytest.raises(CompressionError):
        Compression.extract_archive(tar_path, tmp_path / "out")


@settings(max_examples=30, deadline=None, verbosity=Verbosity.quiet,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(file_names)
def test_tar_valid_extraction(tmp_path, name):
    """Verify valid tar archives extract correctly.
    
    This validates:
    - Valid archives extract correctly
    - Fuzzed filenames work properly
    """
    tar_path = tmp_path / "safe.tar"
    out_dir = tmp_path / "out"
    data = b"payload"

    # Create valid tar with fuzzed filename
    with tarfile.open(tar_path, "w") as tf:
        info = tarfile.TarInfo(name=name)
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))

    # Should extract successfully
    extracted = Compression.extract_archive(tar_path, out_dir)

    assert len(extracted) == 1, "Expected 1 extracted file"
    assert extracted[0].read_bytes() == data, "Extracted data mismatch"


@settings(max_examples=30, deadline=None, verbosity=Verbosity.quiet,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(file_names)
def test_tar_gz_traversal_blocked(tmp_path, name):
    """Verify path traversal attacks are blocked in tar.gz archives."""
    tar_path = tmp_path / "malicious.tar.gz"

    with tarfile.open(tar_path, "w:gz") as tf:
        info = tarfile.TarInfo(name=f"../../{name}")
        data = b"x"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))

    with pytest.raises(CompressionError):
        Compression.extract_archive(tar_path, tmp_path / "out")


@settings(max_examples=30, deadline=None, verbosity=Verbosity.quiet,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(file_names)
def test_tar_gz_valid_extraction(tmp_path, name):
    """Verify valid tar.gz archives extract correctly."""
    tar_path = tmp_path / "safe.tar.gz"
    out_dir = tmp_path / "out"
    data = b"payload"

    with tarfile.open(tar_path, "w:gz") as tf:
        info = tarfile.TarInfo(name=name)
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))

    extracted = Compression.extract_archive(tar_path, out_dir)

    assert len(extracted) == 1
    assert extracted[0].read_bytes() == data
