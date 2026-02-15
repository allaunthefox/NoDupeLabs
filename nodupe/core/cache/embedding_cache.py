"""Embedding Cache Module.

Embedding vector caching using standard library only.

Key Features:
    - In-memory embedding vector caching with TTL
    - Vector similarity and distance calculations
    - Thread-safe operations
    - Cache size limits and eviction policies
    - Vector dimension validation
    - Standard library only (no external dependencies)

Dependencies:
    - threading (standard library)
    - time (standard library)
    - typing (standard library)
    - hashlib (standard library)
    - array (standard library)
"""

import threading
import time
from typing import Optional, Dict, Any, Tuple, List
from collections import OrderedDict


class EmbeddingCacheError(Exception):
    """Embedding cache operation error"""


class EmbeddingCache:
    """Handle embedding vector caching operations.

    Provides caching of embedding vectors with validation, TTL expiration,
    and configurable cache size limits.
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        max_dimensions: int = 1024
    ):
        """Initialize embedding cache.

        Args:
            max_size: Maximum number of entries in cache
            ttl_seconds: Time-to-live in seconds for cache entries
            max_dimensions: Maximum vector dimensions allowed
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.max_dimensions = max_dimensions

        # Cache storage: key -> (embedding_vector, timestamp)
        self._cache: OrderedDict[str, Tuple[List[float], float]] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'insertions': 0
        }

    def get_embedding(self, key: str) -> Optional[List[float]]:
        """Get cached embedding vector.

        Args:
            key: Cache key

        Returns:
            Cached embedding vector or None if not found/cached
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None

            embedding, timestamp = self._cache[key]

            # Check if entry is expired
            if time.monotonic() - timestamp > self.ttl_seconds:
                del self._cache[key]
                self._stats['misses'] += 1
                return None

            self._stats['hits'] += 1
            return embedding

    def set_embedding(self, key: str, embedding: List[float]) -> None:
        """Set embedding vector in cache.

        Args:
            key: Cache key
            embedding: Embedding vector to cache
        """
        with self._lock:
            # Validate embedding dimensions
            if len(embedding) > self.max_dimensions:
                raise EmbeddingCacheError(
                    f"Embedding dimensions {len(embedding)} exceed maximum {self.max_dimensions}"
                )

            # Remove oldest entry if at max size
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._stats['evictions'] += 1

            # Store with current timestamp
            timestamp = time.monotonic()
            self._cache[key] = (embedding, timestamp)

            # Move to end to mark as most recently used
            self._cache.move_to_end(key, last=True)

            self._stats['insertions'] += 1

    def calculate_similarity(self, key1: str, key2: str) -> Optional[float]:
        """Calculate cosine similarity between two cached embeddings.

        Args:
            key1: First embedding key
            key2: Second embedding key

        Returns:
            Cosine similarity (0.0 to 1.0) or None if either not cached
        """
        emb1 = self.get_embedding(key1)
        emb2 = self.get_embedding(key2)

        if emb1 is None or emb2 is None:
            return None

        return self._cosine_similarity(emb1, emb2)

    def invalidate(self, key: str) -> bool:
        """Invalidate cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was invalidated, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def invalidate_all(self) -> None:
        """Invalidate all cache entries."""
        with self._lock:
            # Count the number of entries being cleared
            num_entries = len(self._cache)
            self._cache.clear()
            # Increment evictions by the number of entries that were cleared
            self._stats['evictions'] += num_entries

    def validate_cache(self) -> int:
        """Validate all cache entries and remove stale ones.

        Returns:
            Number of entries removed
        """
        with self._lock:
            removed_count = 0
            current_time = time.monotonic()

            # Collect keys to remove
            keys_to_remove = []
            for cache_key, (_embedding, _timestamp) in self._cache.items():
                # Check TTL expiration
                if current_time - timestamp > self.ttl_seconds:
                    keys_to_remove.append(cache_key)

            # Remove stale entries
            for cache_key in keys_to_remove:
                del self._cache[cache_key]
                removed_count += 1

            return removed_count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        with self._lock:
            stats = self._stats.copy()
            stats['size'] = len(self._cache)
            stats['capacity'] = self.max_size
            stats['hit_rate'] = (
                stats['hits'] / (stats['hits'] + stats['misses'])
                if (stats['hits'] + stats['misses']) > 0
                else 0.0
            )
            return stats

    def get_cache_size(self) -> int:
        """Get current cache size.

        Returns:
            Number of entries in cache
        """
        with self._lock:
            return len(self._cache)

    def is_cached(self, key: str) -> bool:
        """Check if an embedding is cached and valid.

        Args:
            key: Cache key

        Returns:
            True if embedding is cached and valid
        """
        return self.get_embedding(key) is not None

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        return self.validate_cache()

    def resize(self, new_max_size: int) -> None:
        """Resize cache and evict excess entries if necessary.

        Args:
            new_max_size: New maximum cache size
        """
        with self._lock:
            self.max_size = new_max_size

            # Remove excess entries from the beginning (LRU)
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
                self._stats['evictions'] += 1

    def get_memory_usage(self) -> int:
        """Get approximate memory usage of cache.

        Returns:
            Approximate memory usage in bytes
        """
        with self._lock:
            # Rough estimate: key string + embedding array + timestamp + overhead
            usage = 0
            for key, (embedding, timestamp) in self._cache.items():
                usage += len(key.encode('utf-8'))  # Key
                usage += len(embedding) * 8  # Float array (8 bytes per float)
                usage += 8  # Timestamp (float)
                usage += 50  # Overhead per entry

            return usage

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        if len(vec1) != len(vec2):
            raise EmbeddingCacheError("Vector dimensions must match for similarity calculation")

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        # Calculate cosine similarity
        similarity = dot_product / (mag1 * mag2)

        # Clamp to [0, 1] range (handle floating point precision issues)
        return max(0.0, min(1.0, similarity))

    def find_similar(
        self,
        key: str,
        threshold: float = 0.8,
        max_results: int = 10
    ) -> List[Tuple[str, float]]:
        """Find similar embeddings to a cached embedding.

        Args:
            key: Reference embedding key
            threshold: Minimum similarity threshold
            max_results: Maximum number of results to return

        Returns:
            List of (key, similarity) tuples sorted by similarity descending
        """
        reference__embedding = self.get_embedding(key)
        if reference_embedding is None:
            return []

        similarities = []
        with self._lock:
            for cache_key, (embedding, _) in self._cache.items():
                if cache_key == key:
                    continue  # Skip self

                similarity = self._cosine_similarity(reference_embedding, embedding)
                if similarity >= threshold:
                    similarities.append((cache_key, similarity))

        # Sort by similarity descending and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:max_results]

    def get_average_embedding(self, keys: List[str]) -> Optional[List[float]]:
        """Get average embedding from multiple cached embeddings.

        Args:
            keys: List of cache keys

        Returns:
            Average embedding vector or None if none found
        """
        embeddings = []
        for key in keys:
            _embedding = self.get_embedding(key)
            if embedding is not None:
                embeddings.append(embedding)

        if not embeddings:
            return None

        # Calculate average
        avg__embedding = []
        num_embeddings = len(embeddings)

        # Get dimension from first embedding
        if not embeddings:
            return None

        dim = len(embeddings[0])

        for i in range(dim):
            avg_value = sum(embedding[i] for embedding in embeddings) / num_embeddings
            avg_embedding.append(avg_value)

        return avg_embedding

    def clear_by_pattern(self, pattern: str) -> int:
        """Clear cache entries that match a pattern.

        Args:
            pattern: Pattern to match in keys

        Returns:
            Number of entries cleared
        """
        with self._lock:
            keys_to_remove = []
            for key in self._cache.keys():
                if pattern.lower() in key.lower():
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._cache[key]
                self._stats['evictions'] += 1

            return len(keys_to_remove)

    def get_cached_keys(self) -> List[str]:
        """Get list of all cached keys.

        Returns:
            List of cached keys
        """
        with self._lock:
            return list(self._cache.keys())


def create_embedding_cache(
    max_size: int = 1000,
    ttl_seconds: int = 3600,
    max_dims: int = 1024
) -> EmbeddingCache:
    """Create an embedding cache instance.

    Args:
        max_size: Maximum number of entries
        ttl_seconds: Time-to-live in seconds
        max_dims: Maximum vector dimensions

    Returns:
        EmbeddingCache instance
    """
    return EmbeddingCache(max_size, ttl_seconds, max_dims)
