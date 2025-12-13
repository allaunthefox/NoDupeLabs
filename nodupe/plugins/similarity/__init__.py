# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Similarity search module for finding similar files using vector embeddings.

This module provides the similarity search functionality for NoDupeLabs,
allowing users to find similar files based on content embeddings.

Key Features:
    - Vector similarity search
    - Multiple backend support
    - Index management
    - Near-duplicate detection
    - Graceful degradation

Dependencies:
    - typing (standard library)
    - abc (standard library)
    - numpy (optional, for brute-force backend)
"""

from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import json
import pickle
import warnings

import numpy as np

# Handle optional FAISS dependency
# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnnecessaryComparison=false  # pylint: disable=line-too-long
try:
    import faiss
    # Import IndexFlatIP for type hints, but it may not be used directly
    from faiss import IndexFlatIP  # type: ignore[attr-defined]
except ImportError:
    import warnings
    from typing import Any, List, Dict

    # Type aliases for when FAISS is not available
    class _FakeFaiss:
        """Fake FAISS class for type safety when FAISS is not available."""
        def __getattr__(self, name: str) -> Any:
            """Get any attribute (returns None for all)."""
            return None

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            """Allow calling fake FAISS methods."""
            return None

    class _FakeIndexFlatIP:
        """Fake IndexFlatIP class for type safety when FAISS is not available."""
        def __getattr__(self, name: str) -> Any:
            """Get any attribute (returns None for all)."""
            return None

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            """Allow calling fake FAISS methods."""
            return None

    faiss = _FakeFaiss()
    IndexFlatIP = _FakeIndexFlatIP  # type: ignore[assignment]


class SimilarityBackend(ABC):
    """Abstract base class for similarity search backends.

    Responsibilities:
    - Index management
    - Similarity search
    - Vector operations
    - Graceful degradation
    """

    @abstractmethod
    def __init__(self, dimensions: int):
        """Initialize similarity backend.

        Args:
            dimensions: Number of dimensions for vectors
        """
        raise NotImplementedError

    @abstractmethod
    def add_vectors(self,
                    vectors: List[List[float]],
                    metadata: List[Dict[str,
                                        Any]]) -> bool:
        """Add vectors to the index.

        Args:
            vectors: List of vectors to add
            metadata: List of metadata dictionaries

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def search(self,
               query_vector: List[float],
               k: int = 5,
               threshold: float = 0.8) -> List[Tuple[Dict[str,
                                               Any],
                                                     float]]:
        """Search for similar vectors.

        Args:
            query_vector: Query vector
            k: Number of results to return
            threshold: Similarity threshold

        Returns:
            List of (metadata, similarity_score) tuples
        """
        raise NotImplementedError

    @abstractmethod
    def save_index(self, path: str) -> bool:
        """Save index to file.

        Args:
            path: Path to save index

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def load_index(self, path: str) -> bool:
        """Load index from file.

        Args:
            path: Path to load index from

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_index_size(self) -> int:
        """Get number of vectors in index.

        Returns:
            Number of vectors in index
        """
        raise NotImplementedError

    @abstractmethod
    def clear_index(self) -> None:
        """Clear the index."""
        raise NotImplementedError


