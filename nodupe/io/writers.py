# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File I/O abstractions.

Provides FileWriter protocol and implementations for testable file operations.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional


class FileWriter(ABC):
    """Abstract base for file writing operations.

    Allows dependency injection of file I/O for testing.
    """

    @abstractmethod
    def write(self, path: Path, content: str) -> None:
        """Write content to file.

        Args:
            path: Target file path
            content: Content to write
        """
        pass

    @abstractmethod
    def read(self, path: Path) -> Optional[str]:
        """Read content from file.

        Args:
            path: File path to read

        Returns:
            File content or None if file doesn't exist
        """
        pass

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists
        """
        pass


class RealFileWriter(FileWriter):
    """Concrete FileWriter that performs real filesystem operations.

    This implementation uses an atomic write pattern (write to a temporary
    file then rename) to reduce the chance of partially-written files
    being observed by other processes.
    """

    def write(self, path: Path, content: str) -> None:
        """Write content to `path` on disk, using an atomic replace.

        Args:
            path: Destination filesystem path to write the content to.
            content: UTF-8 text to write.

        Raises:
            OSError: If writing or renaming the temporary file fails.
        """
        # Atomic write: write to temp then rename
        tmp_path = path.with_suffix('.tmp')
        tmp_path.write_text(content, encoding='utf-8')
        tmp_path.rename(path)

    def read(self, path: Path) -> Optional[str]:
        """Read and return UTF-8 text from `path`.

        Args:
            path: Filesystem path to read.

        Returns:
            The file contents as a string, or ``None`` if the file does not
            exist.
        """
        if not path.exists():
            return None
        return path.read_text(encoding='utf-8')

    def exists(self, path: Path) -> bool:
        """Return True when `path` exists on the filesystem.

        Args:
            path: Filesystem path to check.

        Returns:
            True when the file exists, otherwise False.
        """
        return path.exists()


class MemoryFileWriter(FileWriter):
    """A lightweight in-memory FileWriter used for tests.

    Stores files in a dict keyed by the stringified Path. Useful for unit
    tests where interacting with the real filesystem would be slower or
    harder to isolate.
    """

    def __init__(self):
        """Initialize with empty file store."""
        self.files: Dict[str, str] = {}

    def write(self, path: Path, content: str) -> None:
        """Store `content` in the in-memory file store.

        Args:
            path: Logical path key for the in-memory store.
            content: Text content to store.
        """
        self.files[str(path)] = content

    def read(self, path: Path) -> Optional[str]:
        """Return the stored content for `path` if present.

        Args:
            path: Logical path key.

        Returns:
            The stored text or ``None`` when the key does not exist.
        """
        return self.files.get(str(path))

    def exists(self, path: Path) -> bool:
        """Return True if `path` is present in the in-memory store.

        Args:
            path: Logical path key to query.

        Returns:
            True when the key is present, False otherwise.
        """
        return str(path) in self.files
