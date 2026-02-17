# pylint: disable=logging-fstring-interpolation
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File processor for metadata extraction and duplicate detection.

This module provides file processing functionality including metadata extraction,
hashing, and duplicate detection using only standard library.

Key Features:
    - File metadata extraction
    - Cryptographic hashing
    - Duplicate detection
    - Batch processing
    - Error handling

Dependencies:
    - hashlib (standard library)
    - os (standard library)
    - typing (standard library)
"""

import argparse
import hashlib
import logging
import os
from typing import Any, Callable, Optional

from nodupe.core.api.codes import ActionCode
from nodupe.core.container import container as global_container
from nodupe.core.hasher_interface import HasherInterface

from .walker import FileWalker

logger = logging.getLogger(__name__)


def _get_default_hasher() -> HasherInterface:
    """Get or create default hasher instance.

    Returns:
        HasherInterface implementation
    """
    # Try to get from container first
    hasher = global_container.get_service("hasher_service")
    if hasher is not None:
        return hasher

    # Fallback: create a new FileHasher instance
    from nodupe.tools.hashing.hasher_logic import FileHasher

    return FileHasher()


class FileProcessor:
    """File processor for metadata extraction and duplicate detection.

    Responsibilities:
    - Process files and extract metadata
    - Calculate file hashes
    - Detect duplicates
    - Handle processing errors
    - Support batch operations
    """

    def __init__(
        self,
        file_walker: Optional[FileWalker] = None,
        hasher: Optional[HasherInterface] = None,
    ):
        """Initialize file processor.

        Args:
            file_walker: Optional FileWalker instance
            hasher: Optional HasherInterface implementation.
                   If None, attempts to resolve from global_container.
        """
        self.logger = logger
        self.file_walker = file_walker or FileWalker()

        # Dependency Injection (Constructor Injection preferred)
        if hasher:
            self._hasher = hasher
        else:
            # Service Location fallback with default hasher
            self._hasher = _get_default_hasher()

        self._hash_algorithm = "sha256"
        self._hash_buffer_size = 65536  # 64KB buffer

    def process_files(
        self,
        root_path: str,
        file_filter: Optional[Callable[[Any], bool]] = None,
        on_progress: Optional[Callable[[Any], None]] = None,
    ) -> list[dict[str, Any]]:
        """Process files in directory and return processed file information.

        Args:
            root_path: Root directory to process
            file_filter: Optional function to filter files
            on_progress: Optional callback for progress updates

        Returns:
            List of processed file information
        """
        # First, walk the directory to get file list
        files = self.file_walker.walk(root_path, file_filter, on_progress)

        # Then process each file to add hashes and other metadata
        processed_files = []
        for i, file_info in enumerate(files):
            try:
                processed_file = self._process_single_file(file_info)

                if processed_file:
                    processed_files.append(processed_file)

                # Update progress
                if on_progress and (i % 10 == 0 or i == len(files) - 1):
                    progress = {
                        "files_processed": i + 1,
                        "total_files": len(files),
                        "current_file": file_info["path"],
                    }
                    on_progress(progress)

            except Exception as e:  # pylint: disable=broad-exception-caught
                self.logger.warning(
                    "[%s] Error processing file %s: %s",
                    ActionCode["FPT_FLS_FAIL"],
                    file_info["path"],
                    e,
                )
                continue

        return processed_files

    def _process_single_file(
        self, file_info: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Process a single file and return enhanced file information.

        Args:
            file_info: Basic file information

        Returns:
            Enhanced file information with hash and metadata
        """
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_info["path"])

            # Create enhanced file info
            processed_file = {
                **file_info,
                "hash": file_hash,
                "hash_algorithm": self._hash_algorithm,
                "is_duplicate": False,
                "duplicate_of": None,
            }

            return processed_file

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(
                "[%s] Error processing file %s: %s",
                ActionCode["FPT_FLS_FAIL"],
                file_info["path"],
                e,
            )
            return None

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate cryptographic hash of file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal hash string
        """
        try:
            # Sync internal state if needed (backward compatibility for direct attribute changes)
            if hasattr(self._hasher, "set_algorithm"):
                self._hasher.set_algorithm(self._hash_algorithm)

            return self._hasher.hash_file(file_path)

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(
                "[%s] Error calculating hash for %s: %s",
                ActionCode["FPT_FLS_FAIL"],
                file_path,
                e,
            )
            raise

    def detect_duplicates(
        self, files: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Detect duplicates in list of files.

        Args:
            files: List of file information

        Returns:
            List of files with duplicate information updated
        """
        if not files:
            return files

        # Group files by hash
        hash_groups = {}
        for file_info in files:
            if "hash" not in file_info or not file_info["hash"]:
                continue

            file_hash = file_info["hash"]
            if file_hash not in hash_groups:
                hash_groups[file_hash] = []
            hash_groups[file_hash].append(file_info)

        # Mark duplicates
        for file_hash, group in hash_groups.items():
            if len(group) > 1:
                # Sort by file size (largest is likely original)
                group.sort(key=lambda x: x["size"], reverse=True)

                # First file is original, rest are duplicates
                original_file = group[0]
                for duplicate_file in group[1:]:
                    duplicate_file["is_duplicate"] = True
                    duplicate_file["duplicate_of"] = original_file["path"]

        return files

    def batch_process_files(
        self,
        file_paths: list[str],
        on_progress: Optional[Callable[[Any], None]] = None,
    ) -> list[dict[str, Any]]:
        """Process multiple files in batch.

        Args:
            file_paths: List of file paths to process
            on_progress: Optional progress callback

        Returns:
            List of processed file information
        """
        processed_files = []

        for i, file_path in enumerate(file_paths):
            try:
                if not os.path.isfile(file_path):
                    continue

                file_info = self._get_basic_file_info(file_path)
                processed_file = self._process_single_file(file_info)

                if processed_file:
                    processed_files.append(processed_file)

                # Update progress
                if on_progress and (i % 10 == 0 or i == len(file_paths) - 1):
                    progress = {
                        "files_processed": i + 1,
                        "total_files": len(file_paths),
                        "current_file": file_path,
                    }
                    on_progress(progress)

            except Exception as e:  # pylint: disable=broad-exception-caught
                self.logger.warning(
                    "[%s] Error processing file %s: %s",
                    ActionCode["FPT_FLS_FAIL"],
                    file_path,
                    e,
                )
                continue

        return processed_files

    def _get_basic_file_info(self, file_path: str) -> dict[str, Any]:
        """Get basic file information for a single file.

        Args:
            file_path: Path to file

        Returns:
            Basic file information dictionary
        """
        try:
            stat = os.stat(file_path)

            return {
                "path": file_path,
                "relative_path": os.path.basename(file_path),
                "name": os.path.basename(file_path),
                "extension": os.path.splitext(file_path)[1].lower(),
                "size": stat.st_size,
                "modified_time": int(stat.st_mtime),
                "created_time": int(stat.st_ctime),
                "is_directory": False,
                "is_file": True,
                "is_symlink": os.path.islink(file_path),
            }
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(
                "[%s] Error getting file info for %s: %s",
                ActionCode["FPT_FLS_FAIL"],
                file_path,
                e,
            )
            raise

    def set_hash_algorithm(self, algorithm: str) -> None:
        """Set hash algorithm to use.

        Args:
            algorithm: Hash algorithm name (e.g., 'sha256', 'md5')
        """
        if algorithm.lower() not in hashlib.algorithms_available:
            raise ValueError(f"Hash algorithm {algorithm} not available")

        self._hash_algorithm = algorithm.lower()

    def get_hash_algorithm(self) -> str:
        """Get current hash algorithm.

        Returns:
            Current hash algorithm name
        """
        return self._hash_algorithm

    def set_hash_buffer_size(self, buffer_size: int) -> None:
        """Set buffer size for hash calculation.

        Args:
            buffer_size: Buffer size in bytes
        """
        if buffer_size <= 0:
            raise ValueError("Buffer size must be positive")

        self._hash_buffer_size = buffer_size

    def get_hash_buffer_size(self) -> int:
        """Get current hash buffer size.

        Returns:
            Current buffer size in bytes
        """
        return self._hash_buffer_size


def create_file_processor(
    file_walker: Optional[FileWalker] = None,
) -> FileProcessor:
    """Create and return a FileProcessor instance.

    Args:
        file_walker: Optional FileWalker instance

    Returns:
        FileProcessor instance
    """
    return FileProcessor(file_walker)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This tool creates digital fingerprints for files to find duplicates."
    )
    parser.add_argument("path", help="The file or folder you want to process")
    args = parser.parse_args()
    processor = FileProcessor()
    results = processor.process_files(args.path)
    for r in results:
        print(f"{r["hash"]}  {r["path"]}")
