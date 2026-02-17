"""Hash Cache Module.

File hash caching using standard library only.

Key Features:
    - In-memory hash caching with TTL
    - File path and modification time validation
    - Thread-safe operations
    - Cache size limits and eviction policies
    - Persistent storage support
    - Standard library only (no external dependencies)

Dependencies:
    - threading (standard library)
    - time (standard library)
    - typing (standard library)
    - pathlib (standard library)
    - collections (standard library)
"""

import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional


class HashCacheError(Exception):
    """Hash cache operation error"""


class HashCache:
    """Handle file hash caching operations.

    Provides caching of file hashes with validation, TTL expiration,
    and configurable cache size limits.
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        enable_persistence: bool = False,
    ):
        """Initialize hash cache.

        Args:
            max_size: Maximum number of entries in cache
            ttl_seconds: Time-to-live in seconds for cache entries
            enable_persistence: Enable persistent storage (future)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.enable_persistence = enable_persistence

        # Cache storage: path -> (hash_value, mtime, timestamp)
        self._cache: OrderedDict[str, tuple[str, float, float]] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "insertions": 0}

    def get_hash(self, file_path: Path) -> Optional[str]:
        """Get cached hash for a file.

        Args:
            file_path: Path to file

        Returns:
            Cached hash value or None if not found/cached
        """
        with self._lock:
            path_str = str(file_path)

            if path_str not in self._cache:
                self._stats["misses"] += 1
                return None

            hash_value, stored_mtime, timestamp = self._cache[path_str]

            # Check if entry is expired
            if time.monotonic() - timestamp > self.ttl_seconds:
                del self._cache[path_str]
                self._stats["misses"] += 1
                return None

            # Check if file has been modified since caching
            try:
                current_mtime = file_path.stat().st_mtime
                if current_mtime != stored_mtime:
                    del self._cache[path_str]
                    self._stats["misses"] += 1
                    return None
            except OSError:
                # File no longer exists, remove from cache
                del self._cache[path_str]
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return hash_value

    def set_hash(self, file_path: Path, hash_value: str) -> None:
        """Set hash for a file in cache.

        Args:
            file_path: Path to file
            hash_value: Hash value to cache
        """
        with self._lock:
            path_str = str(file_path)

            try:
                mtime = file_path.stat().st_mtime
            except OSError:
                # File doesn't exist, don't cache
                return

            # Remove oldest entry if at max size
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._stats["evictions"] += 1

            # Store with current timestamp
            timestamp = time.monotonic()
            self._cache[path_str] = (hash_value, mtime, timestamp)

            # Move to end to mark as most recently used
            self._cache.move_to_end(path_str, last=True)

            self._stats["insertions"] += 1

    def invalidate(self, file_path: Path) -> bool:
        """Invalidate cache entry for a file.

        Args:
            file_path: Path to file to invalidate

        Returns:
            True if entry was invalidated, False if not found
        """
        with self._lock:
            path_str = str(file_path)
            if path_str in self._cache:
                del self._cache[path_str]
                return True
            return False

    def invalidate_all(self) -> None:
        """Invalidate all cache entries."""
        with self._lock:
            # Count the number of entries being cleared
            num_entries = len(self._cache)
            self._cache.clear()
            # Increment evictions by the number of entries that were cleared
            self._stats["evictions"] += num_entries

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
            for path_str, (
                hash_value,
                stored_mtime,
                timestamp,
            ) in self._cache.items():
                # Check TTL expiration
                if current_time - timestamp > self.ttl_seconds:
                    keys_to_remove.append(path_str)
                    continue

                # Check file modification
                try:
                    file_path = Path(path_str)
                    current_mtime = file_path.stat().st_mtime
                    if current_mtime != stored_mtime:
                        keys_to_remove.append(path_str)
                except OSError:
                    # File no longer exists
                    keys_to_remove.append(path_str)

            # Remove stale entries
            for path_str in keys_to_remove:
                del self._cache[path_str]
                removed_count += 1

            return removed_count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        with self._lock:
            stats = self._stats.copy()
            stats["size"] = len(self._cache)
            stats["capacity"] = self.max_size
            stats["hit_rate"] = (
                stats["hits"] / (stats["hits"] + stats["misses"])
                if (stats["hits"] + stats["misses"]) > 0
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

    def is_cached(self, file_path: Path) -> bool:
        """Check if a file is cached and valid.

        Args:
            file_path: Path to file

        Returns:
            True if file is cached and valid
        """
        return self.get_hash(file_path) is not None

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
                self._stats["evictions"] += 1

    def get_memory_usage(self) -> int:
        """Get approximate memory usage of cache.

        Returns:
            Approximate memory usage in bytes
        """
        with self._lock:
            # Rough estimate: path string + hash string + timestamps + overhead
            usage = 0
            for path_str, (
                hash_value,
                stored_mtime,
                timestamp,
            ) in self._cache.items():
                usage += len(path_str.encode("utf-8"))  # Path
                usage += len(hash_value.encode("utf-8"))  # Hash
                usage += 16  # Two floats (mtime, timestamp)
                usage += 50  # Overhead per entry

            return usage


def create_hash_cache(
    max_size: int = 1000,
    ttl_seconds: int = 3600,
    enable_persistence: bool = False,
) -> HashCache:
    """Create a hash cache instance.

    Args:
        max_size: Maximum number of entries
        ttl_seconds: Time-to-live in seconds
        enable_persistence: Enable persistent storage

    Returns:
        HashCache instance
    """
    return HashCache(max_size, ttl_seconds, enable_persistence)
