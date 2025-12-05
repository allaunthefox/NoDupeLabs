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
    """Actual filesystem implementation."""

    def write(self, path: Path, content: str) -> None:
        """Write content to actual file."""
        # Atomic write: write to temp then rename
        tmp_path = path.with_suffix('.tmp')
        tmp_path.write_text(content, encoding='utf-8')
        tmp_path.rename(path)

    def read(self, path: Path) -> Optional[str]:
        """Read from actual file."""
        if not path.exists():
            return None
        return path.read_text(encoding='utf-8')

    def exists(self, path: Path) -> bool:
        """Check if actual file exists."""
        return path.exists()


class MemoryFileWriter(FileWriter):
    """In-memory implementation for testing."""

    def __init__(self):
        """Initialize with empty file store."""
        self.files: Dict[str, str] = {}

    def write(self, path: Path, content: str) -> None:
        """Write to in-memory store."""
        self.files[str(path)] = content

    def read(self, path: Path) -> Optional[str]:
        """Read from in-memory store."""
        return self.files.get(str(path))

    def exists(self, path: Path) -> bool:
        """Check if file exists in memory."""
        return str(path) in self.files
