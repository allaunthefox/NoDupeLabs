# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Compression utilities with zstd support and fallback.

Provides unified compression/decompression with automatic selection
of best available algorithm (zstd > gzip).
"""
import gzip
import io
from pathlib import Path
from typing import Union

# Try to import zstd (3.14 stdlib or third-party)
_ZSTD_MODULE = None
try:
    import compression.zstd  # noqa: F401
    _ZSTD_MODULE = "stdlib"
except ImportError:
    try:
        import zstandard  # noqa: F401
        _ZSTD_MODULE = "zstandard"
    except ImportError:
        pass


def has_zstd() -> bool:
    """Check if zstd compression is available."""
    return _ZSTD_MODULE is not None


def compress(
    data: bytes,
    level: int = 3,
    algorithm: str = "auto"
) -> bytes:
    """Compress data using best available algorithm.

    Args:
        data: Bytes to compress
        level: Compression level (1-22 for zstd, 1-9 for gzip)
        algorithm: 'auto', 'zstd', or 'gzip'

    Returns:
        Compressed bytes
    """
    if algorithm == "auto":
        algorithm = "zstd" if has_zstd() else "gzip"

    if algorithm == "zstd":
        if _ZSTD_MODULE == "stdlib":
            from compression import zstd
            return zstd.compress(data, level=level)
        elif _ZSTD_MODULE == "zstandard":
            # import zstandard
            cctx = zstandard.ZstdCompressor(level=level)
            return cctx.compress(data)
        else:
            # Fallback to gzip
            algorithm = "gzip"

    # gzip fallback
    buf = io.BytesIO()
    gzip_level = min(level, 9)
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=gzip_level) as f:
        f.write(data)
    return buf.getvalue()


def decompress(data: bytes, algorithm: str = "auto") -> bytes:
    """Decompress data.

    Args:
        data: Compressed bytes
        algorithm: 'auto' (detect), 'zstd', or 'gzip'

    Returns:
        Decompressed bytes
    """
    if algorithm == "auto":
        # Detect format by magic bytes
        if data[:4] == b"\x28\xb5\x2f\xfd":  # zstd magic
            algorithm = "zstd"
        elif data[:2] == b"\x1f\x8b":  # gzip magic
            algorithm = "gzip"
        else:
            raise ValueError("Unknown compression format")

    if algorithm == "zstd":
        if _ZSTD_MODULE == "stdlib":
            from compression import zstd
            return zstd.decompress(data)
        elif _ZSTD_MODULE == "zstandard":
            # import zstandard
            dctx = zstandard.ZstdDecompressor()
            return dctx.decompress(data)
        else:
            raise ValueError("zstd not available")

    # gzip
    buf = io.BytesIO(data)
    with gzip.GzipFile(fileobj=buf, mode="rb") as f:
        return f.read()


def compress_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    level: int = 3,
    algorithm: str = "auto"
) -> Path:
    """Compress a file.

    Args:
        src: Source file path
        dst: Destination file path
        level: Compression level
        algorithm: 'auto', 'zstd', or 'gzip'

    Returns:
        Path to compressed file
    """
    src = Path(src)
    dst = Path(dst)
    data = src.read_bytes()
    compressed = compress(data, level=level, algorithm=algorithm)
    dst.write_bytes(compressed)
    return dst


def decompress_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    algorithm: str = "auto"
) -> Path:
    """Decompress a file.

    Args:
        src: Compressed file path
        dst: Destination file path
        algorithm: 'auto' (detect), 'zstd', or 'gzip'

    Returns:
        Path to decompressed file
    """
    src = Path(src)
    dst = Path(dst)
    data = src.read_bytes()
    decompressed = decompress(data, algorithm=algorithm)
    dst.write_bytes(decompressed)
    return dst