class BruteForceBackend(SimilarityBackend):
    """Brute-force similarity search backend using NumPy.

    This backend uses NumPy for vector operations and provides
    a simple brute-force search implementation.
    """

    def __init__(self, dimensions: int):
        """Initialize brute-force backend.

        Args:
            dimensions: Number of dimensions for vectors
        """
        self.dimensions: int = dimensions
        self.vectors: List[List[float]] = []
        self.metadata: List[Dict[str, Any]] = []

        self.np = np
        self.use_numpy: bool = True

    def add_vectors(self,
                    vectors: List[List[float]],
                    metadata: List[Dict[str,
                                        Any]]) -> bool:
        """Add vectors to the index.

        Args:
            vectors: List of vectors to add
            metadata: List of metadata dictionaries

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate input
            if len(vectors) != len(metadata):
                warnings.warn("Vectors and metadata length mismatch")
                return False

            if len(vectors) == 0:
                return True

            # Validate dimensions
            for vector in vectors:
                if len(vector) != self.dimensions:
                    warnings.warn(
                        f"Vector dimension mismatch: expected {self.dimensions}, got {len(vector)}")
                    return False

            # Add vectors and metadata
            self.vectors.extend(vectors)  # type: ignore[arg-type]
            self.metadata.extend(metadata)  # type: ignore[arg-type]

            return True
        except (ValueError, TypeError, AttributeError) as e:
            warnings.warn(f"Failed to add vectors: {str(e)}")
            return False

    def search(self,
               query_vector: List[float],
               k: int = 5,
               threshold: float = 0.8) -> List[Tuple[Dict[str,
                                               Any],
                                                     float]]:
        """Search for similar vectors using brute-force approach.

        Args:
            query_vector: Query vector
            k: Number of results to return
            threshold: Similarity threshold

        Returns:
            List of (metadata, similarity_score) tuples
        """
        if len(self.vectors) == 0:
            return []

        if len(query_vector) != self.dimensions:
            warnings.warn(
                f"Query vector dimension mismatch: expected {
                    self.dimensions}, got {
                    len(query_vector)}")
            return []

        try:
            results = []

            if self.use_numpy:
                # Use NumPy for efficient vector operations
                query_array = self.np.array(query_vector)
                vectors_array = self.np.array(self.vectors)

                # Calculate cosine similarity
                dot_products = self.np.dot(vectors_array, query_array)
                query_norm = self.np.linalg.norm(query_array)
                vector_norms = self.np.linalg.norm(vectors_array, axis=1)
                similarities = dot_products / (vector_norms * query_norm)

                # Get top k results
                top_indices = self.np.argsort(similarities)[-k:][::-1]

                for idx in top_indices:
                    similarity = similarities[idx]
                    if similarity >= threshold:
                        results.append((self.metadata[idx], similarity))  # type: ignore[arg-type]
            else:
                # Fallback to standard library implementation
                for i, vector in enumerate(self.vectors):
                    # Calculate cosine similarity manually
                    dot_product = sum(v * q for v, q in zip(vector, query_vector))
                    query_norm = sum(q**2 for q in query_vector)**0.5
                    vector_norm = sum(v**2 for v in vector)**0.5

                    if query_norm == 0 or vector_norm == 0:
                        similarity = 0.0
                    else:
                        similarity = dot_product / (query_norm * vector_norm)

                    if similarity >= threshold:
                        results.append((self.metadata[i], similarity))

                # Sort by similarity (descending)
                results.sort(key=lambda x: x[1], reverse=True)  # type: ignore[arg-type, return-value]
                results = results[:k]  # type: ignore[assignment]

            return results

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            warnings.warn(f"Similarity search failed: {str(e)}")
            return []

    def save_index(self, path: str) -> bool:
        """Save index to file.

        Args:
            path: Path to save index

        Returns:
            True if successful, False otherwise
        """
        try:
            # Save vectors and metadata
            index_data: Dict[str, Any] = {
                'vectors': self.vectors,
                'metadata': self.metadata,
                'dimensions': self.dimensions
            }

            with open(path, 'wb') as f:
                pickle.dump(index_data, f)

            return True
        except (IOError, OSError, pickle.PickleError) as e:
            warnings.warn(f"Failed to save index: {str(e)}")
            return False

    def load_index(self, path: str) -> bool:
        """Load index from file.

        Args:
            path: Path to load index from

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, 'rb') as f:
                index_data = pickle.load(f)

            # Validate dimensions
            if index_data['dimensions'] != self.dimensions:
                warnings.warn(
                    f"Index dimension mismatch: expected {
                        self.dimensions}, got {
                        index_data['dimensions']}")
                return False

            self.vectors = index_data['vectors']
            self.metadata = index_data['metadata']

            return True
        except (IOError, OSError, pickle.PickleError) as e:
            warnings.warn(f"Failed to load index: {str(e)}")
            return False

    def get_index_size(self) -> int:
        """Get number of vectors in index.

        Returns:
            Number of vectors in index
        """
        return len(self.vectors)

    def clear_index(self) -> None:
        """Clear the index."""
        self.vectors = []
        self.metadata = []


