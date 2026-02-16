"""Tests for hash cache module."""

import tempfile
import time
from pathlib import Path

from nodupe.tools.hashing.hash_cache import HashCache, HashCacheError


class TestHashCache:
    """Test HashCache class."""

    def test_hash_cache_initialization(self):
        """Test hash cache initialization."""
        cache = HashCache(max_size=100, ttl_seconds=1800, enable_persistence=False)
        assert cache.max_size == 100
        assert cache.ttl_seconds == 1800
        assert cache.enable_persistence is False
        assert cache.get_cache_size() == 0
        assert cache.get_stats()["size"] == 0

    def test_set_and_get_hash(self, temp_dir):
        """Test setting and getting hash values."""
        cache = HashCache()

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # Set hash for the file
        expected_hash = "abc123"
        cache.set_hash(test_file, expected_hash)

        # Get the hash back
        retrieved_hash = cache.get_hash(test_file)
        assert retrieved_hash == expected_hash

    def test_get_nonexistent_hash(self, temp_dir):
        """Test getting hash for non-existent file."""
        cache = HashCache()

        # Create a test file and set its hash
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        cache.set_hash(test_file, "abc123")

        # Try to get hash for a different file
        other_file = temp_dir / "other.txt"
        other_file.write_text("other content")
        result = cache.get_hash(other_file)
        assert result is None

    def test_cache_ttl_expiration(self, temp_dir):
        """Test cache entry expiration based on TTL."""
        cache = HashCache(ttl_seconds=1)  # Very short TTL for testing

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # Set hash for the file
        cache.set_hash(test_file, "abc123")

        # Verify it's cached
        assert cache.get_hash(test_file) == "abc123"

        # Wait for TTL to expire
        time.sleep(1.2)

        # Verify it's no longer cached
        assert cache.get_hash(test_file) is None

    def test_cache_file_modification_invalidation(self, temp_dir):
        """Test cache invalidation when file is modified."""
        cache = HashCache()

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # Set hash for the file
        cache.set_hash(test_file, "abc123")

        # Verify it's cached
        assert cache.get_hash(test_file) == "abc123"

        # Modify the file
        time.sleep(0.1)  # Ensure different mtime
        test_file.write_text("modified content")

        # Verify it's no longer cached due to modification
        assert cache.get_hash(test_file) is None

    def test_cache_size_limit(self, temp_dir):
        """Test cache size limit and LRU eviction."""
        cache = HashCache(max_size=2)  # Small cache for testing

        # Create test files
        file1 = temp_dir / "file1.txt"
        file1.write_text("content1")
        file2 = temp_dir / "file2.txt"
        file2.write_text("content2")
        file3 = temp_dir / "file3.txt"
        file3.write_text("content3")

        # Fill the cache
        cache.set_hash(file1, "hash1")
        cache.set_hash(file2, "hash2")

        # Verify both are cached
        assert cache.get_hash(file1) == "hash1"
        assert cache.get_hash(file2) == "hash2"

        # Add a third file, which should evict the least recently used
        cache.set_hash(file3, "hash3")

        # file1 should be evicted (assuming LRU behavior)
        # But file2 was accessed more recently due to the get operation above
        # Actually, the set operation doesn't change LRU order, so file1 should be evicted
        assert cache.get_hash(file1) is None  # Should be evicted
        assert cache.get_hash(file2) == "hash2"  # Should still be there
        assert cache.get_hash(file3) == "hash3"  # Should be added

    def test_invalidate_specific_entry(self, temp_dir):
        """Test invalidating a specific cache entry."""
        cache = HashCache()

        # Create test files
        file1 = temp_dir / "file1.txt"
        file1.write_text("content1")
        file2 = temp_dir / "file2.txt"
        file2.write_text("content2")

        # Set hashes for both files
        cache.set_hash(file1, "hash1")
        cache.set_hash(file2, "hash2")

        # Verify both are cached
        assert cache.get_hash(file1) == "hash1"
        assert cache.get_hash(file2) == "hash2"

        # Invalidate first file
        invalidated = cache.invalidate(file1)
        assert invalidated is True

        # Verify first file is no longer cached
        assert cache.get_hash(file1) is None
        assert cache.get_hash(file2) == "hash2"

    def test_invalidate_nonexistent_entry(self, temp_dir):
        """Test invalidating a non-existent cache entry."""
        cache = HashCache()

        # Create a test file
        file1 = temp_dir / "file1.txt"
        file1.write_text("content1")

        # Try to invalidate non-cached file
        invalidated = cache.invalidate(file1)
        assert invalidated is False

    def test_invalidate_all_entries(self, temp_dir):
        """Test invalidating all cache entries."""
        cache = HashCache()

        # Create test files
        file1 = temp_dir / "file1.txt"
        file1.write_text("content1")
        file2 = temp_dir / "file2.txt"
        file2.write_text("content2")

        # Set hashes for both files
        cache.set_hash(file1, "hash1")
        cache.set_hash(file2, "hash2")

        # Verify both are cached
        assert cache.get_hash(file1) == "hash1"
        assert cache.get_hash(file2) == "hash2"

        # Invalidate all entries
        cache.invalidate_all()

        # Verify neither is cached
        assert cache.get_hash(file1) is None
        assert cache.get_hash(file2) is None

    def test_cache_statistics(self, temp_dir):
        """Test cache statistics tracking."""
        cache = HashCache()

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # Initially, no hits or misses
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

        # Miss - file not in cache
        result = cache.get_hash(test_file)
        assert result is None

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0
        assert stats["hit_rate"] == 0.0

        # Add to cache
        cache.set_hash(test_file, "abc123")

        # Hit - file in cache
        result = cache.get_hash(test_file)
        assert result == "abc123"

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 1
        assert stats["hit_rate"] == 0.5

    def test_validate_cache_removes_expired(self, temp_dir):
        """Test validate_cache method removes expired entries."""
        cache = HashCache(ttl_seconds=1)  # Very short TTL

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # Set hash for the file
        cache.set_hash(test_file, "abc123")

        # Verify it's cached
        assert cache.get_hash(test_file) == "abc123"

        # Wait for TTL to expire
        time.sleep(1.2)

        # Validate cache - should remove expired entry
        removed_count = cache.validate_cache()
        assert removed_count == 1

        # Verify it's no longer cached
        assert cache.get_hash(test_file) is None

    def test_validate_cache_removes_modified_files(self, temp_dir):
        """Test validate_cache method removes entries for modified files."""
        cache = HashCache()

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # Set hash for the file
        cache.set_hash(test_file, "abc123")

        # Verify it's cached
        assert cache.get_hash(test_file) == "abc123"

        # Modify the file
        time.sleep(0.1)  # Ensure different mtime
        test_file.write_text("modified content")

        # Validate cache - should remove entry for modified file
        removed_count = cache.validate_cache()
        assert removed_count == 1

        # Verify it's no longer cached
        assert cache.get_hash(test_file) is None

    def test_is_cached_method(self, temp_dir):
        """Test is_cached method."""
        cache = HashCache()

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # Initially not cached
        assert cache.is_cached(test_file) is False

        # Add to cache
        cache.set_hash(test_file, "abc123")

        # Now cached
        assert cache.is_cached(test_file) is True

        # Remove from cache (by TTL expiration)
        cache.ttl_seconds = 0.1
        time.sleep(1.2)
        assert cache.is_cached(test_file) is False

    def test_resize_cache(self, temp_dir):
        """Test resizing the cache."""
        cache = HashCache(max_size=2)

        # Create test files
        file1 = temp_dir / "file1.txt"
        file1.write_text("content1")
        file2 = temp_dir / "file2.txt"
        file2.write_text("content2")
        file3 = temp_dir / "file3.txt"
        file3.write_text("content3")

        # Fill the cache
        cache.set_hash(file1, "hash1")
        cache.set_hash(file2, "hash2")

        # Verify both are cached
        assert cache.get_hash(file1) == "hash1"
        assert cache.get_hash(file2) == "hash2"

        # Add a third file, which should evict one due to size limit
        cache.set_hash(file3, "hash3")

        # Resize to allow more entries
        cache.resize(5)

        # Add the evicted file back
        cache.set_hash(file1, "hash1_new")

        # Verify all three can now be cached
        assert cache.get_hash(file1) == "hash1_new"
        assert cache.get_hash(file2) == "hash2"  # Should still be there
        assert cache.get_hash(file3) == "hash3"  # Should still be there

    def test_cleanup_expired_method(self, temp_dir):
        """Test cleanup_expired method."""
        cache = HashCache(ttl_seconds=1)  # Very short TTL

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        # Set hash for the file
        cache.set_hash(test_file, "abc123")

        # Verify it's cached
        assert cache.get_hash(test_file) == "abc123"

        # Wait for TTL to expire
        time.sleep(1.2)

        # Cleanup expired - should remove expired entry
        removed_count = cache.cleanup_expired()
        assert removed_count == 1

        # Verify it's no longer cached
        assert cache.get_hash(test_file) is None

    def test_get_memory_usage(self, temp_dir):
        """Test get_memory_usage method."""
        cache = HashCache()

        # Initially empty
        usage = cache.get_memory_usage()
        assert usage >= 0  # Should return a non-negative value

        # Add some entries
        for i in range(5):
            test_file = temp_dir / f"test{i}.txt"
            test_file.write_text(f"test content {i}")
            cache.set_hash(test_file, f"hash{i}")

        # Usage should be greater after adding entries
        new_usage = cache.get_memory_usage()
        assert new_usage > usage

