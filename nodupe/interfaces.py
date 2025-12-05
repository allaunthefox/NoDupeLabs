# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Abstract base classes and protocols for NoDupeLabs.

Defines interfaces for key components to enable dependency injection,
testing, and alternative implementations.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class StorageBackend(ABC):
    """Abstract storage backend for file records."""

    @abstractmethod
    def save_file(self, record: Dict[str, Any]) -> None:
        """Save a file record."""
        pass

    @abstractmethod
    def get_file(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get a file record by hash."""
        pass

    @abstractmethod
    def list_files(self, limit: int = 100) -> Iterable[Dict[str, Any]]:
        """List file records."""
        pass


class SimilarityIndex(ABC):
    """Abstract interface for similarity search."""

    @abstractmethod
    def add(self, file_hash: str, embedding: List[float]) -> None:
        """Add embedding to index."""
        pass

    @abstractmethod
    def search(
        self, query: List[float], k: int = 5
    ) -> List[Tuple[str, float]]:
        """Search for similar embeddings.

        Returns:
            List of (file_hash, distance) tuples
        """
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        """Save index to file."""
        pass

    @abstractmethod
    def load(self, path: Path) -> None:
        """Load index from file."""
        pass


class AIBackend(ABC):
    """Abstract AI backend for ML operations."""

    @abstractmethod
    def predict(self, path: Path) -> Dict[str, Any]:
        """Run prediction on file.

        Args:
            path: Path to file

        Returns:
            Dict with prediction results
        """
        pass

    @abstractmethod
    def embed(self, path: Path) -> List[float]:
        """Generate embedding for file.

        Args:
            path: Path to file

        Returns:
            Embedding vector
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get model name."""
        pass


class FileScanner(ABC):
    """Abstract file scanner interface."""

    @abstractmethod
    def scan(self, root: Path) -> Iterable[Dict[str, Any]]:
        """Scan directory for files.

        Args:
            root: Root directory to scan

        Yields:
            File record dicts
        """
        pass


class ConfigProvider(ABC):
    """Abstract configuration provider."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        """Save configuration to file."""
        pass
