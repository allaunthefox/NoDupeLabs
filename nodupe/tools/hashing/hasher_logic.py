# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File hasher for cryptographic hashing operations.

This module provides file hashing functionality using only standard library,
with support for multiple hash algorithms and chunked processing.

Key Features:
    - Multiple hash algorithms (SHA256, MD5, etc.)
    - Chunked file processing for large files
    - Progress tracking
    - Batch processing
    - Error handling

Dependencies:
    - hashlib (standard library)
    - os (standard library)
    - typing (standard library)
"""

import hashlib
import os
from typing import Any, Callable, Optional


try:
    from ..hasher_interface import HasherInterface
except (ImportError, ValueError):
    from nodupe.core.hasher_interface import HasherInterface


class FileHasher(HasherInterface):
    """File hasher for cryptographic hashing operations.

    Responsibilities:
    - Calculate file hashes using various algorithms
    - Handle large files with chunked processing
    - Support progress tracking
    - Provide batch processing
    - Handle hashing errors
    """

    def __init__(self, algorithm: str = 'sha256', buffer_size: int = 65536):
        """Initialize file hasher.

        Args:
            algorithm: Hash algorithm to use (default: 'sha256')
            buffer_size: Buffer size for chunked reading (default: 64KB)
        """
        self.set_algorithm(algorithm)
        self.set_buffer_size(buffer_size)

    def hash_file(self, file_path: str, on_progress: Optional[Callable[[dict[str, Any]], None]] = None) -> str:
        """Calculate hash of a file.

        Args:
            file_path: Path to file
            on_progress: Optional progress callback

        Returns:
            Hexadecimal hash string
        """
        try:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            file_size = os.path.getsize(file_path)
            hasher = hashlib.new(self._algorithm)
            bytes_read = 0

            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(self._buffer_size)
                    if not data:
                        break

                    hasher.update(data)
                    bytes_read += len(data)

                    # Update progress
                    if on_progress:
                        progress = {
                            'file_path': file_path,
                            'bytes_read': bytes_read,
                            'total_bytes': file_size,
                            'percent_complete': (bytes_read / file_size) * 100 if file_size > 0 else 100
                        }
                        on_progress(progress)

            return hasher.hexdigest()

        except Exception as e:
            print(f"[ERROR] Failed to hash file {file_path}: {e}")
            raise

    def hash_files(self, file_paths: list[str],
                   on_progress: Optional[Callable[[dict[str, Any]], None]] = None) -> dict[str, str]:
        """Calculate hashes for multiple files.

        Args:
            file_paths: List of file paths
            on_progress: Optional progress callback

        Returns:
            Dictionary mapping file paths to hashes
        """
        results = {}

        for i, file_path in enumerate(file_paths):
            try:
                if not os.path.isfile(file_path):
                    continue

                file_hash = self.hash_file(file_path, on_progress)
                results[file_path] = file_hash

                # Update overall progress
                if on_progress:
                    overall_progress = {
                        'files_processed': i + 1,
                        'total_files': len(file_paths),
                        'current_file': file_path,
                        'current_hash': file_hash
                    }
                    on_progress(overall_progress)

            except Exception as e:
                print(f"[WARNING] Error hashing file {file_path}: {e}")
                continue

        return results

    def hash_string(self, data: str) -> str:
        """Calculate hash of a string.

        Args:
            data: String data to hash

        Returns:
            Hexadecimal hash string
        """
        try:
            hasher = hashlib.new(self._algorithm)
            hasher.update(data.encode('utf-8'))
            return hasher.hexdigest()
        except Exception as e:
            print(f"[ERROR] Failed to hash string: {e}")
            raise

    def hash_bytes(self, data: bytes) -> str:
        """Calculate hash of bytes.

        Args:
            data: Bytes data to hash

        Returns:
            Hexadecimal hash string
        """
        try:
            hasher = hashlib.new(self._algorithm)
            hasher.update(data)
            return hasher.hexdigest()
        except Exception as e:
            print(f"[ERROR] Failed to hash bytes: {e}")
            raise

    def verify_hash(self, file_path: str, expected_hash: str) -> bool:
        """Verify file hash against expected value.

        Args:
            file_path: Path to file
            expected_hash: Expected hash value

        Returns:
            True if hash matches, False otherwise
        """
        try:
            actual_hash = self.hash_file(file_path)
            return actual_hash == expected_hash
        except Exception as e:
            print(f"[ERROR] Failed to verify hash for {file_path}: {e}")
            return False

    def set_algorithm(self, algorithm: str) -> None:
        """Set hash algorithm to use.

        Args:
            algorithm: Hash algorithm name

        Raises:
            ValueError: If algorithm is not available
        """
        algorithm_lower = algorithm.lower()
        if algorithm_lower not in hashlib.algorithms_available:
            raise ValueError(f"Hash algorithm {algorithm} not available")

        self._algorithm = algorithm_lower

    def get_algorithm(self) -> str:
        """Get current hash algorithm.

        Returns:
            Current hash algorithm name
        """
        return self._algorithm

    def set_buffer_size(self, buffer_size: int) -> None:
        """Set buffer size for chunked reading.

        Args:
            buffer_size: Buffer size in bytes

        Raises:
            ValueError: If buffer size is not positive
        """
        if buffer_size <= 0:
            raise ValueError("Buffer size must be positive")

        self._buffer_size = buffer_size

    def get_buffer_size(self) -> int:
        """Get current buffer size.

        Returns:
            Current buffer size in bytes
        """
        return self._buffer_size

    def get_available_algorithms(self) -> list[str]:
        """Get list of available hash algorithms.

        Returns:
            List of available algorithm names
        """
        return sorted(hashlib.algorithms_available)


def create_file_hasher(algorithm: str = 'sha256', buffer_size: int = 65536) -> FileHasher:
    """Create and return a FileHasher instance.

    Args:
        algorithm: Hash algorithm to use
        buffer_size: Buffer size for chunked reading

    Returns:
        FileHasher instance
    """
    return FileHasher(algorithm, buffer_size)
