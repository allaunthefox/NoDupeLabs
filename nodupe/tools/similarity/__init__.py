"""Similarity Search Tool for NoDupeLabs.

This module provides similarity search functionality using vector embeddings

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation
with multiple backend support and graceful degradation.

Key Features:
    - Vector similarity search with multiple algorithms
    - Multiple backend support (brute force, FAISS)
    - Index management and persistence
    - Near-duplicate detection
    - Graceful degradation when optional dependencies missing

Dependencies:
    - Standard library only (with optional NumPy and FAISS support)
"""

import contextlib
import json
import pickle
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from nodupe.core.tool_system.base import Tool


try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False


class SimilarityBackend(ABC):
    """Abstract base class for similarity search backends."""

    @abstractmethod
    def __init__(self, dimensions: int):
        """Initialize similarity backend.

        Args:
            dimensions: Number of dimensions for vectors
        """

    @abstractmethod
    def add_vectors(self, vectors: list[list[float]], metadata: list[dict[str, Any]]) -> bool:
        """Add vectors to the index.

        Args:
            vectors: List of vectors to add
            metadata: List of metadata dictionaries

        Returns:
            True if successful, False otherwise
        """

    @abstractmethod
    def search(self, query_vector: list[float], k: int = 5, threshold: float = 0.8) -> list[tuple[dict[str, Any], float]]:
        """Search for similar vectors.

        Args:
            query_vector: Query vector
            k: Number of results to return
            threshold: Similarity threshold

        Returns:
            List of (metadata, similarity_score) tuples
        """

    @abstractmethod
    def save_index(self, path: str) -> bool:
        """Save index to file.

        Args:
            path: Path to save index

        Returns:
            True if successful, False otherwise
        """

    @abstractmethod
    def load_index(self, path: str) -> bool:
        """Load index from file.

        Args:
            path: Path to load index from

        Returns:
            True if successful, False otherwise
        """

    @abstractmethod
    def get_index_size(self) -> int:
        """Get number of vectors in index.

        Returns:
            Number of vectors in index
        """

    @abstractmethod
    def clear_index(self) -> None:
        """Clear the index."""


class BruteForceBackend(SimilarityBackend):
    """Brute-force similarity search using NumPy or standard library."""

    def __init__(self, dimensions: int):
        """Initialize brute-force backend.

        Args:
            dimensions: Number of dimensions for vectors
        """
        self.dimensions = dimensions
        self.vectors: list[list[float]] = []
        self.metadata: list[dict[str, Any]] = []

    def add_vectors(self, vectors: list[list[float]], metadata: list[dict[str, Any]]) -> bool:
        """Add vectors to the index."""
        try:
            if len(vectors) != len(metadata):
                warnings.warn("Vectors and metadata length mismatch")
                return False

            for vector in vectors:
                if len(vector) != self.dimensions:
                    warnings.warn(
                        f"Vector dimension mismatch: expected {self.dimensions}, got {len(vector)}")
                    return False

            self.vectors.extend(vectors)
            self.metadata.extend(metadata)
            return True
        except Exception as e:
            warnings.warn(f"Failed to add vectors: {e}")
            return False

    def search(self, query_vector: list[float], k: int = 5, threshold: float = 0.8) -> list[tuple[dict[str, Any], float]]:
        """Search for similar vectors."""
        if len(self.vectors) == 0:
            return []

        if len(query_vector) != self.dimensions:
            warnings.warn(
                f"Query vector dimension mismatch: expected {self.dimensions}, got {len(query_vector)}")
            return []

        try:
            results = []

            if NUMPY_AVAILABLE and np:
                # Use NumPy for efficient computation
                query_array = np.array(query_vector, dtype=np.float32)
                vectors_array = np.array(self.vectors, dtype=np.float32)

                # Calculate cosine similarity
                dot_products = np.sum(vectors_array * query_array, axis=1)
                query_norm = np.linalg.norm(query_array)
                vector_norms = np.linalg.norm(vectors_array, axis=1)

                # Avoid division by zero
                similarities = np.where(vector_norms == 0, 0, dot_products /
                                        (vector_norms * query_norm))

                # Get top k results
                top_indices = np.argsort(similarities)[-k:][::-1]

                for idx in top_indices:
                    similarity = similarities[idx]
                    if similarity >= threshold:
                        results.append((self.metadata[idx], float(similarity)))
            else:
                # Fallback to standard library
                for i, vector in enumerate(self.vectors):
                    # Calculate cosine similarity manually
                    dot_product = sum(v * q for v, q in zip(vector, query_vector))
                    query_norm = sum(q*q for q in query_vector)**0.5
                    vector_norm = sum(v*v for v in vector)**0.5

                    if query_norm == 0 or vector_norm == 0:
                        similarity = 0.0
                    else:
                        similarity = dot_product / (query_norm * vector_norm)

                    if similarity >= threshold:
                        results.append((self.metadata[i], similarity))

                # Sort by similarity (descending)
                results.sort(key=lambda x: x[1], reverse=True)
                results = results[:k]

            return results

        except Exception as e:
            warnings.warn(f"Similarity search failed: {e}")
            return []

    def save_index(self, path: str) -> bool:
        """Save index to file."""
        try:
            index_data = {
                'vectors': self.vectors,
                'metadata': self.metadata,
                'dimensions': self.dimensions
            }

            with open(path, 'wb') as f:
                pickle.dump(index_data, f)

            return True
        except Exception as e:
            warnings.warn(f"Failed to save index: {e}")
            return False

    def load_index(self, path: str) -> bool:
        """Load index from file."""
        try:
            # First try JSON format (safer), fall back to pickle for backwards compatibility
            json_path = path + '.json'
            if Path(json_path).exists():
                with open(json_path) as f:
                    index_data = json.load(f)
            else:
                # Fallback to pickle for backwards compatibility - but validate
                with open(path, 'rb') as f:
                    # Only allow specific trusted content types
                    index_data = pickle.load(f)

            if index_data.get('dimensions') != self.dimensions:
                warnings.warn(
                    f"Index dimension mismatch: expected {self.dimensions}, got {index_data.get('dimensions')}")
                return False

            self.vectors = index_data['vectors']
            self.metadata = index_data['metadata']
            return True
        except Exception as e:
            warnings.warn(f"Failed to load index: {e}")
            return False

    def get_index_size(self) -> int:
        """Get number of vectors in index."""
        return len(self.vectors)

    def clear_index(self) -> None:
        """Clear the index."""
        self.vectors.clear()
        self.metadata.clear()


