"""Tests for query cache module."""

import time

from nodupe.tools.databases.query_cache import QueryCache, QueryCacheError


class TestQueryCache:
    """Test QueryCache class."""

    def test_query_cache_initialization(self):
        """Test query cache initialization."""
        cache = QueryCache(max_size=100, ttl_seconds=1800)
        assert cache.max_size == 100
        assert cache.ttl_seconds == 1800
        assert cache.get_cache_size() == 0
        assert cache.get_stats()["size"] == 0

    def test_set_and_get_result(self):
        """Test setting and getting query results."""
        cache = QueryCache()

        # Set result for a query
        query = "SELECT * FROM users WHERE id = ?"
        params = {"id": 1}
        expected_result = [{"id": 1, "name": "John"}]

        cache.set_result(query, params, expected_result)

        # Get the result back
        retrieved_result = cache.get_result(query, params)
        assert retrieved_result == expected_result

    def test_get_nonexistent_result(self):
        """Test getting result for non-existent query."""
        cache = QueryCache()

        # Set result for one query
        query1 = "SELECT * FROM users WHERE id = ?"
        params1 = {"id": 1}
        cache.set_result(query1, params1, [{"id": 1, "name": "John"}])

        # Try to get result for a different query
        query2 = "SELECT * FROM orders WHERE user_id = ?"
        params2 = {"user_id": 1}
        result = cache.get_result(query2, params2)
        assert result is None

    def test_cache_ttl_expiration(self):
        """Test cache entry expiration based on TTL."""
        cache = QueryCache(ttl_seconds=1)  # Very short TTL for testing

        # Set result for a query
        query = "SELECT * FROM users WHERE id = ?"
        params = {"id": 1}
        cache.set_result(query, params, [{"id": 1, "name": "John"}])

        # Verify it's cached
        assert cache.get_result(query, params) == [{"id": 1, "name": "John"}]

        # Wait for TTL to expire
        time.sleep(1.2)

        # Verify it's no longer cached
        assert cache.get_result(query, params) is None

    def test_cache_size_limit(self):
        """Test cache size limit and LRU eviction."""
        cache = QueryCache(max_size=2)  # Small cache for testing

        # Fill the cache
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1}])
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 2}, [{"id": 2}])

        # Verify both are cached
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) == [{"id": 1}]
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 2}) == [{"id": 2}]

        # Add a third query, which should evict the least recently used
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 3}, [{"id": 3}])

        # Verify the first query was evicted and others remain
        assert (
            cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) is None
        )  # Should be evicted
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 2}) == [
            {"id": 2}
        ]  # Should still be there
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 3}) == [
            {"id": 3}
        ]  # Should be added

    def test_invalidate_specific_entry(self):
        """Test invalidating a specific cache entry."""
        cache = QueryCache()

        # Set results for two queries
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1}])
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 2}, [{"id": 2}])

        # Verify both are cached
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) == [{"id": 1}]
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 2}) == [{"id": 2}]

        # Invalidate first query
        invalidated = cache.invalidate("SELECT * FROM users WHERE id = ?", {"id": 1})
        assert invalidated is True

        # Verify first query is no longer cached
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) is None
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 2}) == [{"id": 2}]

    def test_invalidate_nonexistent_entry(self):
        """Test invalidating a non-existent cache entry."""
        cache = QueryCache()

        # Try to invalidate non-cached query
        invalidated = cache.invalidate("SELECT * FROM users WHERE id = ?", {"id": 1})
        assert invalidated is False

    def test_invalidate_all_entries(self):
        """Test invalidating all cache entries."""
        cache = QueryCache()

        # Set results for two queries
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1}])
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 2}, [{"id": 2}])

        # Verify both are cached
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) == [{"id": 1}]
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 2}) == [{"id": 2}]

        # Invalidate all entries
        cache.invalidate_all()

        # Verify neither is cached
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) is None
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 2}) is None

    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = QueryCache()

        # Initially, no hits or misses
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

        # Miss - query not in cache
        result = cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1})
        assert result is None

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0
        assert stats["hit_rate"] == 0.0

        # Add to cache
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1}])

        # Hit - query in cache
        result = cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1})
        assert result == [{"id": 1}]

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 1
        assert stats["hit_rate"] == 0.5

    def test_validate_cache_removes_expired(self):
        """Test validate_cache method removes expired entries."""
        cache = QueryCache(ttl_seconds=1)  # Very short TTL

        # Set result for a query
        query = "SELECT * FROM users WHERE id = ?"
        params = {"id": 1}
        cache.set_result(query, params, [{"id": 1}])

        # Verify it's cached
        assert cache.get_result(query, params) == [{"id": 1}]

        # Wait for TTL to expire
        time.sleep(1.2)

        # Validate cache - should remove expired entry
        removed_count = cache.validate_cache()
        assert removed_count == 1

        # Verify it's no longer cached
        assert cache.get_result(query, params) is None

    def test_is_cached_method(self):
        """Test is_cached method."""
        cache = QueryCache()

        # Initially not cached
        assert cache.is_cached("SELECT * FROM users WHERE id = ?", {"id": 1}) is False

        # Add to cache
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1}])

        # Now cached
        assert cache.is_cached("SELECT * FROM users WHERE id = ?", {"id": 1}) is True

        # Remove from cache (by TTL expiration)
        cache.ttl_seconds = 0.1
        time.sleep(1.2)
        assert cache.is_cached("SELECT * FROM users WHERE id = ?", {"id": 1}) is False

    def test_resize_cache(self):
        """Test resizing the cache."""
        cache = QueryCache(max_size=2)

        # Fill the cache
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1}])
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 2}, [{"id": 2}])

        # Verify both are cached
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) == [{"id": 1}]
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 2}) == [{"id": 2}]

        # Add a third query, which should evict one due to size limit
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 3}, [{"id": 3}])

        # Resize to allow more entries
        cache.resize(5)

        # Add the evicted query back
        cache.set_result(
            "SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1, "updated": True}]
        )

        # Verify all three can now be cached
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) == [
            {"id": 1, "updated": True}
        ]
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 2}) == [
            {"id": 2}
        ]  # Should still be there
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 3}) == [
            {"id": 3}
        ]  # Should still be there

    def test_cleanup_expired_method(self):
        """Test cleanup_expired method."""
        cache = QueryCache(ttl_seconds=1)  # Very short TTL

        # Set result for a query
        query = "SELECT * FROM users WHERE id = ?"
        params = {"id": 1}
        cache.set_result(query, params, [{"id": 1}])

        # Verify it's cached
        assert cache.get_result(query, params) == [{"id": 1}]

        # Wait for TTL to expire
        time.sleep(1.2)

        # Cleanup expired - should remove expired entry
        removed_count = cache.cleanup_expired()
        assert removed_count == 1

        # Verify it's no longer cached
        assert cache.get_result(query, params) is None

    def test_get_memory_usage(self):
        """Test get_memory_usage method."""
        cache = QueryCache()

        # Initially empty
        usage = cache.get_memory_usage()
        assert usage >= 0  # Should return a non-negative value

        # Add some entries
        for i in range(5):
            cache.set_result(
                "SELECT * FROM table WHERE id = ?", {"id": i}, [{"id": i, "data": f"data_{i}"}]
            )

        # Usage should be greater after adding entries
        new_usage = cache.get_memory_usage()
        assert new_usage > usage

    def test_generate_key_method(self):
        """Test _generate_key method for consistent key generation."""
        cache = QueryCache()

        # Same query and params should generate same key
        key1 = cache._generate_key("SELECT * FROM users WHERE id = ?", {"id": 1})
        key2 = cache._generate_key("SELECT * FROM users WHERE id = ?", {"id": 1})
        assert key1 == key2

        # Different params should generate different keys
        key3 = cache._generate_key("SELECT * FROM users WHERE id = ?", {"id": 2})
        assert key1 != key3

        # Different queries should generate different keys
        key4 = cache._generate_key("SELECT name FROM users WHERE id = ?", {"id": 1})
        assert key1 != key4

        # Case insensitive query normalization
        key5 = cache._generate_key("select * from users where id = ?", {"id": 1})
        assert key1 == key5  # Should be the same after normalization

    def test_invalidate_by_prefix(self):
        """Test invalidate_by_prefix method."""
        cache = QueryCache()

        # Add entries with different prefixes
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1}])
        cache.set_result("SELECT * FROM users WHERE name = ?", {"name": "John"}, [{"id": 1}])
        cache.set_result(
            "SELECT * FROM orders WHERE user_id = ?", {"user_id": 1}, [{"order_id": 10}]
        )

        # Verify all are cached
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) == [{"id": 1}]
        assert cache.get_result("SELECT * FROM users WHERE name = ?", {"name": "John"}) == [
            {"id": 1}
        ]
        assert cache.get_result("SELECT * FROM orders WHERE user_id = ?", {"user_id": 1}) == [
            {"order_id": 10}
        ]

        # Invalidate entries with "SELECT * FROM users" prefix
        invalidated_count = cache.invalidate_by_prefix("select * from users")  # Normalized
        assert invalidated_count == 2  # Both user queries should be invalidated

        # Verify user queries are no longer cached but order query remains
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) is None
        assert cache.get_result("SELECT * FROM users WHERE name = ?", {"name": "John"}) is None
        assert cache.get_result("SELECT * FROM orders WHERE user_id = ?", {"user_id": 1}) == [
            {"order_id": 10}
        ]

    def test_clear_by_query_pattern(self):
        """Test clear_by_query_pattern method."""
        cache = QueryCache()

        # Add entries with different patterns
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1}])
        cache.set_result("SELECT * FROM users WHERE name = ?", {"name": "John"}, [{"id": 1}])
        cache.set_result(
            "SELECT * FROM orders WHERE user_id = ?", {"user_id": 1}, [{"order_id": 10}]
        )

        # Verify all are cached
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) == [{"id": 1}]
        assert cache.get_result("SELECT * FROM users WHERE name = ?", {"name": "John"}) == [
            {"id": 1}
        ]
        assert cache.get_result("SELECT * FROM orders WHERE user_id = ?", {"user_id": 1}) == [
            {"order_id": 10}
        ]

        # Clear entries matching "users" pattern (case insensitive)
        cleared_count = cache.clear_by_query_pattern("users")
        assert cleared_count == 2  # Both user queries should be cleared

        # Verify user queries are no longer cached but order query remains
        assert cache.get_result("SELECT * FROM users WHERE id = ?", {"id": 1}) is None
        assert cache.get_result("SELECT * FROM users WHERE name = ?", {"name": "John"}) is None
        assert cache.get_result("SELECT * FROM orders WHERE user_id = ?", {"user_id": 1}) == [
            {"order_id": 10}
        ]

    def test_get_cached_queries(self):
        """Test get_cached_queries method."""
        cache = QueryCache()

        # Initially empty
        queries = cache.get_cached_queries()
        assert queries == []

        # Add some queries
        cache.set_result("SELECT * FROM users WHERE id = ?", {"id": 1}, [{"id": 1}])
        cache.set_result("SELECT * FROM users WHERE name = ?", {"name": "John"}, [{"id": 1}])
        cache.set_result(
            "SELECT * FROM orders WHERE user_id = ?", {"user_id": 1}, [{"order_id": 10}]
        )

        # Get cached queries
        queries = cache.get_cached_queries()

        # Should contain the normalized query patterns (the full normalized query strings)
        assert len(queries) == 3  # Each unique query pattern
        assert "select * from users where id = ?" in queries
        assert "select * from users where name = ?" in queries
        assert "select * from orders where user_id = ?" in queries
