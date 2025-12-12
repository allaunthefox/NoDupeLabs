# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File processing utilities.

Provides the FileProcessor class for processing individual files
during scanning operations.
"""
from pathlib import Path
from typing import Optional, Tuple

from ..utils.hashing import hash_file
from ..utils.filesystem import detect_context, get_mime_safe, get_permissions


# Type alias for file record tuple
FileRecord = Tuple[str, int, int, str, str, str, str, str]


class FileProcessor:
    """Processes files and extracts metadata.

    Handles hashing, MIME detection, context detection, and permissions
    extraction for individual files.

    Attributes:
        hash_algo: Hash algorithm to use
    """

    def __init__(self, hash_algo: str = "sha512"):
        """Initialize file processor.

        Args:
            hash_algo: Hash algorithm name (sha256, sha512, blake2b)
        """
        self.hash_algo = hash_algo

    def process(
        self,
        path: Path,
        known_hash: Optional[str] = None
    ) -> FileRecord:
        """Process a single file and return a metadata tuple.

        This method handles all aspects of file processing including:
        - File statistics (size, modification time)
        - Hash computation (or reuse of known hash)
        - MIME type detection
        - Context detection (file category)
        - Permission extraction

        Args:
            path: Path to the file to process
            known_hash: Optional pre-computed hash to skip re-hashing

        Returns:
            Tuple containing file metadata with elements:
            - path: File path as string
            - size: File size in bytes
            - mtime: Modification timestamp as integer
            - hash: File hash string
            - mime: MIME type string
            - context: Detected context/category string
            - algo: Hash algorithm used
            - perms: File permissions string

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be read
            OSError: If file operations fail

        Example:
            >>> processor = FileProcessor("sha512")
            >>> record = processor.process(Path("/path/to/file.txt"))
            >>> print(f"File: {record[0]}, Hash: {record[3]}")
        """
        st = path.stat()

        if known_hash:
            file_hash = known_hash
        else:
            file_hash = hash_file(path, self.hash_algo)

        mime = get_mime_safe(path)
        context = detect_context(path)
        perms = get_permissions(path)

        return (
            str(path),
            st.st_size,
            int(st.st_mtime),
            file_hash,
            mime,
            context,
            self.hash_algo,
            perms
        )


def process_file(
    p: Path, hash_algo: str, known_hash: Optional[str] = None
) -> Tuple[str, int, int, str, str, str, str, str]:
    """Process a single file and return a metadata tuple.

    This standalone function processes individual files and returns
    metadata in the standard format used throughout the project.
    It's used by both the FileProcessor class and direct calls.

    Args:
        p: Path to the file to process
        hash_algo: Hash algorithm name used by hash_file
        known_hash: Optional pre-computed hash to avoid re-hashing
            (used by incremental scans where file size/mtime match)

    Returns:
        Tuple containing file metadata with elements:
        - path: File path as string
        - size: File size in bytes
        - mtime: Modification timestamp as integer
        - hash: File hash string
        - mime: MIME type string
        - context: Detected context/category string
        - algo: Hash algorithm used
        - perms: File permissions string

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
        OSError: If file operations fail

    Example:
        >>> record = process_file(Path("/path/to/file.txt"), "sha512")
        >>> print(f"File: {record[0]}, Size: {record[1]} bytes")
    """
    st = p.stat()

    if known_hash:
        sha = known_hash
    else:
        sha = hash_file(p, hash_algo)

    mime = get_mime_safe(p)
    context = detect_context(p)
    perms = get_permissions(p)
    return (
        str(p), st.st_size, int(st.st_mtime), sha, mime,
        context, hash_algo, perms
    )
