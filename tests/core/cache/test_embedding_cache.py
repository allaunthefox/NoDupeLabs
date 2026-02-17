"""Tests for embedding cache module."""

import time

from nodupe.tools.ml.embedding_cache import EmbeddingCache, EmbeddingCacheError


class TestEmbeddingCache:
    """Test EmbeddingCache class."""

    def test_embedding_cache_initialization(self):
        """Test embedding cache initialization."""
        cache = EmbeddingCache(
            max_size=100, ttl_seconds=1800, max_dimensions=512
        )
        assert cache.max_size == 100
        assert cache.ttl_seconds == 1800
        assert cache.max_dimensions == 512
        assert cache.get_cache_size() == 0
        assert cache.get_stats()["size"] == 0

    def test_set_and_get_embedding(self):
        """Test setting and getting embedding vectors."""
        cache = EmbeddingCache()

        # Set embedding for a key
        key = "test_embedding"
        expected_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        cache.set_embedding(key, expected_embedding)

        # Get the embedding back
        retrieved_embedding = cache.get_embedding(key)
        assert retrieved_embedding == expected_embedding

    def test_get_nonexistent_embedding(self):
        """Test getting embedding for non-existent key."""
        cache = EmbeddingCache()

        # Set embedding for one key
        cache.set_embedding("key1", [0.1, 0.2, 0.3])

        # Try to get embedding for a different key
        result = cache.get_embedding("key2")
        assert result is None

    def test_cache_ttl_expiration(self):
        """Test cache entry expiration based on TTL."""
        cache = EmbeddingCache(ttl_seconds=1)  # Very short TTL for testing

        # Set embedding for a key
        cache.set_embedding("test_key", [0.1, 0.2, 0.3])

        # Verify it's cached
        assert cache.get_embedding("test_key") == [0.1, 0.2, 0.3]

        # Wait for TTL to expire
        time.sleep(1.2)

        # Verify it's no longer cached
        assert cache.get_embedding("test_key") is None

    def test_cache_size_limit(self):
        """Test cache size limit and LRU eviction."""
        cache = EmbeddingCache(max_size=2)  # Small cache for testing

        # Fill the cache
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])

        # Verify both are cached
        assert cache.get_embedding("key1") == [0.1, 0.2]
        assert cache.get_embedding("key2") == [0.3, 0.4]

        # Add a third embedding, which should evict the least recently used
        cache.set_embedding("key3", [0.5, 0.6])

        # Verify the first embedding was evicted and others remain
        assert cache.get_embedding("key1") is None  # Should be evicted
        assert cache.get_embedding("key2") == [
            0.3,
            0.4,
        ]  # Should still be there
        assert cache.get_embedding("key3") == [0.5, 0.6]  # Should be added

    def test_dimension_validation(self):
        """Test embedding dimension validation."""
        cache = EmbeddingCache(max_dimensions=5)

        # Valid embedding should work
        cache.set_embedding("valid", [0.1, 0.2, 0.3, 0.4, 0.5])
        assert cache.get_embedding("valid") == [0.1, 0.2, 0.3, 0.4, 0.5]

        # Invalid embedding should raise error
        try:
            cache.set_embedding("invalid", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
            assert False, "Expected EmbeddingCacheError"
        except EmbeddingCacheError:
            pass  # Expected

    def test_calculate_similarity(self):
        """Test calculating cosine similarity between embeddings."""
        cache = EmbeddingCache()

        # Set two identical embeddings
        cache.set_embedding("emb1", [1.0, 0.0, 0.0])
        cache.set_embedding("emb2", [1.0, 0.0, 0.0])

        # Should have perfect similarity
        similarity = cache.calculate_similarity("emb1", "emb2")
        assert (
            abs(similarity - 1.0) < 0.001
        )  # Allow for floating point precision

        # Set orthogonal embeddings
        cache.set_embedding("emb3", [0.0, 1.0, 0.0])
        similarity = cache.calculate_similarity("emb1", "emb3")
        assert abs(similarity - 0.0) < 0.001  # Should be nearly 0

    def test_calculate_similarity_with_different_vectors(self):
        """Test similarity calculation with different vectors."""
        cache = EmbeddingCache()

        # Set two similar embeddings
        cache.set_embedding("emb1", [1.0, 1.0])
        cache.set_embedding("emb2", [1.0, 1.0])

        similarity = cache.calculate_similarity("emb1", "emb2")
        assert abs(similarity - 1.0) < 0.001  # Perfect similarity

        # Set two different embeddings
        cache.set_embedding("emb3", [1.0, 0.0])
        cache.set_embedding("emb4", [0.0, 1.0])

        similarity = cache.calculate_similarity("emb3", "emb4")
        assert abs(similarity - 0.0) < 0.001  # Orthogonal vectors

    def test_calculate_similarity_with_none_result(self):
        """Test similarity calculation when one embedding doesn't exist."""
        cache = EmbeddingCache()

        # Set one embedding
        cache.set_embedding("emb1", [1.0, 0.0, 0.0])

        # Try to calculate similarity with non-existent embedding
        similarity = cache.calculate_similarity("emb1", "nonexistent")
        assert similarity is None

    def test_invalidate_specific_entry(self):
        """Test invalidating a specific cache entry."""
        cache = EmbeddingCache()

        # Set embeddings for two keys
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])

        # Verify both are cached
        assert cache.get_embedding("key1") == [0.1, 0.2]
        assert cache.get_embedding("key2") == [0.3, 0.4]

        # Invalidate first key
        invalidated = cache.invalidate("key1")
        assert invalidated is True

        # Verify first key is no longer cached
        assert cache.get_embedding("key1") is None
        assert cache.get_embedding("key2") == [0.3, 0.4]

    def test_invalidate_nonexistent_entry(self):
        """Test invalidating a non-existent cache entry."""
        cache = EmbeddingCache()

        # Try to invalidate non-cached key
        invalidated = cache.invalidate("nonexistent_key")
        assert invalidated is False

    def test_invalidate_all_entries(self):
        """Test invalidating all cache entries."""
        cache = EmbeddingCache()

        # Set embeddings for two keys
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])

        # Verify both are cached
        assert cache.get_embedding("key1") == [0.1, 0.2]
        assert cache.get_embedding("key2") == [0.3, 0.4]

        # Invalidate all entries
        cache.invalidate_all()

        # Verify neither is cached
        assert cache.get_embedding("key1") is None
        assert cache.get_embedding("key2") is None

    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = EmbeddingCache()

        # Initially, no hits or misses
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

        # Miss - key not in cache
        result = cache.get_embedding("nonexistent")
        assert result is None

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0
        assert stats["hit_rate"] == 0.0

        # Add to cache
        cache.set_embedding("key1", [0.1, 0.2])

        # Hit - key in cache
        result = cache.get_embedding("key1")
        assert result == [0.1, 0.2]

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 1
        assert stats["hit_rate"] == 0.5

    def test_validate_cache_removes_expired(self):
        """Test validate_cache method removes expired entries."""
        cache = EmbeddingCache(ttl_seconds=1)  # Very short TTL

        # Set embedding for a key
        cache.set_embedding("test_key", [0.1, 0.2, 0.3])

        # Verify it's cached
        assert cache.get_embedding("test_key") == [0.1, 0.2, 0.3]

        # Wait for TTL to expire
        time.sleep(1.2)

        # Validate cache - should remove expired entry
        removed_count = cache.validate_cache()
        assert removed_count == 1

        # Verify it's no longer cached
        assert cache.get_embedding("test_key") is None

    def test_is_cached_method(self):
        """Test is_cached method."""
        cache = EmbeddingCache()

        # Initially not cached
        assert cache.is_cached("test_key") is False

        # Add to cache
        cache.set_embedding("test_key", [0.1, 0.2])

        # Now cached
        assert cache.is_cached("test_key") is True

        # Remove from cache (by TTL expiration)
        cache.ttl_seconds = 0.1
        time.sleep(1.2)
        assert cache.is_cached("test_key") is False

    def test_resize_cache(self):
        """Test resizing the cache."""
        cache = EmbeddingCache(max_size=2)

        # Fill the cache
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])

        # Verify both are cached
        assert cache.get_embedding("key1") == [0.1, 0.2]
        assert cache.get_embedding("key2") == [0.3, 0.4]

        # Add a third embedding, which should evict one due to size limit
        cache.set_embedding("key3", [0.5, 0.6])

        # Resize to allow more entries
        cache.resize(5)

        # Add the evicted embedding back
        cache.set_embedding("key1", [0.1, 0.2, 0.3])  # Changed embedding

        # Verify all three can now be cached
        assert cache.get_embedding("key1") == [
            0.1,
            0.2,
            0.3,
        ]  # Should have new embedding
        assert cache.get_embedding("key2") == [
            0.3,
            0.4,
        ]  # Should still be there
        assert cache.get_embedding("key3") == [
            0.5,
            0.6,
        ]  # Should still be there

    def test_cleanup_expired_method(self):
        """Test cleanup_expired method."""
        cache = EmbeddingCache(ttl_seconds=1)  # Very short TTL

        # Set embedding for a key
        cache.set_embedding("test_key", [0.1, 0.2, 0.3])

        # Verify it's cached
        assert cache.get_embedding("test_key") == [0.1, 0.2, 0.3]

        # Wait for TTL to expire
        time.sleep(1.2)

        # Cleanup expired - should remove expired entry
        removed_count = cache.cleanup_expired()
        assert removed_count == 1

        # Verify it's no longer cached
        assert cache.get_embedding("test_key") is None

    def test_get_memory_usage(self):
        """Test get_memory_usage method."""
        cache = EmbeddingCache()

        # Initially empty
        usage = cache.get_memory_usage()
        assert usage >= 0  # Should return a non-negative value

        # Add some entries
        for i in range(5):
            cache.set_embedding(
                f"key_{i}", [float(j) for j in range(i + 1, i + 4)]
            )

        # Usage should be greater after adding entries
        new_usage = cache.get_memory_usage()
        assert new_usage > usage

    def test_cosine_similarity_calculation(self):
        """Test the internal cosine similarity calculation."""
        cache = EmbeddingCache()

        # Test with identical vectors
        sim = cache._cosine_similarity([1, 0], [1, 0])
        assert abs(sim - 1.0) < 0.001

        # Test with orthogonal vectors
        sim = cache._cosine_similarity([1, 0], [0, 1])
        assert abs(sim - 0.0) < 0.001

        # Test with opposite vectors (should be clamped to 0 due to [0,1] range)
        sim = cache._cosine_similarity([1, 0], [-1, 0])
        assert abs(sim - 0.0) < 0.001  # Negative values are clamped to 0

        # Test with similar vectors
        sim = cache._cosine_similarity([1, 1], [1, 1])
        assert abs(sim - 1.0) < 0.001

    def test_find_similar_embeddings(self):
        """Test finding similar embeddings."""
        cache = EmbeddingCache()

        # Set several embeddings
        cache.set_embedding("ref", [1.0, 0.0, 0.0])
        cache.set_embedding("similar", [0.9, 0.1, 0.0])  # Similar to ref
        cache.set_embedding("orthogonal", [0.0, 1.0, 0.0])  # Orthogonal to ref
        cache.set_embedding("opposite", [-1.0, 0.0, 0.0])  # Opposite to ref

        # Find similar embeddings with high threshold
        similar = cache.find_similar("ref", threshold=0.5, max_results=10)

        # Should find the similar embedding
        assert len(similar) >= 1
        found_keys = [key for key, _ in similar]
        assert "similar" in found_keys
        # The similar embedding should have high similarity
        for key, sim in similar:
            if key == "similar":
                assert sim > 0.5

    def test_get_average_embedding(self):
        """Test getting average embedding from multiple embeddings."""
        cache = EmbeddingCache()

        # Set several embeddings
        cache.set_embedding("emb1", [1.0, 2.0, 3.0])
        cache.set_embedding("emb2", [3.0, 4.0, 5.0])
        cache.set_embedding("emb3", [5.0, 6.0, 7.0])

        # Get average of all three
        avg = cache.get_average_embedding(["emb1", "emb2", "emb3"])
        expected_avg = [
            (1.0 + 3.0 + 5.0) / 3,
            (2.0 + 4.0 + 6.0) / 3,
            (3.0 + 5.0 + 7.0) / 3,
        ]

        assert avg is not None
        assert len(avg) == 3
        assert abs(avg[0] - expected_avg[0]) < 0.001
        assert abs(avg[1] - expected_avg[1]) < 0.001
        assert abs(avg[2] - expected_avg[2]) < 0.001

    def test_get_average_embedding_with_missing_keys(self):
        """Test getting average embedding when some keys don't exist."""
        cache = EmbeddingCache()

        # Set only one embedding
        cache.set_embedding("emb1", [1.0, 2.0, 3.0])

        # Try to get average with some missing keys
        avg = cache.get_average_embedding(["emb1", "missing1", "missing2"])

        # Should return the single embedding as average
        assert avg == [1.0, 2.0, 3.0]

        # Try with all missing keys
        avg = cache.get_average_embedding(["missing1", "missing2"])
        assert avg is None

    def test_clear_by_pattern(self):
        """Test clearing cache entries by pattern."""
        cache = EmbeddingCache()

        # Set several embeddings with different patterns
        cache.set_embedding("user_profile_123", [1.0, 0.0])
        cache.set_embedding("user_avatar_456", [0.0, 1.0])
        cache.set_embedding("post_content_789", [0.5, 0.5])

        # Verify all are cached
        assert cache.get_embedding("user_profile_123") is not None
        assert cache.get_embedding("user_avatar_456") is not None
        assert cache.get_embedding("post_content_789") is not None

        # Clear entries matching "user" pattern (case insensitive)
        cleared_count = cache.clear_by_pattern("user")
        assert cleared_count == 2  # Both user entries should be cleared

        # Verify user entries are no longer cached but post remains
        assert cache.get_embedding("user_profile_123") is None
        assert cache.get_embedding("user_avatar_456") is None
        assert cache.get_embedding("post_content_789") is not None

    def test_get_cached_keys(self):
        """Test get_cached_keys method."""
        cache = EmbeddingCache()

        # Initially empty
        keys = cache.get_cached_keys()
        assert keys == []

        # Add some embeddings
        cache.set_embedding("key1", [1.0, 0.0])
        cache.set_embedding("key2", [0.0, 1.0])
        cache.set_embedding("key3", [0.5, 0.5])

        # Get cached keys
        keys = cache.get_cached_keys()

        # Should contain all the keys
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys
