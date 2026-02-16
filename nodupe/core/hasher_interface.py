# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Hasher Interface.

Defines the interface for hashing aspects to be used by plugins and core.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable

class HasherInterface(ABC):
    """Abstract base class for hashers."""

    @abstractmethod
    def hash_file(self, file_path: str, on_progress: Optional[Callable[[Dict[str, Any]], None]] = None) -> str:
        """Calculate hash of a file."""

    @abstractmethod
    def hash_string(self, data: str) -> str:
        """Calculate hash of a string."""

    @abstractmethod
    def hash_bytes(self, data: bytes) -> str:
        """Calculate hash of bytes."""

    @abstractmethod
    def verify_hash(self, file_path: str, expected_hash: str) -> bool:
        """Verify file hash."""

    @abstractmethod
    def set_algorithm(self, algorithm: str) -> None:
        """Set hash algorithm."""

    @abstractmethod
    def get_algorithm(self) -> str:
        """Get current algorithm."""

    @abstractmethod
    def get_available_algorithms(self) -> List[str]:
        """Get available algorithms."""
