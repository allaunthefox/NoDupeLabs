# pylint: disable=logging-fstring-interpolation
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File system walker for directory traversal.

This module provides file system traversal functionality using standard library only,

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation
with support for filtering, progress tracking, and error handling.

Key Features:
    - Recursive directory traversal
    - File filtering by extension
    - Error handling with graceful degradation
    - Progress tracking support
    - Incremental scanning support

Dependencies:
    - os (standard library)
    - pathlib (standard library)
    - typing (standard library)
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional

from nodupe.core.api.codes import ActionCode
from nodupe.core.archive_interface import ArchiveHandlerInterface
from nodupe.core.container import container as global_container
from nodupe.tools.archive.archive_logic import ArchiveHandler as SecurityHardenedArchiveHandler


logger = logging.getLogger(__name__)


class FileWalker:
    """File system walker for directory traversal.

    Responsibilities:
    - Traverse directory structures
    - Filter files by criteria
    - Handle file system errors gracefully
    - Support incremental scanning
    - Track progress
    """

    def __init__(self, archive_handler: Optional[ArchiveHandlerInterface] = None):
        """Initialize file walker.

        Args:
            archive_handler: Optional ArchiveHandler implementation.
                           If None, attempts to resolve from global_container
                           or falls back to SecurityHardenedArchiveHandler.
        """
        self.logger = logger
        self._file_count = 0
        self._dir_count = 0
        self._error_count = 0
        self._start_time: float = 0.0
        self._last_update: float = 0.0

        # Dependency Injection (Constructor Injection preferred)
        if archive_handler:
            self._archive_handler = archive_handler
        else:
            # Service Location fallback for backward compatibility
            self._archive_handler = global_container.get_service('archive_handler_service')
            if not self._archive_handler:
                self._archive_handler = SecurityHardenedArchiveHandler()

        self._enable_archive_support = True

    def walk(self, root_path: str, file_filter: Optional[Callable[[str], bool]] = None,
             on_progress: Optional[Callable[[dict[str, Any]], None]] = None) -> list[dict[str, Any]]:
        """Walk directory tree and return file information.

        Args:
            root_path: Root directory to start walking from
            file_filter: Optional function to filter files
            on_progress: Optional callback for progress updates

        Returns:
            List of file information dictionaries
        """
        self._reset_counters()
        self._start_time = time.monotonic()
        self._last_update = self._start_time

        files = []
        root_path = str(Path(root_path).absolute())

        try:
            for dirpath, _, filenames in os.walk(root_path, followlinks=False):
                self._dir_count += 1

                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(file_path, root_path)

                    try:
                        file_info = self._get_file_info(file_path, relative_path)

                        if file_filter is None or file_filter(file_info):
                            files.append(file_info)
                            self._file_count += 1

                            # Check for archive files and extract contents
                            if self._enable_archive_support and self._is_archive_file(file_path):
                                archive_files = self._process_archive_file(file_path, root_path)
                                files.extend(archive_files)
                                self._file_count += len(archive_files)

                        self._check_progress_update(on_progress)

                    except Exception as e:
                        self._error_count += 1
                        # pylint: disable=logging-fstring-interpolation
                        self.logger.warning(f"[{ActionCode.FPT_FLS_FAIL}] Error processing file {file_path}: {e}")

                # Update progress after each directory
                self._check_progress_update(on_progress)

        except Exception:
            # pylint: disable=logging-fstring-interpolation
            self.logger.exception(f"[{ActionCode.FPT_FLS_FAIL}] Failed to walk directory {root_path}")
            raise

        return files

    def _get_file_info(self, file_path: str, relative_path: str) -> dict[str, Any]:
        """Get file information for a single file.

        Args:
            file_path: Absolute file path
            relative_path: Relative file path

        Returns:
            Dictionary containing file information
        """
        try:
            stat = os.stat(file_path)

            return {
                'path': file_path,
                'relative_path': relative_path,
                'name': os.path.basename(file_path),
                'extension': os.path.splitext(file_path)[1].lower(),
                'size': stat.st_size,
                'modified_time': int(stat.st_mtime),
                'created_time': int(stat.st_ctime),
                'is_directory': False,
                'is_file': True,
                'is_symlink': os.path.islink(file_path),
                'is_archive': self._is_archive_file(file_path)
            }
        except Exception as e:
            self.logger.warning(f"[{ActionCode.FPT_FLS_FAIL}] Error getting file info for {file_path}: {e}")
            raise

    def _is_archive_file(self, file_path: str) -> bool:
        """Check if file is an archive.

        Args:
            file_path: Path to file

        Returns:
            True if file is an archive
        """
        try:
            return self._archive_handler.is_archive_file(file_path)
        except Exception:
            return False

    def _process_archive_file(self, archive_path: str, base_path: str) -> list[dict[str, Any]]:
        """Process archive file and return contents information.

        Args:
            archive_path: Path to archive file
            base_path: Base path for relative path calculation

        Returns:
            List of file information dictionaries for archive contents
        """
        try:
            return self._archive_handler.get_archive_contents_info(archive_path, base_path)
        except Exception as e:
            self.logger.warning(f"[{ActionCode.FPT_FLS_FAIL}] Error processing archive {archive_path}: {e}")
            return []

    def _check_progress_update(self, on_progress: Optional[Callable[[dict[str, Any]], None]]) -> None:
        """Check if progress update should be sent.

        Args:
            on_progress: Optional progress callback
        """
        if on_progress is None:
            return

        current_time = time.monotonic()
        if current_time - self._last_update >= 0.1:  # Update every 100ms
            self._last_update = current_time
            on_progress(self._get_progress())

    def _get_progress(self) -> dict[str, Any]:
        """Get current progress information.

        Returns:
            Dictionary containing progress information
        """
        elapsed = time.monotonic() - self._start_time
        return {
            'files_processed': self._file_count,
            'directories_processed': self._dir_count,
            'errors_encountered': self._error_count,
            'elapsed_time': elapsed,
            'files_per_second': self._file_count / elapsed if elapsed > 0 else 0
        }

    def _reset_counters(self) -> None:
        """Reset all counters."""
        self._file_count = 0
        self._dir_count = 0
        self._error_count = 0
        self._start_time = 0
        self._last_update = 0

    def get_statistics(self) -> dict[str, Any]:
        """Get final statistics after walk completion.

        Returns:
            Dictionary containing final statistics
        """
        elapsed = time.monotonic() - self._start_time
        return {
            'total_files': self._file_count,
            'total_directories': self._dir_count,
            'total_errors': self._error_count,
            'total_time': elapsed,
            'average_files_per_second': self._file_count / elapsed if elapsed > 0 else 0
        }

    def enable_archive_support(self, enable: bool = True) -> None:
        """Enable or disable archive support.

        Args:
            enable: True to enable archive support, False to disable
        """
        self._enable_archive_support = enable

    def is_archive_support_enabled(self) -> bool:
        """Check if archive support is enabled.

        Returns:
            True if archive support is enabled
        """
        return self._enable_archive_support


def create_file_walker() -> FileWalker:
    """Create and return a FileWalker instance.

    Returns:
        FileWalker instance
    """
    return FileWalker()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="This tool walks through folders and lists all files found.")
    parser.add_argument("path", help="The folder you want to scan")
    args = parser.parse_args()
    walker = FileWalker()
    files = walker.walk(args.path)
    for f in files:
        print(f["path"])
