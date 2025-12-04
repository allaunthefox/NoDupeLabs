# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File hashing utilities with multiple algorithm support.

This module provides cryptographic hashing of files using various
algorithms. Implements incremental chunk-based hashing to efficiently
handle large files without loading them entirely into memory.

Supported Algorithms:
    - sha512: SHA-512 (default, recommended for deduplication)
    - sha256: SHA-256 (good balance of speed and security)
    - blake2b: BLAKE2b (fastest, cryptographically secure)
    - sha1: SHA-1 (legacy support, not recommended)
    - md5: MD5 (legacy support, not recommended)

Performance Characteristics:
    - 1MB chunk size optimized for modern storage
    - Incremental hashing prevents memory overflow on large files
    - BLAKE2b typically 2-3x faster than SHA-512
    - SHA-256 good middle ground for speed vs. collision resistance

Key Features:
    - Memory-efficient incremental hashing
    - Algorithm validation before hashing
    - Consistent hex digest output format
    - Support for legacy algorithms (SHA-1, MD5)

Dependencies:
    - hashlib: Standard library cryptographic hashing
    - pathlib: Path handling

Example:
    >>> from pathlib import Path
    >>> file_hash = hash_file(Path('/data/file.bin'), 'sha512')
    >>> print(len(file_hash))  # SHA-512 produces 128 hex chars
    128
    >>> # Validate algorithm before use
    >>> algo = validate_hash_algo('blake2b')
    >>> fast_hash = hash_file(Path('/data/file.bin'), algo)
"""

import hashlib
from pathlib import Path
from typing import Any

CHUNK = 1024 * 1024  # 1MB

SUPPORTED_HASH_ALGOS = {"sha512", "sha256", "blake2b", "sha1", "md5"}


def validate_hash_algo(algo: str) -> str:
    """Validate and normalize hash algorithm name.

    Checks that the requested algorithm is supported and returns
    the normalized lowercase algorithm name.

    Args:
        algo: Hash algorithm name (case-insensitive)

    Returns:
        Normalized algorithm name (lowercase, stripped)

    Raises:
        ValueError: If algorithm is not in SUPPORTED_HASH_ALGOS

    Example:
        >>> validate_hash_algo('SHA512')
        'sha512'
        >>> validate_hash_algo('  blake2b  ')
        'blake2b'
        >>> validate_hash_algo('sha999')
        Traceback (most recent call last):
        ValueError: Unsupported hash algorithm: 'sha999'. Supported: ...
    """
    algo = algo.lower().strip()
    if algo not in SUPPORTED_HASH_ALGOS:
        raise ValueError(
            f"Unsupported hash algorithm: '{algo}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_HASH_ALGOS))}"
        )
    return algo


def hash_file(p: Path, algo: str = "sha512") -> str:
    """Compute cryptographic hash of file using incremental reading.

    Hashes file contents using the specified algorithm with chunk-based
    incremental processing. This prevents memory overflow when hashing
    large files (e.g., video files, disk images).

    Args:
        p: Path to file to hash
        algo: Hash algorithm to use (default: 'sha512')
            Must be one of: sha512, sha256, blake2b, sha1, md5

    Returns:
        Hexadecimal hash digest string (length varies by algorithm:
        SHA-512: 128 chars, SHA-256: 64 chars, BLAKE2b: 128 chars,
        SHA-1: 40 chars, MD5: 32 chars)

    Raises:
        FileNotFoundError: If file at path p doesn't exist
        PermissionError: If file cannot be read
        OSError: If I/O error occurs during reading

    Performance:
        - Reads file in 1MB chunks to optimize I/O
        - BLAKE2b: ~2-3x faster than SHA-512 on modern CPUs
        - SHA-256: Good balance of speed and security
        - SHA-512: Slower but maximum collision resistance

    Example:
        >>> from pathlib import Path
        >>> # Hash with default SHA-512
        >>> h1 = hash_file(Path('/data/photo.jpg'))
        >>> print(len(h1))
        128
        >>> # Hash with faster BLAKE2b
        >>> h2 = hash_file(Path('/data/photo.jpg'), 'blake2b')
        >>> # Both produce consistent results
        >>> h = hash_file(Path('/data/file.bin'))
        >>> hash_file(Path('/data/file.bin')) == h
        True
    """
    h: Any
    if algo == "sha512":
        h = hashlib.sha512()
    elif algo == "sha256":
        h = hashlib.sha256()
    elif algo == "blake2b":
        h = hashlib.blake2b()
    elif algo == "sha1":
        h = hashlib.sha1()
    elif algo == "md5":
        h = hashlib.md5()
    else:
        h = hashlib.sha512()

    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()