class FaissBackend(SimilarityBackend):
    """FAISS similarity search backend.

    This backend uses Facebook's FAISS library for efficient
    similarity search on large datasets.
    """

    def __init__(self, dimensions: int):
        """Initialize FAISS backend.

        Args:
            dimensions: Number of dimensions for vectors
        """
        self.dimensions: int = dimensions
        self.index: Optional[Any] = None
        self.metadata: List[Dict[str, Any]] = []

        self.faiss = faiss
        self.available: bool = True

        # Create FAISS index
        if faiss is not None and hasattr(faiss, 'IndexFlatIP'):
            self.index = faiss.IndexFlatIP(dimensions)  # type: ignore[attr-defined]
        else:
            self.available = False
            warnings.warn("FAISS not available, backend will not function")

    def add_vectors(self,
                    vectors: List[List[float]],
                    metadata: List[Dict[str,
                                        Any]]) -> bool:
        """Add vectors to the index.

        Args:
            vectors: List of vectors to add
            metadata: List of metadata dictionaries

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            warnings.warn("FAISS backend not available")
            return False

        try:
            # Validate input
            if len(vectors) != len(metadata):
                warnings.warn("Vectors and metadata length mismatch")
                return False

            if len(vectors) == 0:
                return True

            # Validate dimensions
            for vector in vectors:
                if len(vector) != self.dimensions:
                    warnings.warn(
                        f"Vector dimension mismatch: expected {
                            self.dimensions}, got {
                            len(vector)}")
                    return False

            # Convert to numpy array
            vectors_array = np.array(vectors, dtype=np.float32)

            # Add to FAISS index
            if self.index is not None and hasattr(self.index, 'add'):
                self.index.add(vectors_array)  # type: ignore[attr-defined]
            self.metadata.extend(metadata)  # type: ignore[arg-type]

            return True
        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            warnings.warn(f"Failed to add vectors to FAISS index: {str(e)}")
            return False

    def search(self,
               query_vector: List[float],
               k: int = 5,
               threshold: float = 0.8) -> List[Tuple[Dict[str,
                                               Any],
                                                     float]]:
        """Search for similar vectors using FAISS.

        Args:
            query_vector: Query vector
            k: Number of results to return
            threshold: Similarity threshold

        Returns:
            List of (metadata, similarity_score) tuples
        """
        if not self.available:
            warnings.warn("FAISS backend not available")
            return []

        if len(query_vector) != self.dimensions:
            warnings.warn(
                f"Query vector dimension mismatch: expected {
                    self.dimensions}, got {
                    len(query_vector)}")
            return []

        try:
            # Convert query to numpy array
            query_array = np.array([query_vector], dtype=np.float32)

            # Search FAISS index
            if self.index is not None and hasattr(self.index, 'search'):
                distances, indices = self.index.search(query_array, k)  # type: ignore[attr-defined]
            else:
                return []

            results: List[Tuple[Dict[str, Any], float]] = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.metadata):
                    similarity = distances[0][i]
                    if similarity >= threshold:
                        results.append((self.metadata[idx], similarity))  # type: ignore[arg-type]

            return results

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            warnings.warn(f"FAISS search failed: {str(e)}")
            return []

    def save_index(self, path: str) -> bool:
        """Save index to file.

        Args:
            path: Path to save index

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            warnings.warn("FAISS backend not available")
            return False

        try:
            # Save FAISS index
            if (self.faiss is not None and
                hasattr(self.faiss, 'write_index') and
                self.index is not None and
                hasattr(self.index, 'add')):
                try:
                    # Use type narrowing with try/except
                    if hasattr(self.faiss, 'write_index'):
                        self.faiss.write_index(self.index, path)  # type: ignore[attr-defined]
                except (AttributeError, TypeError):
                    warnings.warn("FAISS write_index method failed")
                    return False
            else:
                warnings.warn("FAISS write_index method not available")
                return False

            # Save metadata separately
            metadata_path = path + ".metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f)

            return True
        except (IOError, OSError, json.JSONDecodeError) as e:
            warnings.warn(f"Failed to save FAISS index: {str(e)}")
            return False

    def load_index(self, path: str) -> bool:
        """Load index from file.

        Args:
            path: Path to load index from

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            warnings.warn("FAISS backend not available")
            return False

        try:
            # Load FAISS index
            if self.faiss is not None and hasattr(self.faiss, 'read_index'):
                try:
                    # Use type narrowing with try/except
                    if hasattr(self.faiss, 'read_index'):
                        self.index = self.faiss.read_index(path)  # type: ignore[attr-defined]
                except (AttributeError, TypeError):
                    warnings.warn("FAISS read_index method failed")
                    return False
            else:
                warnings.warn("FAISS read_index method not available")
                return False

            # Load metadata
            metadata_path = path + ".metadata.json"
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

            return True
        except (IOError, OSError, json.JSONDecodeError) as e:
            warnings.warn(f"Failed to load FAISS index: {str(e)}")
            return False

    def get_index_size(self) -> int:
        """Get number of vectors in index.

        Returns:
            Number of vectors in index
        """
        if not self.available:
            return 0
        if self.index is not None and hasattr(self.index, 'ntotal'):
            return self.index.ntotal  # type: ignore[attr-defined]
        return 0

    def clear_index(self) -> None:
        """Clear the index."""
        if self.available and self.index is not None and hasattr(self.index, 'reset'):
            self.index.reset()  # type: ignore[attr-defined]
            self.metadata = []


class SimilaritySearchManager:
    """Manager for similarity search backends.

    Responsibilities:
    - Backend selection and management
    - Graceful fallback
    - Index coordination
    - Error handling
    """

    def __init__(self):
        """Initialize similarity search manager."""
        self.backends: Dict[str, SimilarityBackend] = {}
        self.current_backend: Optional[SimilarityBackend] = None

    def add_backend(self, name: str, backend: SimilarityBackend) -> None:
        """Add a similarity backend.

        Args:
            name: Backend name
            backend: Backend instance
        """
        self.backends[name] = backend

    def set_backend(self, name: str) -> bool:
        """Set the current backend.

        Args:
            name: Backend name

        Returns:
            True if successful, False otherwise
        """
        if name in self.backends:
            self.current_backend = self.backends[name]
            return True
        return False

    def get_backend(self, name: str) -> Optional[SimilarityBackend]:
        """Get a backend by name.

        Args:
            name: Backend name

        Returns:
            Backend instance or None
        """
        return self.backends.get(name)

    def get_current_backend(self) -> Optional[SimilarityBackend]:
        """Get the current backend.

        Returns:
            Current backend instance or None
        """
        return self.current_backend

    def add_vectors(self,
                    vectors: List[List[float]],
                    metadata: List[Dict[str,
                                        Any]]) -> bool:
        """Add vectors to the current backend.

        Args:
            vectors: List of vectors to add
            metadata: List of metadata dictionaries

        Returns:
            True if successful, False otherwise
        """
        if self.current_backend:
            return self.current_backend.add_vectors(vectors, metadata)
        return False

    def search(self,
               query_vector: List[float],
               k: int = 5,
               threshold: float = 0.8) -> List[Tuple[Dict[str,
                                               Any],
                                                     float]]:
        """Search for similar vectors using current backend.

        Args:
            query_vector: Query vector
            k: Number of results to return
            threshold: Similarity threshold

        Returns:
            List of (metadata, similarity_score) tuples
        """
        if self.current_backend:
            return self.current_backend.search(query_vector, k, threshold)
        return []

    def save_index(self, path: str) -> bool:
        """Save current backend index.

        Args:
            path: Path to save index

        Returns:
            True if successful, False otherwise
        """
        if self.current_backend:
            return self.current_backend.save_index(path)
        return False

    def load_index(self, path: str) -> bool:
        """Load index into current backend.

        Args:
            path: Path to load index from

        Returns:
            True if successful, False otherwise
        """
        if self.current_backend:
            return self.current_backend.load_index(path)
        return False


def create_similarity_manager() -> SimilaritySearchManager:
    """Create and return a SimilaritySearchManager instance.

    Returns:
        SimilaritySearchManager instance
    """
    return SimilaritySearchManager()


def create_brute_force_backend(dimensions: int) -> BruteForceBackend:
    """Create and return a BruteForceBackend instance.

    Args:
        dimensions: Number of dimensions for vectors

    Returns:
        BruteForceBackend instance
    """
    return BruteForceBackend(dimensions)


def create_faiss_backend(dimensions: int) -> FaissBackend:
    """Create and return a FaissBackend instance.

    Args:
        dimensions: Number of dimensions for vectors

    Returns:
        FaissBackend instance
    """
    return FaissBackend(dimensions)
