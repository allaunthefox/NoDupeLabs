# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Compression Module.

This module provides data compression functionality for database storage optimization.

Classes:
    DatabaseCompression: Handles data compression and decompression.

Example:
    >>> from nodupe.core.database import Database
    >>> db = Database("/path/to/db.db")
    >>> compressed = db.compression.compress_data("large text data")
"""

from __future__ import annotations

import zlib
from typing import Any


class DatabaseCompression:
    """Database data compression.

    Provides methods for compressing and decompressing data stored in the database
    to optimize storage and reduce I/O overhead.

    Example:
        >>> compression = DatabaseCompression(connection)
        >>> compressed = compression.compress_data("data")
        >>> decompressed = compression.decompress_data(compressed)
    """

    def __init__(self, connection: Any, level: int = 6) -> None:
        """Initialize database compression.

        Args:
            connection: Database connection instance.
            level: Compression level (1-9, default 6).
        """
        self.connection = connection
        self.level = max(1, min(9, level))

    def compress_data(self, data: Any) -> bytes:
        """Compress data.

        Args:
            data: Data to compress (str or bytes).

        Returns:
            Compressed data as bytes.

        Raises:
            ValueError: If data cannot be compressed.

        Example:
            >>> compression.compress_data("large text")
            b'x\x9c...'
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        try:
            return zlib.compress(data, self.level)
        except zlib.error as e:
            raise ValueError(f"Compression failed: {e}")

    def decompress_data(self, compressed_data: bytes) -> Any:
        """Decompress data.

        Args:
            compressed_data: Compressed data bytes.

        Returns:
            Decompressed data (str or bytes depending on original).

        Raises:
            ValueError: If decompression fails.

        Example:
            >>> compression.decompress_data(compressed)
            'original data'
        """
        try:
            decompressed = zlib.decompress(compressed_data)
            # Try to decode as UTF-8
            try:
                return decompressed.decode("utf-8")
            except UnicodeDecodeError:
                return decompressed
        except zlib.error as e:
            raise ValueError(f"Decompression failed: {e}")

    def compress_safe(self, data: Any) -> bytes:
        """Safely compress data, returning empty bytes on failure.

        Args:
            data: Data to compress.

        Returns:
            Compressed data or empty bytes on failure.

        Example:
            >>> compression.compress_safe("data")
            b'x\x9c...'
        """
        try:
            return self.compress_data(data)
        except ValueError:
            return b""

    def decompress_safe(self, compressed_data: bytes) -> Any:
        """Safely decompress data, returning original on failure.

        Args:
            compressed_data: Compressed data.

        Returns:
            Decompressed data or original data on failure.

        Example:
            >>> compression.decompress_safe(compressed)
            'data'
        """
        try:
            return self.decompress_data(compressed_data)
        except ValueError:
            return compressed_data
