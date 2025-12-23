"""
Test suite for query cache functionality.
Tests query result caching operations from nodupe.core.cache.query_cache.
"""

import os
import tempfile
import shutil
from pathlib import Path
import time
import pytest
from unittest.mock import patch

from nodupe.core.cache.query_cache import QueryCache, create_query_cache


class TestQueryCache:
    """Test QueryCache functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_query_cache_initialization(self):
        """Test QueryCache initialization."""
        cache = QueryCache()
        
        assert cache is not None
        assert cache.max_size == 1000  # Default from implementation
        assert cache.ttl_seconds == 3600  # Default from implementation
        assert len(cache._cache) == 0
        assert cache._stats['hits'] == 0
        assert cache._stats['misses'] == 0
        assert cache._stats['evictions'] == 0
        assert cache._stats['insertions'] == 0
    
    def test_query_cache_initialization_with_parameters(self):
        """Test QueryCache initialization with custom parameters."""
        cache = QueryCache(max_size=500, ttl_seconds=1800)
        
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800
    
    def test_get_result_nonexistent_query(self):
        """Test getting result for nonexistent query."""
        cache = QueryCache()
        query = "SELECT * FROM users WHERE id = ?"
        params = {"id": 123}
        
        result = cache.get_result(query, params)
        assert result is None
        assert cache._stats['misses'] == 1
    
    def test_get_result_empty_cache(self):
        """Test getting result from empty cache."""
        cache = QueryCache()
        query = "SELECT name FROM users"
        
        result = cache.get_result(query)
        assert result is None
        assert cache._stats['misses'] == 1
    
    def test_set_and_get_result(self):
        """Test setting and getting result for a query."""
        cache = QueryCache()
        query = "SELECT * FROM users WHERE id = ?"
        params = {"id": 123}
        result_data = [{"id": 123, "name": "John Doe"}]
        
        # Set result
        cache.set_result(query, params, result_data)
        assert cache._stats['insertions'] == 1
        
        # Get result
        result = cache.get_result(query, params)
        assert result == result_data
        assert cache._stats['hits'] == 1
        assert cache._stats['misses'] == 0  # No miss when setting - only when getting non-existent
    
    def test_result_ttl_expiration(self):
        """Test result expiration based on TTL."""
        cache = QueryCache(ttl_seconds=0.1)  # Very short TTL
        query = "SELECT * FROM expired_test"
        result_data = [{"id": 1, "status": "expired"}]
        
        # Set result
        cache.set_result(query, None, result_data)
        assert cache.get_result(query) == result_data  # Should work initially
        
        # Wait for TTL to expire
        time.sleep(0.2)
        
        # Result should be expired
        result = cache.get_result(query)
        assert result is None
        assert cache._stats['misses'] == 1  # After expiration
    
    def test_cache_size_limit_eviction(self):
        """Test cache size limit and LRU eviction."""
        cache = QueryCache(max_size=2)
        queries = [f"SELECT * FROM table_{i}" for i in range(3)]
        results = [f"result_{i}" for i in range(3)]
        
        # Fill cache to max size
        cache.set_result(queries[0], None, results[0])  # Oldest
        cache.set_result(queries[1], None, results[1])  # Newest
        assert cache.get_result(queries[0]) == results[0]
        assert cache.get_result(queries[1]) == results[1]
        
        # Add third item - should evict oldest (queries[0])
        cache.set_result(queries[2], None, results[2])
        
        # Verify oldest was evicted
        assert cache.get_result(queries[0]) is None  # Evicted
        assert cache.get_result(queries[1]) == results[1]  # Still there
        assert cache.get_result(queries[2]) == results[2]  # New entry
        assert cache._stats['evictions'] == 1
    
    def test_invalidate_specific_query(self):
        """Test invalidating specific query from cache."""
        cache = QueryCache()
        query1 = "SELECT * FROM users WHERE id = ?"
        query2 = "SELECT * FROM orders WHERE user_id = ?"
        params1 = {"id": 1}
        params2 = {"user_id": 1}
        result1 = [{"id": 1, "name": "User 1"}]
        result2 = [{"order_id": 100, "user_id": 1}]
        
        # Set results for both queries
        cache.set_result(query1, params1, result1)
        cache.set_result(query2, params2, result2)
        
        # Verify both are cached
        assert cache.get_result(query1, params1) == result1
        assert cache.get_result(query2, params2) == result2
        
        # Invalidate first query
        result = cache.invalidate(query1, params1)
        assert result is True
        
        # Verify only first query was invalidated
        assert cache.get_result(query1, params1) is None
        assert cache.get_result(query2, params2) == result2
    
    def test_invalidate_nonexistent_query(self):
        """Test invalidating nonexistent query."""
        cache = QueryCache()
        nonexistent_query = "SELECT * FROM nonexistent_table"
        params = {"id": 999}
        
        result = cache.invalidate(nonexistent_query, params)
        assert result is False
    
    def test_invalidate_all(self):
        """Test invalidating all cache entries."""
        cache = QueryCache()
        queries = [f"SELECT * FROM test_{i}" for i in range(3)]
        results = [f"result_{i}" for i in range(3)]
        
        # Set results for all queries
        for i, query in enumerate(queries):
            cache.set_result(query, None, results[i])
        
        # Verify all are cached
        for i, query in enumerate(queries):
            assert cache.get_result(query) == results[i]
        
        # Invalidate all
        cache.invalidate_all()
        
        # Verify all are invalidated
        for query in queries:
            assert cache.get_result(query) is None
        assert cache._stats['evictions'] == 3
    
    def test_invalidate_by_prefix(self):
        """Test invalidating queries by prefix."""
        cache = QueryCache()
        queries = [
            "SELECT * FROM users WHERE id = ?",
            "SELECT * FROM users WHERE name = ?", 
            "SELECT * FROM orders WHERE id = ?"
        ]
        results = ["users_result1", "users_result2", "orders_result"]
        
        # Set results for all queries
        for i, query in enumerate(queries):
            cache.set_result(query, None, results[i])
        
        # Verify all are cached
        for i, query in enumerate(queries):
            assert cache.get_result(query) == results[i]
        
        # Invalidate all queries starting with "SELECT * FROM users"
        removed_count = cache.invalidate_by_prefix("select * from users")
        assert removed_count == 2  # Two user queries should be removed
        
        # Verify user queries were removed but order query remains
        assert cache.get_result(queries[0]) is None  # User query 1
        assert cache.get_result(queries[1]) is None  # User query 2
        assert cache.get_result(queries[2]) == results[2]  # Order query remains
    
    def test_validate_cache_removes_stale_entries(self):
        """Test validate_cache removes stale entries."""
        cache = QueryCache(ttl_seconds=0.1)
        valid_query = "SELECT * FROM valid"
        expired_query = "SELECT * FROM expired"
        valid_result = [{"status": "valid"}]
        expired_result = [{"status": "expired"}]
        
        # Set results
        cache.set_result(valid_query, None, valid_result)
        cache.set_result(expired_query, None, expired_result)
        
        # Wait for TTL to expire for one query
        time.sleep(0.2)
        
        # Validate cache - should remove expired query entry
        removed_count = cache.validate_cache()
        assert removed_count == 1  # Only expired query
        
        # Valid query should still be cached
        assert cache.get_result(valid_query) == valid_result
        # Expired query should be removed
        assert cache.get_result(expired_query) is None
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = QueryCache(max_size=10)
        query = "SELECT * FROM stats_test"
        result_data = [{"id": 1, "name": "Stats Test"}]
        
        # Perform operations to populate stats
        cache.set_result(query, None, result_data)
        cache.get_result(query)  # Hit
        cache.get_result("SELECT * FROM nonexistent")  # Miss
        
        stats = cache.get_stats()
        
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'evictions' in stats
        assert 'insertions' in stats
        assert 'size' in stats
        assert 'capacity' in stats
        assert 'hit_rate' in stats
        
        assert stats['insertions'] == 1
        assert stats['hits'] == 1
        assert stats['misses'] == 2  # Initial miss + nonexistent query
        assert stats['size'] == 1
        assert stats['capacity'] == 10
        assert stats['hit_rate'] == 1.0 / 3.0  # hits / (hits + misses)
    
    def test_get_cache_size(self):
        """Test getting current cache size."""
        cache = QueryCache()
        queries = [f"SELECT * FROM size_test_{i}" for i in range(3)]
        results = [f"size_result_{i}" for i in range(3)]
        
        # Check initial size
        assert cache.get_cache_size() == 0
        
        # Add queries and check size
        for i, query in enumerate(queries):
            cache.set_result(query, None, results[i])
            assert cache.get_cache_size() == i + 1
    
    def test_is_cached(self):
        """Test is_cached method."""
        cache = QueryCache()
        query = "SELECT * FROM cached_test"
        result_data = [{"id": 1, "cached": True}]
        
        # Should not be cached initially
        assert cache.is_cached(query) is False
        
        # Set result
        cache.set_result(query, None, result_data)
        
        # Should be cached
        assert cache.is_cached(query) is True
        
        # After TTL expiration should not be cached
        cache.ttl_seconds = 0.01
        time.sleep(0.02)
        assert cache.is_cached(query) is False
    
    def test_cleanup_expired(self):
        """Test cleanup_expired method."""
        cache = QueryCache(ttl_seconds=0.01)
        queries = [f"SELECT * FROM cleanup_{i}" for i in range(2)]
        results = [f"cleanup_result_{i}" for i in range(2)]
        
        # Set results
        for i, query in enumerate(queries):
            cache.set_result(query, None, results[i])
        
        # Wait for TTL to expire
        time.sleep(0.02)
        
        # Cleanup expired - should remove both entries
        removed_count = cache.cleanup_expired()
        assert removed_count == 2
        
        # Both queries should no longer be cached
        for query in queries:
            assert cache.is_cached(query) is False
    
    def test_resize_cache(self):
        """Test resizing cache and evicting excess entries."""
        cache = QueryCache(max_size=3)
        queries = [f"SELECT * FROM resize_{i}" for i in range(4)]
        results = [f"resize_result_{i}" for i in range(4)]
        
        # Fill cache
        for i, query in enumerate(queries):
            cache.set_result(query, None, results[i])
        
        # Cache should have 3 entries (4th caused eviction of 1st)
        assert cache.get_cache_size() == 3
        assert cache._stats['evictions'] == 1
        
        # Resize to smaller size - should evict more entries
        cache.resize(2)
        assert cache.get_cache_size() == 2
        assert cache._stats['evictions'] == 2 # Original + resize eviction
    
    def test_get_memory_usage(self):
        """Test getting approximate memory usage."""
        cache = QueryCache()
        query = "SELECT * FROM memory_test"
        result_data = [{"id": 1, "name": "Memory Test"}]
        
        # Check initial usage
        initial_usage = cache.get_memory_usage()
        assert isinstance(initial_usage, int)
        assert initial_usage >= 0
        
        # Add entry and check usage increased
        cache.set_result(query, None, result_data)
        final_usage = cache.get_memory_usage()
        
        assert final_usage > initial_usage
        assert isinstance(final_usage, int)
    
    def test_generate_key_normalization(self):
        """Test key generation with query normalization."""
        cache = QueryCache()
        
        # Test with different spacing and case
        query1 = "SELECT * FROM users WHERE id = ?"
        query2 = "select  *  from  users  where  id  =  ?"
        
        key1 = cache._generate_key(query1, {"id": 123})
        key2 = cache._generate_key(query2, {"id": 123})
        
        # Keys should be the same due to normalization
        assert key1 == key2
        
        # Test with different parameters
        key3 = cache._generate_key(query1, {"id": 456})
        assert key1 != key3  # Different parameters should create different keys
    
    def test_generate_key_without_params(self):
        """Test key generation without parameters."""
        cache = QueryCache()
        query = "SELECT COUNT(*) FROM users"
        
        key = cache._generate_key(query, None)
        assert key.endswith(":none")  # Should use "none" suffix when no params
        
        key2 = cache._generate_key(query, {})
        assert key2.endswith(":none")  # Empty dict should also use "none"
    
    def test_clear_by_query_pattern(self):
        """Test clearing cache entries by query pattern."""
        cache = QueryCache()
        queries = [
            "SELECT * FROM users WHERE active = ?",
            "SELECT id, name FROM users WHERE active = ?",
            "SELECT * FROM orders WHERE user_id = ?"
        ]
        results = ["users_active", "users_selective", "orders"]
        
        # Set results for all queries
        for i, query in enumerate(queries):
            cache.set_result(query, None, results[i])
        
        # Verify all are cached
        for i, query in enumerate(queries):
            assert cache.get_result(query) == results[i]
        
        # Clear all user-related queries
        cleared_count = cache.clear_by_query_pattern("users")
        assert cleared_count == 2  # Two user queries
        
        # Verify user queries were cleared but order query remains
        assert cache.get_result(queries[0]) is None  # Users query 1
        assert cache.get_result(queries[1]) is None  # Users query 2
        assert cache.get_result(queries[2]) == results[2]  # Orders query remains
    
    def test_get_cached_queries(self):
        """Test getting list of cached query patterns."""
        cache = QueryCache()
        queries = [
            "SELECT * FROM users WHERE id = ?",
            "SELECT * FROM orders WHERE user_id = ?",
            "SELECT COUNT(*) FROM users"
        ]
        results = ["users_result", "orders_result", "count_result"]
        
        # Set results for all queries
        for i, query in enumerate(queries):
            cache.set_result(query, None, results[i])
        
        cached_patterns = cache.get_cached_queries()
        
        # Should contain the normalized query patterns
        assert len(cached_patterns) == 3
        for query in queries:
            normalized = ' '.join(query.split()).lower()
            assert normalized in cached_patterns
    
    def test_thread_safety(self):
        """Test basic thread safety."""
        import threading
        cache = QueryCache()
        query = "SELECT * FROM thread_test"
        
        results = []
        
        def worker():
            for i in range(10):
                cache.set_result(query, {"index": i}, f"result_{i}")
                result = cache.get_result(query, {"index": i})
                results.append(result is not None)
        
        # Run multiple threads
        threads = []
        for _ in range(3):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All operations should complete without errors
        assert len(results) == 30
        # At least some operations should succeed
        assert any(results)


def test_create_query_cache_function():
    """Test the create_query_cache factory function."""
    # Test with default parameters
    cache1 = create_query_cache()
    assert isinstance(cache1, QueryCache)
    assert cache1.max_size == 1000
    assert cache1.ttl_seconds == 3600
    
    # Test with custom parameters
    cache2 = create_query_cache(max_size=500, ttl_seconds=1800)
    assert isinstance(cache2, QueryCache)
    assert cache2.max_size == 500
    assert cache2.ttl_seconds == 1800


def test_query_cache_error_handling():
    """Test error handling in QueryCache operations."""
    cache = QueryCache()
    
    # Test with None query (should not crash)
    try:
        result = cache.get_result(None)
        assert result is None
    except Exception:
        pytest.fail("get_result should not raise exception for None query")
    
    # Test setting result with None query (should not crash)
    try:
        cache.set_result(None, None, "test_result")
        # Should not add to cache if query is None
    except Exception:
        pytest.fail("set_result should not raise exception for None query")


if __name__ == "__main__":
    pytest.main([__file__])
