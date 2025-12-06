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
    """Abstract storage backend interface for storing and retrieving
    file metadata records.

    Implementations should provide persistent storage for file records
    used by NoDupeLabs. This abstraction allows swapping between an in-
    memory store (tests) and a production DB-backed implementation.
    """

    @abstractmethod
    def save_file(self, record: Dict[str, Any]) -> None:
        """Save or update a single file record in the backend.

        Args:
            record: Mapping representing file metadata (path, size, hash,
                mtime, inferred metadata etc.). Implementations should
                persist this record and ensure it can be retrieved by
                subsequent calls to :py:meth:`get_file`.
        """
        pass

    @abstractmethod
    def get_file(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve a stored file record by content hash.

        Args:
            file_hash: Content hash identifier for the file.

        Returns:
            Optional mapping with file metadata if found, otherwise None.
        """
        pass

    @abstractmethod
    def list_files(self, limit: int = 100) -> Iterable[Dict[str, Any]]:
        """Iterate over file records stored in the backend.

        Args:
            limit: Maximum number of records to return in a single call.

        Yields:
            Mappings containing file metadata for each stored file.
        """
        pass


class SimilarityIndex(ABC):
    """Abstract similarity index interface.

    Implementations must provide an efficient vector index capable of
    adding vectors, searching for nearest neighbors, and persisting the
    index to disk for later reuse.
    """

    @abstractmethod
    def add(self, file_hash: str, embedding: List[float]) -> None:
        """Add or update an embedding into the similarity index.

        Args:
            file_hash: Identifier associated with this embedding (file id).
            embedding: Dense numeric vector representing file features.
        """
        pass

    @abstractmethod
    def search(
        self, query: List[float], k: int = 5
    ) -> List[Tuple[str, float]]:
        """Search the index for the k nearest neighbors to a query vector.

        Args:
            query: Dense numeric query vector.
            k: Number of neighbors to return (default: 5).

        Returns:
            List of (file_hash, score) tuples ordered by increasing distance
            or score depending on the backend semantics.
        """
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        """Persist the index to disk so it can be reloaded later.

        Args:
            path: Filesystem path where index data will be written.
        """
        pass

    @abstractmethod
    def load(self, path: Path) -> None:
        """Load index contents persisted by :py:meth:`save`.

        Args:
            path: Filesystem path to index data previously written by save().
        """
        pass


class AIBackend(ABC):
    """Abstract AI backend used for model inference and embedding.

    Concrete implementations adapt to various runtime engines (ONNX,
    on-device heuristics, cloud) and must implement ``predict`` and
    ``embed`` helpers.
    """

    @abstractmethod
    def predict(self, path: Path) -> Dict[str, Any]:
        """Run model prediction on a single file.

        Args:
            path: Path to a file to run inference over (image/video/etc.).

        Returns:
            Mapping containing the model's prediction results. The exact
            structure is backend-specific but commonly includes scores
            and labels.
        """
        pass

    @abstractmethod
    def embed(self, path: Path) -> List[float]:
        """Compute and return a numeric embedding for a file.

        Args:
            path: File path to compute an embedding for.

        Returns:
            A dense numeric vector representing the file's features.
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return a short name identifying the model/runtime in use.

        The name should be human-readable and include enough detail for
        debugging (e.g. 'onnx-onnxruntime-cpu-v1').
        """
        pass


class FileScanner(ABC):
    """Abstract interface for file scanners.

    Implementations should walk directories and yield normalized file
    metadata dictionaries consumed by the rest of the system.
    """

    @abstractmethod
    def scan(self, root: Path) -> Iterable[Dict[str, Any]]:
        """Scan a root directory and yield file metadata records.

        Args:
            root: Top-level directory to scan for files.

        Yields:
            Mappings describing each discovered file (path, size, mtime,
            hash, inferred metadata, etc.).
        """
        pass


class ConfigProvider(ABC):
    """Abstract configuration provider interface.

    Provides a minimal key/value API for configuration stores used by
    the application. Implementations may back onto files, environment
    variables or more advanced stores.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value.

        Args:
            key: Configuration key to look up.
            default: Fallback value to return when the key is not present.

        Returns:
            The configuration value or the provided default.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set or update a configuration value in the provider.

        Args:
            key: Configuration key to set.
            value: Arbitrary JSON-serializable value to store.
        """
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        """Persist configuration to a file at the provided path.

        Args:
            path: Filesystem path where configuration will be written.
        """
        pass
