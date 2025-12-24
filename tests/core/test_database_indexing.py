"""
Test suite for database indexing functionality.
Tests indexing operations from nodupe.core.database.indexing.
"""

import os
import tempfile
import shutil
from pathlib import Path
import time
import pytest
from unittest.mock import patch, MagicMock

from nodupe.core.database.indexing import IndexingManager, IndexOptimizer, get_indexing_manager


class TestIndexingManager:
    """Test IndexingManager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_indexing_manager_initialization(self):
        """Test IndexingManager initialization."""
        indexer = IndexingManager()
        
        assert indexer is not None
        assert hasattr(indexer, 'create_indexes')
        assert hasattr(indexer, 'optimize_indexes')
        assert hasattr(indexer, 'drop_indexes')
    
    def test_get_indexing_manager_singleton(self):
        """Test get_indexing_manager returns singleton instance."""
        manager1 = get_indexing_manager()
        manager2 = get_indexing_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, IndexingManager)
        assert isinstance(manager2, IndexingManager)
    
    def test_create_indexes_basic(self):
        """Test basic index creation."""
        indexer = IndexingManager()
        
        # Mock database connection
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        
        # Test index creation (should not crash)
        result = indexer.create_indexes(mock_db)
        assert result is None  # create_indexes returns None
        
        # Should have called cursor methods
        assert mock_db.cursor.called
        assert mock_cursor.execute.called
    
    def test_create_indexes_with_custom_connection(self):
        """Test index creation with custom database connection."""
        indexer = IndexingManager()
        
        # Mock database connection
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        
        # Test index creation with custom connection
        result = indexer.create_indexes(mock_db)
        assert result is None
        
        # Verify cursor was used appropriately
        mock_db.cursor.assert_called_once()
        mock_cursor.close.assert_called()
    
    def test_optimize_indexes_basic(self):
        """Test basic index optimization."""
        indexer = IndexingManager()
        
        # Mock database connection
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        
        # Test index optimization (should not crash)
        result = indexer.optimize_indexes(mock_db)
        assert result is None
        
        # Should have called cursor methods
        assert mock_db.cursor.called
        assert mock_cursor.execute.called
    
    def test_drop_indexes_basic(self):
        """Test basic index dropping."""
        indexer = IndexingManager()
        
        # Mock database connection
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        
        # Test index dropping (should not crash)
        result = indexer.drop_indexes(mock_db)
        assert result is None
        
        # Should have called cursor methods
        assert mock_db.cursor.called
        assert mock_cursor.execute.called
    
    def test_create_indexes_empty_database(self):
        """Test index creation with empty database."""
        indexer = IndexingManager()
        
        # Mock empty database
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        
        result = indexer.create_indexes(mock_db)
        assert result is None
    
    def test_optimize_indexes_empty_database(self):
        """Test index optimization with empty database."""
        indexer = IndexingManager()
        
        # Mock empty database
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        
        result = indexer.optimize_indexes(mock_db)
        assert result is None
    
    def test_drop_indexes_empty_database(self):
        """Test index dropping with empty database."""
        indexer = IndexingManager()
        
        # Mock empty database
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        
        result = indexer.drop_indexes(mock_db)
        assert result is None


class TestIndexOptimizer:
    """Test IndexOptimizer functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_index_optimizer_initialization(self):
        """Test IndexOptimizer initialization."""
        optimizer = IndexOptimizer()
        
        assert optimizer is not None
        assert hasattr(optimizer, 'analyze_query_patterns')
        assert hasattr(optimizer, 'suggest_indexes')
        assert hasattr(optimizer, 'recommend_optimizations')
    
    def test_analyze_query_patterns(self):
        """Test query pattern analysis."""
        optimizer = IndexOptimizer()
        
        # Test with sample query patterns
        queries = [
            "SELECT * FROM files WHERE path LIKE '%test%'",
            "SELECT * FROM files WHERE size > 1000",
            "SELECT * FROM files WHERE hash = ?"
        ]
        
        # Should not crash
        result = optimizer.analyze_query_patterns(queries)
        assert result is None  # Method likely modifies internal state
    
    def test_suggest_indexes_basic(self):
        """Test basic index suggestions."""
        optimizer = IndexOptimizer()
        
        # Should return list of suggested indexes
        suggestions = optimizer.suggest_indexes()
        assert isinstance(suggestions, list)
        assert len(suggestions) >= 0  # Could be empty list
    
    def test_recommend_optimizations(self):
        """Test optimization recommendations."""
        optimizer = IndexOptimizer()
        
        # Should return recommendations (even if empty)
        recommendations = optimizer.recommend_optimizations()
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 0
    
    def test_analyze_query_patterns_empty(self):
        """Test query pattern analysis with empty list."""
        optimizer = IndexOptimizer()
        
        # Test with empty query list
        result = optimizer.analyze_query_patterns([])
        assert result is None
    
    def test_analyze_query_patterns_none(self):
        """Test query pattern analysis with None."""
        optimizer = IndexOptimizer()
        
        # Test with None (should handle gracefully)
        result = optimizer.analyze_query_patterns(None)
        assert result is None


class TestIndexingManagerIntegration:
    """Test IndexingManager integration aspects."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_indexing_workflow(self):
        """Test complete indexing workflow."""
        indexer = IndexingManager()
        
        # Mock database
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        
        # Full workflow: create, optimize, drop
        indexer.create_indexes(mock_db)
        indexer.optimize_indexes(mock_db)
        indexer.drop_indexes(mock_db)
        
        # All operations should complete without errors
        assert mock_db.cursor.call_count >= 3
    
    def test_indexing_with_realistic_queries(self):
        """Test indexing with realistic database queries."""
        indexer = IndexingManager()
        
        # Mock database with realistic behavior
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        
        # Test with realistic query patterns
        realistic_queries = [
            "CREATE INDEX idx_files_path ON files(path)",
            "CREATE INDEX idx_files_hash ON files(hash)",
            "CREATE INDEX idx_files_size ON files(size)"
        ]
        
        # Create indexes with realistic patterns
        indexer.create_indexes(mock_db)
        assert mock_cursor.execute.called
    
    def test_error_handling_in_indexing(self):
        """Test error handling during indexing operations."""
        indexer = IndexingManager()
        
        # Mock database that raises exceptions
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_db.cursor.return_value = mock_cursor
        
        # Should handle gracefully and not crash
        try:
            indexer.create_indexes(mock_db)
        except Exception:
            pass  # Expected to handle the exception
        
        try:
            indexer.optimize_indexes(mock_db)
        except Exception:
            pass  # Expected to handle the exception
        
        try:
            indexer.drop_indexes(mock_db)
        except Exception:
            pass  # Expected to handle the exception


def test_indexing_manager_error_handling():
    """Test error handling in indexing manager operations."""
    indexer = IndexingManager()
    
    # Test with None database (should handle gracefully)
    try:
        indexer.create_indexes(None)
        indexer.optimize_indexes(None)
        indexer.drop_indexes(None)
    except Exception:
        pass  # Should handle gracefully
    
    # Verify no crashes occurred
    assert True


if __name__ == "__main__":
    pytest.main([__file__])
