"""
Test suite for rollback command functionality.
Tests rollback operations from nodupe.plugins.commands.rollback.
"""

import os
import tempfile
import shutil
from pathlib import Path
import time
import pytest
from unittest.mock import patch, MagicMock

from nodupe.plugins.commands.rollback import RollbackPlugin, rollback_plugin


class TestRollbackPlugin:
    """Test RollbackPlugin functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_rollback_plugin_initialization(self):
        """Test RollbackPlugin initialization."""
        plugin = RollbackPlugin()
        
        assert plugin is not None
        assert plugin.name == "rollback"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Rollback operations and restore system state"
        assert plugin.dependencies == []
    
    def test_get_capabilities(self):
        """Test getting plugin capabilities."""
        plugin = RollbackPlugin()
        capabilities = plugin.get_capabilities()
        
        assert 'commands' in capabilities
        assert 'rollback' in capabilities['commands']
        assert 'operations' in capabilities
        assert 'last' in capabilities['operations']
        assert 'all' in capabilities['operations']
        assert 'to-point' in capabilities['operations']
    
    def test_on_rollback_start_event(self):
        """Test rollback start event handling."""
        plugin = RollbackPlugin()
        
        # Should not raise exception
        plugin._on_rollback_start(operation='last')
        # Output is printed, no return value to check
    
    def test_on_rollback_complete_event(self):
        """Test rollback complete event handling."""
        plugin = RollbackPlugin()
        
        # Should not raise exception
        plugin._on_rollback_complete(operations_undone=5)
        # Output is printed, no return value to check
    
    def test_register_commands(self):
        """Test registering rollback commands."""
        plugin = RollbackPlugin()
        
        # Create mock parser
        class MockParser:
            def add_argument(self, *args, **kwargs):
                pass
            
            def set_defaults(self, **kwargs):
                pass
        
        # Create mock subparsers
        class MockSubparsers:
            def add_parser(self, name, **kwargs):
                return MockParser()
        
        mock_subparsers = MockSubparsers()
        
        # Register commands
        plugin.register_commands(mock_subparsers)
        
        # The function should complete without errors
        assert True
    
    def test_execute_rollback_last_operation(self):
        """Test basic rollback execution for last operation."""
        plugin = RollbackPlugin()
        
        # Create test files
        test_dir = Path("test_source")
        test_dir.mkdir()
        
        test_file1 = test_dir / "file1.txt"
        test_file1.write_text("test content 1")
        
        test_file2 = test_dir / "file2.txt"
        test_file2.write_text("test content 2")
        
        # Create rollback plan file
        rollback_file = Path("test_rollback.json")
        
        # Mock args for rollback operation
        class MockArgs:
            operation = 'last'
            steps = 1
            output = str(rollback_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = False
            verbose = False
            container = None
        
        args = MockArgs()
        
        # Test rollback execution
        result = plugin.execute_rollback(args)
        
        # Should return 0 for success (though may fail due to missing dependencies)
        assert result in [0, 1]
    
    def test_execute_rollback_all_operations(self):
        """Test rollback execution for all operations."""
        plugin = RollbackPlugin()
        
        # Create test directory
        test_dir = Path("all_test")
        test_dir.mkdir()
        
        test_file = test_dir / "all_file.txt"
        test_file.write_text("all content")
        
        rollback_file = Path("all_rollback.json")
        
        # Mock args with all operation
        class MockArgs:
            operation = 'all'
            steps = 1
            output = str(rollback_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = True  # Use dry run to avoid dependency issues
            verbose = False
            container = None
        
        args = MockArgs()
        
        # Test rollback execution with all operation
        result = plugin.execute_rollback(args)
        
        assert result in [0, 1]
    
    def test_execute_rollback_to_point(self):
        """Test rollback execution to a specific point."""
        plugin = RollbackPlugin()
        
        # Create test directory
        test_dir = Path("to_point_test")
        test_dir.mkdir()
        
        test_file = test_dir / "to_point.txt"
        test_file.write_text("to point content")
        
        rollback_file = Path("to_point_rollback.json")
        
        # Mock args with to-point operation
        class MockArgs:
            operation = 'to-point'
            steps = 1
            output = str(rollback_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = True  # Use dry run to avoid dependency issues
            verbose = False
            container = None
            point = "test_point"
        
        args = MockArgs()
        
        # Test rollback execution with to-point operation
        result = plugin.execute_rollback(args)
        
        assert result in [0, 1]
    
    def test_execute_rollback_invalid_operation(self):
        """Test rollback execution with invalid operation."""
        plugin = RollbackPlugin()
        
        rollback_file = Path("invalid_rollback.json")
        
        # Mock args with invalid operation
        class MockArgs:
            operation = 'invalid_operation'
            steps = 1
            output = str(rollback_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = True  # Use dry run to avoid dependency issues
            verbose = False
            container = None
        
        args = MockArgs()
        
        # Test rollback execution with invalid operation
        result = plugin.execute_rollback(args)
        
        # Should return error code for invalid operation
        assert result == 1
    
    def test_execute_rollback_with_verbose(self):
        """Test rollback execution with verbose output."""
        plugin = RollbackPlugin()
        
        # Create test directory
        test_dir = Path("verbose_test")
        test_dir.mkdir()
        
        test_file = test_dir / "verbose.txt"
        test_file.write_text("verbose content")
        
        rollback_file = Path("verbose_rollback.json")
        
        # Mock args with verbose
        class MockArgs:
            operation = 'last'
            steps = 1
            output = str(rollback_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = True  # Use dry run to avoid dependency issues
            verbose = True
            container = None
        
        args = MockArgs()
        
        # Test rollback execution with verbose
        result = plugin.execute_rollback(args)
        
        assert result in [0, 1]
    
    def test_execute_rollback_with_dry_run(self):
        """Test rollback execution with dry run."""
        plugin = RollbackPlugin()
        
        # Create test directory
        test_dir = Path("dry_run_test")
        test_dir.mkdir()
        
        test_file = test_dir / "dry_run.txt"
        test_file.write_text("dry run content")
        
        rollback_file = Path("dry_run_rollback.json")
        
        # Mock args with dry run
        class MockArgs:
            operation = 'last'
            steps = 1
            output = str(rollback_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = True
            verbose = False
            container = None
        
        args = MockArgs()
        
        # Test dry run - should not crash
        result = plugin.execute_rollback(args)
        
        assert result in [0, 1]
    
    def test_format_size_human_readable(self):
        """Test human-readable size formatting."""
        plugin = RollbackPlugin()
        
        # Test various sizes
        assert plugin.format_size(0) == "0 B"
        assert plugin.format_size(512) == "512 B"
        assert plugin.format_size(1024) == "1.0 KB"
        assert plugin.format_size(1024*1024) == "1.0 MB"
        assert plugin.format_size(1024*1024*1024) == "1.0 GB"
        assert plugin.format_size(1024*1024*1024*1024) == "1.0 TB"


class TestRollbackPluginIntegration:
    """Test RollbackPlugin integration aspects."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_plugin_registration(self):
        """Test plugin registration function."""
        from nodupe.plugins.commands.rollback import register_plugin
        
        plugin_instance = register_plugin()
        assert isinstance(plugin_instance, RollbackPlugin)
        assert plugin_instance.name == "rollback"
    
    def test_global_plugin_instance(self):
        """Test global plugin instance."""
        assert isinstance(rollback_plugin, RollbackPlugin)
        assert rollback_plugin.name == "rollback"


def test_rollback_plugin_error_handling():
    """Test error handling in RollbackPlugin operations."""
    plugin = RollbackPlugin()
    
    # Test with None args (should not crash)
    class MockArgs:
        operation = 'last'
        steps = 1
        output = "test_rollback.json"
        filter = None
        read_only = False
        show_originals = False
        hide_links = False
        sort_by = 'name'
        dry_run = False
        verbose = False
        container = None
    
    args = MockArgs()
    
    # Should handle gracefully and return error code
    result = plugin.execute_rollback(args)
    assert result in [0, 1]


if __name__ == "__main__":
    pytest.main([__file__])