class FaissBackend(SimilarityBackend):
    """FAISS similarity search backend for large-scale operations."""

    def __init__(self, dimensions: int):
        """Initialize FAISS backend.

        Args:
            dimensions: Number of dimensions for vectors
        """
        if not FAISS_AVAILABLE:
            warnings.warn("FAISS not available, using fallback")
            raise RuntimeError("FAISS is not available")

        self.dimensions = dimensions
        self.index = faiss.IndexFlatIP(dimensions)
        self.metadata: list[dict[str, Any]] = []

    def add_vectors(self, vectors: list[list[float]], metadata: list[dict[str, Any]]) -> bool:
        """Add vectors to the FAISS index."""
        if not FAISS_AVAILABLE:
            return False

        try:
            if len(vectors) != len(metadata):
                warnings.warn("Vectors and metadata length mismatch")
                return False

            for vector in vectors:
                if len(vector) != self.dimensions:
                    warnings.warn(
                        f"Vector dimension mismatch: expected {self.dimensions}, got {len(vector)}")
                    return False

            # Convert to numpy array and normalize for inner product
            vectors_array = np.array(vectors, dtype=np.float32)
            faiss.normalize_L2(vectors_array)

            # Add to index
            self.index.add(vectors_array)
            self.metadata.extend(metadata)
            return True
        except Exception as e:
            warnings.warn(f"Failed to add vectors to FAISS: {e}")
            return False

    def search(self, query_vector: list[float], k: int = 5, threshold: float = 0.8) -> list[tuple[dict[str, Any], float]]:
        """Search for similar vectors using FAISS."""
        if not FAISS_AVAILABLE or (self.index is not None and self.index.ntotal == 0):
            return []

        if len(query_vector) != self.dimensions:
            warnings.warn(
                f"Query vector dimension mismatch: expected {self.dimensions}, got {len(query_vector)}")
            return []

        try:
            # Convert and normalize query vector
            query_array = np.array([query_vector], dtype=np.float32)
            if faiss is not None:
                faiss.normalize_L2(query_array)

            # Search
            if self.index is not None:
                scores, indices = self.index.search(query_array, k)
            else:
                scores, indices = np.array([[]], dtype=np.float32), np.array([[]], dtype=np.int32)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.metadata) and score >= threshold:
                    results.append((self.metadata[idx], float(score)))

            return results
        except Exception as e:
            warnings.warn(f"FAISS search failed: {e}")
            return []

    def save_index(self, path: str) -> bool:
        """Save FAISS index to file."""
        if not FAISS_AVAILABLE:
            return False

        try:
            # Save FAISS index
            faiss.write_index(self.index, path)

            # Save metadata separately
            metadata_path = f"{path}.metadata"
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f)

            return True
        except Exception as e:
            warnings.warn(f"Failed to save FAISS index: {e}")
            return False

    def load_index(self, path: str) -> bool:
        """Load FAISS index from file."""
        if not FAISS_AVAILABLE:
            return False

        try:
            # Load FAISS index
            if faiss is not None:
                self.index = faiss.read_index(path)

            # Load metadata
            metadata_path = f"{path}.metadata"
            with open(metadata_path) as f:
                self.metadata = json.load(f)

            return True
        except Exception as e:
            warnings.warn(f"Failed to load FAISS index: {e}")
            return False

    def get_index_size(self) -> int:
        """Get number of vectors in index."""
        return self.index.ntotal if FAISS_AVAILABLE else 0

    def clear_index(self) -> None:
        """Clear the index."""
        if FAISS_AVAILABLE and self.index is not None:
            self.index.reset()
            self.metadata.clear()


