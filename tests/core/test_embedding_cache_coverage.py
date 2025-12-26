"""Additional tests for embedding cache to achieve 100% coverage."""

import pytest
from nodupe.core.cache.embedding_cache import EmbeddingCache


class TestEmbeddingCacheCoverage:
    """Additional tests to achieve 100% coverage."""

    def test_get_average_embedding_empty_list(self):
        """Test get_average_embedding with empty key list."""
        cache = EmbeddingCache()
        
        # Test with empty list
        avg = cache.get_average_embedding([])
        assert avg is None

    def test_get_average_embedding_no_valid_keys(self):
        """Test get_average_embedding when no keys are found."""
        cache = EmbeddingCache()
        
        # Test with all non-existent keys
        avg = cache.get_average_embedding(["none1", "none2"])
        assert avg is None

    def test_get_average_embedding_partial_valid_keys(self):
        """Test get_average_embedding with some valid and some invalid keys."""
        cache = EmbeddingCache()
        
        # Set one embedding
        cache.set_embedding("valid_key", [1.0, 2.0, 3.0])
        
        # Test with mix of valid and invalid keys
        avg = cache.get_average_embedding(["valid_key", "invalid_key"])
        assert avg is not None
        assert len(avg) == 3
        assert avg == [1.0, 2.0, 3.0]  # Should be the same as the single valid embedding

    def test_clear_by_pattern_no_matches(self):
        """Test clear_by_pattern when no keys match the pattern."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])
        
        assert cache.get_cache_size() == 2
        
        # Clear with pattern that doesn't match
        cleared = cache.clear_by_pattern("nonexistent")
        assert cleared == 0
        
        assert cache.get_cache_size() == 2
        assert cache.get_embedding("key1") is not None
        assert cache.get_embedding("key2") is not None

    def test_clear_by_pattern_all_matches(self):
        """Test clear_by_pattern when all keys match the pattern."""
        cache = EmbeddingCache()
        
        cache.set_embedding("test1", [0.1, 0.2])
        cache.set_embedding("test2", [0.3, 0.4])
        cache.set_embedding("test3", [0.5, 0.6])
        
        assert cache.get_cache_size() == 3
        
        # Clear all entries
        cleared = cache.clear_by_pattern("test")
        assert cleared == 3
        
        assert cache.get_cache_size() == 0
        assert cache.get_embedding("test1") is None
        assert cache.get_embedding("test2") is None
        assert cache.get_embedding("test3") is None

    def test_get_cached_keys_empty_cache(self):
        """Test get_cached_keys when cache is empty."""
        cache = EmbeddingCache()
        
        keys = cache.get_cached_keys()
        assert keys == []

    def test_get_cached_keys_with_entries(self):
        """Test get_cached_keys when cache has entries."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])
        cache.set_embedding("key3", [0.5, 0.6])
        
        keys = cache.get_cached_keys()
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys

    def test_invalidate_all_with_empty_cache(self):
        """Test invalidate_all when cache is empty."""
        cache = EmbeddingCache()
        
        assert cache.get_cache_size() == 0
        
        cache.invalidate_all()
        
        assert cache.get_cache_size() == 0

    def test_invalidate_all_with_entries(self):
        """Test invalidate_all when cache has entries."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [0.1, 0.2])
        cache.set_embedding("key2", [0.3, 0.4])
        
        assert cache.get_cache_size() == 2
        
        cache.invalidate_all()
        
        assert cache.get_cache_size() == 0
        assert cache.get_embedding("key1") is None
        assert cache.get_embedding("key2") is None

    def test_get_average_embedding_single_key(self):
        """Test get_average_embedding with single key."""
        cache = EmbeddingCache()
        
        cache.set_embedding("single_key", [1.0, 2.0, 3.0])
        
        avg = cache.get_average_embedding(["single_key"])
        assert avg is not None
        assert len(avg) == 3
        assert avg == [1.0, 2.0, 3.0]

    def test_get_average_embedding_identical_keys(self):
        """Test get_average_embedding with identical embeddings."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 2.0, 3.0])
        cache.set_embedding("key2", [1.0, 2.0, 3.0])
        
        avg = cache.get_average_embedding(["key1", "key2"])
        assert avg is not None
        assert len(avg) == 3
        assert avg == [1.0, 2.0, 3.0]

    def test_clear_by_pattern_case_insensitive(self):
        """Test clear_by_pattern with case insensitive matching."""
        cache = EmbeddingCache()
        
        cache.set_embedding("TestFile1", [0.1, 0.2])
        cache.set_embedding("testfile2", [0.3, 0.4])
        cache.set_embedding("OTHER_FILE", [0.5, 0.6])
        
        assert cache.get_cache_size() == 3
        
        # Clear with lowercase pattern - should match both test files
        cleared = cache.clear_by_pattern("test")
        assert cleared == 2  # TestFile1 and testfile2
        
        assert cache.get_cache_size() == 1  # Only OTHER_FILE remains
        assert cache.get_embedding("OTHER_FILE") is not None
        assert cache.get_embedding("TestFile1") is None
        assert cache.get_embedding("testfile2") is None
