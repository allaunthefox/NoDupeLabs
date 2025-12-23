"""
Test suite for hash cache functionality.
Tests file hash caching operations from nodupe.core.cache.hash_cache.
"""

import os
import tempfile
import shutil
from pathlib import Path
import time
import pytest
from unittest.mock import patch

from nodupe.core.cache.hash_cache import HashCache, create_hash_cache


class TestHashCache:
    """Test HashCache functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_hash_cache_initialization(self):
        """Test HashCache initialization."""
        cache = HashCache()
        
        assert cache is not None
        assert cache.max_size == 1000  # Default from implementation
        assert cache.ttl_seconds == 3600  # Default from implementation
        assert cache.enable_persistence is False
        assert len(cache._cache) == 0
        assert cache._stats['hits'] == 0
        assert cache._stats['misses'] == 0
        assert cache._stats['evictions'] == 0
        assert cache._stats['insertions'] == 0
    
    def test_hash_cache_initialization_with_parameters(self):
        """Test HashCache initialization with custom parameters."""
        cache = HashCache(max_size=500, ttl_seconds=1800, enable_persistence=True)
        
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800
        assert cache.enable_persistence is True
    
    def test_get_hash_nonexistent_file(self):
        """Test getting hash for nonexistent file."""
        cache = HashCache()
        test_path = Path("nonexistent.txt")
        
        result = cache.get_hash(test_path)
        assert result is None
        assert cache._stats['misses'] == 1
    
    def test_get_hash_empty_cache(self):
        """Test getting hash from empty cache."""
        cache = HashCache()
        test_file = Path("test.txt")
        
        # Create test file
        test_file.write_text("test content")
        
        result = cache.get_hash(test_file)
        assert result is None
        assert cache._stats['misses'] == 1
    
    def test_set_and_get_hash(self):
        """Test setting and getting hash for a file."""
        cache = HashCache()
        test_file = Path("test.txt")
        test_hash = "abc123def456"
        
        # Create test file
        test_file.write_text("test content")
        
        # Set hash
        cache.set_hash(test_file, test_hash)
        assert cache._stats['insertions'] == 1
        
        # Get hash
        result = cache.get_hash(test_file)
        assert result == test_hash
        assert cache._stats['hits'] == 1
        assert cache._stats['misses'] == 0  # No miss when setting - only when getting non-existent
    
    def test_hash_invalidation_on_file_modification(self):
        """Test hash invalidation when file is modified."""
        cache = HashCache()
        test_file = Path("test.txt")
        original_hash = "original_hash"
        modified_hash = "modified_hash"
        
        # Create initial file
        test_file.write_text("original content")
        initial_mtime = test_file.stat().st_mtime
        
        # Set hash for initial file
        cache.set_hash(test_file, original_hash)
        assert cache.get_hash(test_file) == original_hash
        
        # Modify file
        time.sleep(0.01) # Ensure different mtime
        test_file.write_text("modified content")
        new_mtime = test_file.stat().st_mtime
        
        assert new_mtime != initial_mtime
        
        # Hash should be invalidated due to modification
        result = cache.get_hash(test_file)
        assert result is None
        assert cache._stats['misses'] == 1  # Only one miss when getting modified file
    
    def test_hash_ttl_expiration(self):
        """Test hash expiration based on TTL."""
        cache = HashCache(ttl_seconds=0.1)  # Very short TTL
        test_file = Path("test.txt")
        test_hash = "ttl_test_hash"
        
        # Create test file
        test_file.write_text("ttl test content")
        
        # Set hash
        cache.set_hash(test_file, test_hash)
        assert cache.get_hash(test_file) == test_hash  # Should work initially
        
        # Wait for TTL to expire
        time.sleep(0.2)
        
        # Hash should be expired
        result = cache.get_hash(test_file)
        assert result is None
        assert cache._stats['misses'] == 2  # Initial + after expiration
    
    def test_cache_size_limit_eviction(self):
        """Test cache size limit and LRU eviction."""
        cache = HashCache(max_size=2)
        test_files = [Path(f"test_{i}.txt") for i in range(3)]
        test_hashes = [f"hash_{i}" for i in range(3)]
        
        # Create test files
        for i, file_path in enumerate(test_files):
            file_path.write_text(f"content {i}")
        
        # Fill cache to max size
        cache.set_hash(test_files[0], test_hashes[0])  # Oldest
        cache.set_hash(test_files[1], test_hashes[1])  # Newest
        assert cache.get_hash(test_files[0]) == test_hashes[0]
        assert cache.get_hash(test_files[1]) == test_hashes[1]
        
        # Add third item - should evict oldest (test_files[0])
        cache.set_hash(test_files[2], test_hashes[2])
        
        # Verify oldest was evicted
        assert cache.get_hash(test_files[0]) is None  # Evicted
        assert cache.get_hash(test_files[1]) == test_hashes[1]  # Still there
        assert cache.get_hash(test_files[2]) == test_hashes[2]  # New entry
        assert cache._stats['evictions'] == 1
    
    def test_invalidate_specific_file(self):
        """Test invalidating specific file from cache."""
        cache = HashCache()
        test_file1 = Path("test1.txt")
        test_file2 = Path("test2.txt")
        hash1 = "hash1"
        hash2 = "hash2"
        
        # Create test files
        test_file1.write_text("content 1")
        test_file2.write_text("content 2")
        
        # Set hashes for both files
        cache.set_hash(test_file1, hash1)
        cache.set_hash(test_file2, hash2)
        
        # Verify both are cached
        assert cache.get_hash(test_file1) == hash1
        assert cache.get_hash(test_file2) == hash2
        
        # Invalidate first file
        result = cache.invalidate(test_file1)
        assert result is True
        
        # Verify only first file was invalidated
        assert cache.get_hash(test_file1) is None
        assert cache.get_hash(test_file2) == hash2
    
    def test_invalidate_nonexistent_file(self):
        """Test invalidating nonexistent file."""
        cache = HashCache()
        nonexistent_file = Path("nonexistent.txt")
        
        result = cache.invalidate(nonexistent_file)
        assert result is False
    
    def test_invalidate_all(self):
        """Test invalidating all cache entries."""
        cache = HashCache()
        test_files = [Path(f"test_{i}.txt") for i in range(3)]
        test_hashes = [f"hash_{i}" for i in range(3)]
        
        # Create test files and set hashes
        for i, file_path in enumerate(test_files):
            file_path.write_text(f"content {i}")
            cache.set_hash(file_path, test_hashes[i])
        
        # Verify all are cached
        for i, file_path in enumerate(test_files):
            assert cache.get_hash(file_path) == test_hashes[i]
        
        # Invalidate all
        cache.invalidate_all()
        
        # Verify all are invalidated
        for file_path in test_files:
            assert cache.get_hash(file_path) is None
        assert cache._stats['evictions'] == 3
    
    def test_validate_cache_removes_stale_entries(self):
        """Test validate_cache removes stale entries."""
        cache = HashCache(ttl_seconds=0.1)
        valid_file = Path("valid.txt")
        expired_file = Path("expired.txt")
        deleted_file = Path("deleted.txt")
        
        # Create files
        valid_file.write_text("valid content")
        expired_file.write_text("expired content")
        deleted_file.write_text("deleted content")
        
        # Set hashes
        cache.set_hash(valid_file, "valid_hash")
        cache.set_hash(expired_file, "expired_hash")
        cache.set_hash(deleted_file, "deleted_hash")
        
        # Wait for TTL to expire for one file
        time.sleep(0.2)
        
        # Delete one file
        deleted_file.unlink()
        
        # Validate cache - should remove expired and deleted file entries
        removed_count = cache.validate_cache()
        assert removed_count == 2 # expired + deleted file
        
        # Valid file should still be cached
        assert cache.get_hash(valid_file) == "valid_hash"
        # Expired and deleted files should be removed
        assert cache.get_hash(expired_file) is None
        assert cache.get_hash(deleted_file) is None
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = HashCache(max_size=10)
        test_file = Path("stats_test.txt")
        
        # Create test file
        test_file.write_text("stats content")
        
        # Perform operations to populate stats
        cache.set_hash(test_file, "test_hash")
        cache.get_hash(test_file)  # Hit
        cache.get_hash(Path("nonexistent.txt"))  # Miss
        
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
        assert stats['misses'] == 2  # Initial miss + nonexistent file
        assert stats['size'] == 1
        assert stats['capacity'] == 10
        assert stats['hit_rate'] == 1.0 / 3.0  # hits / (hits + misses)
    
    def test_get_cache_size(self):
        """Test getting current cache size."""
        cache = HashCache()
        test_files = [Path(f"size_test_{i}.txt") for i in range(3)]
        
        # Create test files
        for i, file_path in enumerate(test_files):
            file_path.write_text(f"size test content {i}")
        
        # Check initial size
        assert cache.get_cache_size() == 0
        
        # Add files and check size
        for i, file_path in enumerate(test_files):
            cache.set_hash(file_path, f"hash_{i}")
            assert cache.get_cache_size() == i + 1
    
    def test_is_cached(self):
        """Test is_cached method."""
        cache = HashCache()
        test_file = Path("cached_test.txt")
        
        # Create test file
        test_file.write_text("cached content")
        
        # Should not be cached initially
        assert cache.is_cached(test_file) is False
        
        # Set hash
        cache.set_hash(test_file, "cached_hash")
        
        # Should be cached
        assert cache.is_cached(test_file) is True
        
        # After TTL expiration should not be cached
        cache.ttl_seconds = 0.01
        time.sleep(0.02)
        assert cache.is_cached(test_file) is False
    
    def test_cleanup_expired(self):
        """Test cleanup_expired method."""
        cache = HashCache(ttl_seconds=0.01)
        test_files = [Path(f"cleanup_{i}.txt") for i in range(2)]
        
        # Create test files
        for i, file_path in enumerate(test_files):
            file_path.write_text(f"cleanup content {i}")
        
        # Set hashes
        for i, file_path in enumerate(test_files):
            cache.set_hash(file_path, f"cleanup_hash_{i}")
        
        # Wait for TTL to expire
        time.sleep(0.02)
        
        # Cleanup expired - should remove both entries
        removed_count = cache.cleanup_expired()
        assert removed_count == 2
        
        # Both files should no longer be cached
        for file_path in test_files:
            assert cache.is_cached(file_path) is False
    
    def test_resize_cache(self):
        """Test resizing cache and evicting excess entries."""
        cache = HashCache(max_size=3)
        test_files = [Path(f"resize_{i}.txt") for i in range(4)]
        
        # Create test files
        for i, file_path in enumerate(test_files):
            file_path.write_text(f"resize content {i}")
        
        # Fill cache
        for i, file_path in enumerate(test_files):
            cache.set_hash(file_path, f"resize_hash_{i}")
        
        # Cache should have 3 entries (4th caused eviction of 1st)
        assert cache.get_cache_size() == 3
        assert cache._stats['evictions'] == 1
        
        # Resize to smaller size - should evict more entries
        cache.resize(2)
        assert cache.get_cache_size() == 2
        assert cache._stats['evictions'] == 2 # Original + resize eviction
    
    def test_get_memory_usage(self):
        """Test getting approximate memory usage."""
        cache = HashCache()
        test_file = Path("memory_test.txt")
        
        # Create test file
        test_file.write_text("memory test content")
        
        # Check initial usage
        initial_usage = cache.get_memory_usage()
        assert isinstance(initial_usage, int)
        assert initial_usage >= 0
        
        # Add entry and check usage increased
        cache.set_hash(test_file, "memory_hash")
        final_usage = cache.get_memory_usage()
        
        assert final_usage > initial_usage
        assert isinstance(final_usage, int)
    
    def test_thread_safety(self):
        """Test basic thread safety."""
        import threading
        cache = HashCache()
        test_file = Path("thread_test.txt")
        
        # Create test file
        test_file.write_text("thread safety test")
        
        results = []
        
        def worker():
            for i in range(10):
                cache.set_hash(test_file, f"hash_{i}")
                result = cache.get_hash(test_file)
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


def test_create_hash_cache_function():
    """Test the create_hash_cache factory function."""
    # Test with default parameters
    cache1 = create_hash_cache()
    assert isinstance(cache1, HashCache)
    assert cache1.max_size == 1000
    assert cache1.ttl_seconds == 3600
    assert cache1.enable_persistence is False
    
    # Test with custom parameters
    cache2 = create_hash_cache(max_size=500, ttl_seconds=1800, enable_persistence=True)
    assert isinstance(cache2, HashCache)
    assert cache2.max_size == 500
    assert cache2.ttl_seconds == 1800
    assert cache2.enable_persistence is True


def test_hash_cache_error_handling():
    """Test error handling in HashCache operations."""
    cache = HashCache()
    
    # Test with invalid path (should not crash)
    try:
        result = cache.get_hash(Path("/invalid/path/that/does/not/exist"))
        assert result is None
    except Exception:
        pytest.fail("get_hash should not raise exception for invalid path")
    
    # Test setting hash for non-existent file (should not crash)
    try:
        cache.set_hash(Path("/invalid/path/file.txt"), "test_hash")
        # Should not add to cache if file doesn't exist
    except Exception:
        pytest.fail("set_hash should not raise exception for invalid path")


if __name__ == "__main__":
    pytest.main([__file__])