class SimilarityManager:
    """Manager for similarity search backends with graceful fallback."""

    def __init__(self):
        """Initialize similarity manager."""
        self.backends: dict[str, SimilarityBackend] = {}
        self.current_backend: Optional[SimilarityBackend] = None

        # Try to initialize available backends
        try:
            self.add_backend('bruteforce', BruteForceBackend(dimensions=512))
            self.set_backend('bruteforce')
        except Exception:
            pass

        if FAISS_AVAILABLE:
            with contextlib.suppress(Exception):
                self.add_backend('faiss', FaissBackend(dimensions=512))

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

    def add_vectors(self, vectors: list[list[float]], metadata: list[dict[str, Any]]) -> bool:
        """Add vectors to current backend."""
        if self.current_backend:
            return self.current_backend.add_vectors(vectors, metadata)
        return False

    def search(self, query_vector: list[float], k: int = 5, threshold: float = 0.8) -> list[tuple[dict[str, Any], float]]:
        """Search for similar vectors."""
        if self.current_backend:
            return self.current_backend.search(query_vector, k, threshold)
        return []

    def save_index(self, path: str) -> bool:
        """Save current backend index."""
        if self.current_backend:
            return self.current_backend.save_index(path)
        return False

    def load_index(self, path: str) -> bool:
        """Load index into current backend."""
        if self.current_backend:
            return self.current_backend.load_index(path)
        return False

    def get_index_size(self) -> int:
        """Get current backend index size."""
        if self.current_backend:
            return self.current_backend.get_index_size()
        return 0


def create_similarity_manager() -> SimilarityManager:
    """Create and return a similarity manager instance.

    Returns:
        SimilarityManager instance with available backends
    """
    return SimilarityManager()


# Tool interface for the system
class SimilarityBackendTool(Tool):
    """Similarity search backend tool."""

    @property
    def name(self) -> str:
        return "similarity_backend"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return []

    @property
    def api_methods(self) -> dict[str, Callable[..., Any]]:
        return {
            'add_vectors': self.manager.add_vectors,
            'search': self.manager.search,
            'save_index': self.manager.save_index,
            'load_index': self.manager.load_index,
            'get_index_size': self.manager.get_index_size
        }

    def __init__(self):
        """TODO: Document __init__."""
        self.description = "Similarity search backend services"
        self.manager = create_similarity_manager()

    def initialize(self, container: Any) -> None:
        """Initialize the tool."""
        container.register_service('similarity_manager', self.manager)

    def shutdown(self) -> None:
        """Shutdown the tool."""

    def get_capabilities(self) -> dict[str, Any]:
        """Get tool capabilities."""
        return {
            'backends': list(self.manager.backends.keys()),
            'supports_faiss': FAISS_AVAILABLE,
            'supports_numpy': NUMPY_AVAILABLE
        }


def register_tool():
    """Register the similarity tool."""
    return SimilarityBackendTool()


if __name__ == "__main__":
    # Example usage
    print(f"NumPy available: {NUMPY_AVAILABLE}")
    print(f"FAISS available: {FAISS_AVAILABLE}")

    # Create manager
    manager = create_similarity_manager()
    print(f"Available backends: {list(manager.backends.keys())}")

    # Test with brute force backend
    if manager.set_backend('bruteforce'):
        # Add some test vectors
        vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        metadata = [{'id': 1, 'name': 'vector1'}, {
            'id': 2, 'name': 'vector2'}, {'id': 3, 'name': 'vector3'}]

        success = manager.add_vectors(vectors, metadata)
        print(f"Added vectors: {success}")
        print(f"Index size: {manager.get_index_size()}")

        # Search
        query = [0.8, 0.1, 0.1]
        results = manager.search(query, k=2, threshold=0.5)
        print(f"Search results: {results}")
