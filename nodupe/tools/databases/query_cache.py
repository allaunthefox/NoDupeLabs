"""Query Cache Module.

Query result caching using standard library only.

Key Features:
    - In-memory query result caching with TTL
    - Query parameter and result validation
    - Thread-safe operations
    - Cache size limits and eviction policies
    - Query normalization and deduplication
    - Standard library only (no external dependencies)

Dependencies:
    - threading (standard library)
    - time (standard library)
    - typing (standard library)
    - hashlib (standard library)
    - json (standard library)
"""

import threading
import time
from typing import Optional, Dict, Any, Tuple, List
from collections import OrderedDict
import hashlib
import json


class QueryCacheError(Exception):
    """Query cache operation error"""


class QueryCache:
    """Handle query result caching operations.

    Provides caching of query results with validation, TTL expiration,
    and configurable cache size limits.
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600
    ):
        """Initialize query cache.

        Args:
            max_size: Maximum number of entries in cache
            ttl_seconds: Time-to-live in seconds for cache entries
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        # Cache storage: query_key -> (result, timestamp)
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        # Add ttl_expiries and ensure counters exist for metrics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "insertions": 0,
            "ttl_expiries": 0,
        }

    def get_result
    def get_result(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Get cached result for a query.

        Args:
            query: Query string
            params: Query parameters

        Returns:
            Cached result or None if not found/cached
        """
        with self._lock:
            query_key = self._generate_key(query, params)

            if query_key not in self._cache:
                self._stats['misses'] += 1
                return None

            result, timestamp = self._cache[query_key]

            # Check if entry is expired
            if time.monotonic() - timestamp > self.ttl_seconds:
                del self._cache[query_key]
# track TTL-driven expirations separately
                self._stats["ttl_expiries"] += 1
                self._stats["misses"] += 1
                return None

            # ACCESS-LRU: mark this entry as recently used on read
            try:
                self._cache.move_to_end(query_key, last=True)
            except Exception:
                # non-critical — keep serving result
                pass

            self._stats["hits"] += 1
            return result

    def set_result(self, query: str, params: Optional[Dict[str, Any]] = None, result: Any = None) -> None:
        """Set result for a query in cache.

        Args:
            query: Query string
            params: Query parameters
            result: Query result to cache
        """
        with self._lock:
            query_key = self._generate_key(query, params)

            # Remove oldest entry if at max size
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._stats['evictions'] += 1

            # Store with current timestamp
            timestamp = time.monotonic()
            self._cache[query_key] = (result, timestamp)

            # Move to end to mark as most recently used
            self._cache.move_to_end(query_key, last=True)

            self._stats['insertions'] += 1

    def invalidate(self, query: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Invalidate cache entry for a query.

        Args:
            query: Query string
            params: Query parameters

        Returns:
            True if entry was invalidated, False if not found
        """
        with self._lock:
            query_key = self._generate_key(query, params)
            if query_key in self._cache:
                del self._cache[query_key]
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

    def invalidate_by_prefix(self, prefix: str) -> int:
        """Invalidate all cache entries with a specific prefix.

        Args:
            prefix: Prefix to match

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = []
            for key in self._cache.keys():
                if key.startswith(prefix):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._cache[key]
                self._stats['evictions'] += 1

            return len(keys_to_remove)

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
            for query_key, (result, timestamp) in self._cache.items():
                # Check TTL expiration
                if current_time - timestamp > self.ttl_seconds:
                    keys_to_remove.append(query_key)

            # Remove stale entries
            for query_key in keys_to_remove:
                del self._cache[query_key]
                removed_count += 1
                self._stats["ttl_expiries"] += 1

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

    def is_cached(self, query: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a query result is cached and valid.

        Args:
            query: Query string
            params: Query parameters

        Returns:
            True if query result is cached and valid
        """
        return self.get_result(query, params) is not None

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
            # Rough estimate: query_key string + result + timestamp + overhead
            usage = 0
            for query_key, (result, timestamp) in self._cache.items():
                usage += len(query_key.encode('utf-8'))  # Query key
                # Estimate result size (this is a rough approximation)
                try:
                    result_str = str(result)
                    usage += len(result_str.encode('utf-8'))
                except:
                    usage += 100  # Default estimate if conversion fails
                usage += 8  # Timestamp (float)
                usage += 50  # Overhead per entry

            return usage

    def _generate_key(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate a unique cache key for a query and parameters.

        Args:
            query: Query string
            params: Query parameters

        Returns:
            Unique cache key
        """
        # Normalize query (remove extra whitespace, convert to lowercase)
        normalized_query = ' '.join(query.split()).lower()

        # Create parameter string if params exist
        if params:
            # Sort parameters by key for consistency
            sorted_params = sorted(params.items())
            params_str = json.dumps(sorted_params, sort_keys=True, default=str)
            # Create hash of parameters to keep key manageable
            params_hash = hashlib.md5(params_str.encode()).hexdigest()
            return f"{normalized_query}:{params_hash}"
        else:
            return f"{normalized_query}:none"

    def clear_by_query_pattern(self, pattern: str) -> int:
        """Clear cache entries that match a query pattern.

        Args:
            pattern: Pattern to match in query strings

        Returns:
            Number of entries cleared
        """
        with self._lock:
            keys_to_remove = []
            for key in self._cache.keys():
                # Extract query part from key (before the last colon)
                query_part = key.rsplit(':', 1)[0] if ':' in key else key
                if pattern.lower() in query_part.lower():
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._cache[key]
                self._stats['evictions'] += 1

            return len(keys_to_remove)

    def get_cached_queries(self) -> List[str]:
        """Get list of cached query patterns.

        Returns:
            List of cached query patterns
        """
        with self._lock:
            queries = []
            for key in self._cache.keys():
                query_part = key.rsplit(':', 1)[0] if ':' in key else key
                if query_part not in queries:
                    queries.append(query_part)
            return queries


def create_query_cache(
    max_size: int = 1000,
    ttl_seconds: int = 3600
) -> QueryCache:
    """Create a query cache instance.

    Args:
        max_size: Maximum number of entries
        ttl_seconds: Time-to-live in seconds

    Returns:
        QueryCache instance
    """
    return QueryCache(max_size, ttl_seconds)
