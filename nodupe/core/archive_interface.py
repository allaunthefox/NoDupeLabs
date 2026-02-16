# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Archive Handler Interface.

Defines the interface for archive handling aspects to be used by plugins and core.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

class ArchiveHandlerInterface(ABC):
    """Abstract base class for archive handlers."""

    @abstractmethod
    def is_archive_file(self, file_path: str) -> bool:
        """Check if file is an archive."""

    @abstractmethod
    def detect_archive_format(self, file_path: str) -> Optional[str]:
        """Detect archive format."""

    @abstractmethod
    def extract_archive(self, archive_path: str, extract_to: Optional[str] = None, password: Optional[bytes] = None) -> Dict[str, str]:
        """Extract archive contents."""

    @abstractmethod
    def create_archive(self, output_path: str, files: List[str], format: Optional[str] = None) -> str:
        """Create an archive from a list of files."""

    @abstractmethod
    def get_archive_contents_info(self, archive_path: str, base_path: str) -> List[Dict[str, Any]]:
        """Get file information for archive contents."""

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up temporary resources."""
