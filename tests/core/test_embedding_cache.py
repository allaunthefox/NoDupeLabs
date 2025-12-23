"""Tests for embedding cache module."""

import pytest
import tempfile
import os
from pathlib import Path
from nodupe.core.cache.embedding_cache import EmbeddingCache, EmbeddingCacheError, create_embedding_cache


class TestEmbeddingCache:
    """Test EmbeddingCache functionality."""

    def test_embedding_cache_creation(self):
        """Test embedding cache creation."""
        cache = EmbeddingCache()
        
        assert cache is not None
        assert cache.max_size == 1000
        assert cache.ttl_seconds == 3600
        assert cache.max_dimensions == 1024
        
        # Test with custom parameters
        cache = EmbeddingCache(max_size=500, ttl_seconds=1800, max_dimensions=512)
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800
        assert cache.max_dimensions == 512

    def test_get_set_embedding(self):
        """Test getting and setting embeddings."""
        cache = EmbeddingCache()
        
        # Test setting and getting an embedding
        key = "test_key"
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        cache.set_embedding(key, embedding)
        retrieved = cache.get_embedding(key)
        
        assert retrieved is not None
        assert retrieved == embedding
        assert len(retrieved) == len(embedding)

    def test_get_nonexistent_embedding(self):
        """Test getting a nonexistent embedding."""
        cache = EmbeddingCache()
        
        result = cache.get_embedding("nonexistent_key")
        assert result is None

    def test_dimension_validation(self):
        """Test embedding dimension validation."""
        cache = EmbeddingCache(max_dimensions=10)
        
        # Valid dimensions
        valid_embedding = [0.1] * 10
        cache.set_embedding("valid_key", valid_embedding)
        
        # Invalid dimensions
        invalid_embedding = [0.1] * 15  # Exceeds max_dimensions
        with pytest.raises(EmbeddingCacheError, match="exceed maximum"):
            cache.set_embedding("invalid_key", invalid_embedding)

    def test_cache_size_limit(self):
        """Test cache size limit enforcement."""
        cache = EmbeddingCache(max_size=2)
        
        # Add three embeddings to a cache with max size 2
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])
        cache.set_embedding("key3", [0.5, 0.6])
        
        # Should have evicted the oldest key
        assert cache.get_embedding("key1") is None
        assert cache.get_embedding("key2") is not None
        assert cache.get_embedding("key3") is not None

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = EmbeddingCache(ttl_seconds=0.001)  # Very short TTL
        
        cache.set_embedding("expiring_key", [0.1, 0.2, 0.3])
        
        # Wait for expiration
        import time
        time.sleep(0.002)  # Wait longer than TTL
        
        # Should be expired
        result = cache.get_embedding("expiring_key")
        assert result is None

    def test_calculate_similarity(self):
        """Test similarity calculation between embeddings."""
        cache = EmbeddingCache()
        
        # Set two embeddings
        emb1 = [0.5, 0.5, 0.5, 0.5]
        emb2 = [0.5, 0.5, 0.5, 0.5]  # Same as emb1
        emb3 = [0.1, 0.1, 0.1, 0.1]  # Different
        
        cache.set_embedding("key1", emb1)
        cache.set_embedding("key2", emb2)
        cache.set_embedding("key3", emb3)
        
        # Same embeddings should have similarity of 1.0
        similarity = cache.calculate_similarity("key1", "key2")
        assert similarity == 1.0
        
        # Different embeddings should have some similarity
        similarity = cache.calculate_similarity("key1", "key3")
        assert similarity is not None
        assert 0.0 <= similarity <= 1.0
        
        # Nonexistent key should return None
        similarity = cache.calculate_similarity("key1", "nonexistent")
        assert similarity is None

    def test_cosine_similarity_calculation(self):
        """Test cosine similarity calculation directly."""
        cache = EmbeddingCache()
        
        # Orthogonal vectors (should have similarity 0)
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = cache._cosine_similarity(vec1, vec2)
        assert similarity == 0.0
        
        # Identical vectors (should have similarity 1.0)
        vec1 = [1.0, 1.0]
        vec2 = [1.0, 1.0]
        similarity = cache._cosine_similarity(vec1, vec2)
        # Account for floating point precision - allow small tolerance
        assert abs(similarity - 1.0) < 1e-10
        
        # Opposite vectors (should have similarity 0 due to clamping)
        vec1 = [1.0, 1.0]
        vec2 = [-1.0, -1.0]
        similarity = cache._cosine_similarity(vec1, vec2)
        # This should be -1.0 but clamped to 0.0
        assert similarity == 0.0

    def test_invalid_dimension_similarity(self):
        """Test similarity calculation with different dimension embeddings."""
        cache = EmbeddingCache()
        
        emb1 = [0.1, 0.2]
        emb2 = [0.3, 0.4, 0.5]  # Different dimensions
        
        cache.set_embedding("small", emb1)
        cache.set_embedding("large", emb2)
        
        with pytest.raises(EmbeddingCacheError, match="dimensions must match"):
            cache.calculate_similarity("small", "large")

    def test_invalidate_entry(self):
        """Test invalidating a cache entry."""
        cache = EmbeddingCache()
        
        cache.set_embedding("test_key", [0.1, 0.2, 0.3])
        assert cache.get_embedding("test_key") is not None
        
        # Invalidate the entry
        result = cache.invalidate("test_key")
        assert result is True
        
        # Should no longer exist
        result = cache.get_embedding("test_key")
        assert result is None
        
        # Invalidating non-existent key should return False
        result = cache.invalidate("nonexistent")
        assert result is False

    def test_invalidate_all(self):
        """Test invalidating all cache entries."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])
        cache.set_embedding("key3", [0.5, 0.6])
        
        assert cache.get_cache_size() == 3
        
        cache.invalidate_all()
        
        assert cache.get_cache_size() == 0
        assert cache.get_embedding("key1") is None
        assert cache.get_embedding("key2") is None
        assert cache.get_embedding("key3") is None

    def test_validate_cache(self):
        """Test validating cache and removing stale entries."""
        cache = EmbeddingCache(ttl_seconds=0.001)  # Very short TTL
        
        cache.set_embedding("fresh_key", [0.1, 0.2])
        cache.set_embedding("stale_key", [0.3, 0.4])
        
        import time
        time.sleep(0.002)  # Wait for expiration
        
        # Add a fresh entry
        cache.set_embedding("new_key", [0.5, 0.6])
        
        # Validate cache - should remove stale entries
        removed_count = cache.validate_cache()
        assert removed_count == 2  # Both initially set entries were expired
        
        # Fresh and new entries should still be there
        assert cache.get_embedding("fresh_key") is None  # Was expired
        assert cache.get_embedding("stale_key") is None  # Was expired
        assert cache.get_embedding("new_key") is not None  # Was just added

    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = EmbeddingCache()
        
        stats = cache.get_stats()
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'evictions' in stats
        assert 'insertions' in stats
        assert 'size' in stats
        assert 'capacity' in stats
        assert 'hit_rate' in stats
        
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['evictions'] == 0
        assert stats['insertions'] == 0
        assert stats['size'] == 0
        assert stats['capacity'] == 1000
        assert stats['hit_rate'] == 0.0

    def test_is_cached(self):
        """Test is_cached method."""
        cache = EmbeddingCache()
        
        # Initially not cached
        assert cache.is_cached("nonexistent") is False
        
        # After setting
        cache.set_embedding("test_key", [0.1, 0.2])
        assert cache.is_cached("test_key") is True
        
        # After invalidating
        cache.invalidate("test_key")
        assert cache.is_cached("test_key") is False

    def test_resize_cache(self):
        """Test resizing cache."""
        cache = EmbeddingCache(max_size=3)
        
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])
        cache.set_embedding("key3", [0.5, 0.6])
        
        assert cache.get_cache_size() == 3
        
        # Resize to smaller size - should evict entries
        cache.resize(1)
        assert cache.get_cache_size() == 1  # Only the most recent entry remains
        assert cache.get_embedding("key1") is None
        assert cache.get_embedding("key2") is None
        assert cache.get_embedding("key3") is not None

    def test_memory_usage(self):
        """Test memory usage calculation."""
        cache = EmbeddingCache()
        
        # Initially no memory usage
        usage = cache.get_memory_usage()
        assert usage >= 0
        
        # Add some embeddings
        cache.set_embedding("key1", [0.1, 0.2, 0.3])
        cache.set_embedding("key2", [0.4, 0.5, 0.6])
        
        usage = cache.get_memory_usage()
        assert usage > 0

    def test_find_similar(self):
        """Test finding similar embeddings."""
        cache = EmbeddingCache()
        
        # Set some embeddings
        cache.set_embedding("reference", [1.0, 1.0, 1.0])
        cache.set_embedding("similar", [0.9, 0.9, 0.9])  # Very similar
        cache.set_embedding("different", [0.1, 0.1, 0.1])  # Very different
        cache.set_embedding("another", [1.0, 1.0, 1.0])  # Identical
        
        results = cache.find_similar("reference", threshold=0.5, max_results=10)
        
        # Should find similar embeddings
        assert len(results) >= 1  # At least the identical one
        for key, similarity in results:
            assert similarity >= 0.5

    def test_get_average_embedding(self):
        """Test getting average embedding from multiple embeddings."""
        cache = EmbeddingCache()
        
        # Set multiple embeddings
        cache.set_embedding("emb1", [1.0, 2.0, 3.0])
        cache.set_embedding("emb2", [3.0, 4.0, 5.0])
        cache.set_embedding("emb3", [5.0, 6.0, 7.0])
        
        avg = cache.get_average_embedding(["emb1", "emb2", "emb3"])
        assert avg is not None
        assert len(avg) == 3
        assert avg[0] == 3.0  # (1+3+5)/3
        assert avg[1] == 4.0  # (2+4+6)/3
        assert avg[2] == 5.0  # (3+5+7)/3
        
        # Test with non-existent keys
        avg = cache.get_average_embedding(["emb1", "nonexistent"])
        assert avg is not None  # Should work with partial results
        assert len(avg) == 3
        
        # Test with all non-existent keys
        avg = cache.get_average_embedding(["none1", "none2"])
        assert avg is None

    def test_clear_by_pattern(self):
        """Test clearing cache entries by pattern."""
        cache = EmbeddingCache()
        
        cache.set_embedding("test_file1", [0.1, 0.2])
        cache.set_embedding("test_file2", [0.3, 0.4])
        cache.set_embedding("other_file", [0.5, 0.6])
        cache.set_embedding("test_another", [0.7, 0.8])
        
        assert cache.get_cache_size() == 4
        
        # Clear entries matching "test"
        cleared = cache.clear_by_pattern("test")
        assert cleared == 3  # test_file1, test_file2, test_another
        
        assert cache.get_cache_size() == 1  # Only "other_file" remains
        assert cache.get_embedding("other_file") is not None

    def test_get_cached_keys(self):
        """Test getting all cached keys."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])
        cache.set_embedding("key3", [0.5, 0.6])
        
        keys = cache.get_cached_keys()
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys
        assert len(keys) == 3


def test_create_embedding_cache():
    """Test create_embedding_cache factory function."""
    cache = create_embedding_cache()
    assert isinstance(cache, EmbeddingCache)
    assert cache.max_size == 1000
    assert cache.ttl_seconds == 3600
    assert cache.max_dimensions == 1024
    
    # Test with custom parameters
    cache = create_embedding_cache(max_size=500, ttl_seconds=1800, max_dims=512)
    assert cache.max_size == 500
    assert cache.ttl_seconds == 1800
    assert cache.max_dimensions == 512


if __name__ == "__main__":
    pytest.main([__file__])
