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

        Args:
            path: Path to the file to process
            known_hash: Optional pre-computed hash to skip re-hashing

        Returns:
            Tuple: (path, size, mtime, hash, mime, context, algo, perms)
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
