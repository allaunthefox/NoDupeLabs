"""Final tests to achieve 100% coverage for embedding cache."""

import pytest
from nodupe.core.cache.embedding_cache import EmbeddingCache


class TestEmbeddingCacheFinalCoverage:
    """Final tests to achieve 100% coverage."""

    def test_get_average_embedding_empty_embeddings_list(self):
        """Test get_average_embedding when embeddings list is empty (line 227)."""
        cache = EmbeddingCache()
        
        # This should trigger the empty embeddings list case
        avg = cache.get_average_embedding([])
        assert avg is None

    def test_get_average_embedding_no_valid_embeddings_found(self):
        """Test get_average_embedding when no valid embeddings are found (line 281)."""
        cache = EmbeddingCache()
        
        # Test with all non-existent keys - should trigger the no embeddings found case
        avg = cache.get_average_embedding(["nonexistent1", "nonexistent2"])
        assert avg is None

    def test_clear_by_pattern_returns_count(self):
        """Test that clear_by_pattern returns the correct count (line 307)."""
        cache = EmbeddingCache()
        
        # Add some embeddings
        cache.set_embedding("test1", [0.1, 0.2])
        cache.set_embedding("test2", [0.3, 0.4])
        cache.set_embedding("other", [0.5, 0.6])
        
        # Clear by pattern and verify return value
        cleared_count = cache.clear_by_pattern("test")
        assert cleared_count == 2  # Should return the number of keys removed
        
        # Verify the count is correct
        assert cache.get_cache_size() == 1
        assert cache.get_embedding("other") is not None

    def test_get_cached_keys_returns_list(self):
        """Test that get_cached_keys returns a list (line 316)."""
        cache = EmbeddingCache()
        
        # Test with empty cache
        keys = cache.get_cached_keys()
        assert isinstance(keys, list)
        assert keys == []
        
        # Test with populated cache
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])
        
        keys = cache.get_cached_keys()
        assert isinstance(keys, list)
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys
