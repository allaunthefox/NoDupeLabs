"""Final tests to achieve 100% coverage for embedding cache."""

import pytest
from nodupe.core.cache.embedding_cache import EmbeddingCache


class TestEmbeddingCache100PercentFinal:
    """Final tests to achieve 100% coverage."""

    def test_get_average_embedding_empty_list_line_227(self):
        """Test line 227: return None when embeddings list is empty."""
        cache = EmbeddingCache()
        
        # This should trigger line 227: return None
        avg = cache.get_average_embedding([])
        assert avg is None

    def test_get_average_embedding_no_valid_embeddings_line_281(self):
        """Test line 281: return None when no valid embeddings found."""
        cache = EmbeddingCache()
        
        # This should trigger line 281: return None
        avg = cache.get_average_embedding(["nonexistent1", "nonexistent2"])
        assert avg is None

    def test_clear_by_pattern_returns_count_line_307(self):
        """Test line 307: clear_by_pattern returns len(keys_to_remove)."""
        cache = EmbeddingCache()
        
        # Add some embeddings
        cache.set_embedding("test1", [0.1, 0.2])
        cache.set_embedding("test2", [0.3, 0.4])
        cache.set_embedding("other", [0.5, 0.6])
        
        # Clear by pattern and verify return value (line 307)
        cleared_count = cache.clear_by_pattern("test")
        assert cleared_count == 2  # Should return the number of keys removed

    def test_get_cached_keys_returns_list_line_316(self):
        """Test line 316: get_cached_keys returns list(self._cache.keys())."""
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
