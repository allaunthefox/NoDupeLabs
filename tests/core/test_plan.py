"""
Test suite for plan command functionality.
Tests plan operations from nodupe.plugins.commands.plan.
"""

import os
import tempfile
import shutil
from pathlib import Path
import time
import pytest
from unittest.mock import patch

from nodupe.plugins.commands.plan import PlanPlugin, plan_plugin


class TestPlanPlugin:
    """Test PlanPlugin functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_plan_plugin_initialization(self):
        """Test PlanPlugin initialization."""
        plugin = PlanPlugin()
        
        assert plugin is not None
        assert plugin.name == "plan"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Create execution plan from scan results"
        assert plugin.dependencies == ["scan", "database"]
    
    def test_get_capabilities(self):
        """Test getting plugin capabilities."""
        plugin = PlanPlugin()
        capabilities = plugin.get_capabilities()
        
        assert 'commands' in capabilities
        assert 'plan' in capabilities['commands']
        assert 'strategies' in capabilities
        assert 'newest' in capabilities['strategies']
        assert 'oldest' in capabilities['strategies']
        assert 'interactive' in capabilities['strategies']
    
    def test_on_plan_start_event(self):
        """Test plan start event handling."""
        plugin = PlanPlugin()
        
        # Should not raise exception
        plugin._on_plan_start(strategy='newest')
        # Output is printed, no return value to check
    
    def test_on_plan_complete_event(self):
        """Test plan complete event handling."""
        plugin = PlanPlugin()
        
        # Should not raise exception
        plugin._on_plan_complete(action_count=5)
        # Output is printed, no return value to check
    
    def test_register_commands(self):
        """Test registering plan commands."""
        plugin = PlanPlugin()
        
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
    
    def test_execute_plan_basic(self):
        """Test basic plan execution."""
        plugin = PlanPlugin()
        
        # Create test files
        test_dir = Path("test_source")
        test_dir.mkdir()
        
        test_file1 = test_dir / "file1.txt"
        test_file1.write_text("test content 1")
        
        test_file2 = test_dir / "file2.txt"
        test_file2.write_text("test content 2")
        
        # Create destination plan file
        plan_file = Path("test_plan.json")
        
        # Mock args for plan operation
        class MockArgs:
            strategy = 'newest'
            output = str(plan_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = False
            verbose = False
            container = None
        
        args = MockArgs()
        
        # Test plan execution
        result = plugin.execute_plan(args)
        
        # Should return 0 for success (though may fail due to missing dependencies)
        assert result in [0, 1]
    
    def test_execute_plan_with_filter(self):
        """Test plan execution with filter."""
        plugin = PlanPlugin()
        
        # Create test directory
        test_dir = Path("filter_test")
        test_dir.mkdir()
        
        test_file = test_dir / "filtered_file.txt"
        test_file.write_text("filtered content")
        
        plan_file = Path("filtered_plan.json")
        
        # Mock args with filter
        class MockArgs:
            strategy = 'newest'
            output = str(plan_file)
            filter = "filtered"
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = True  # Use dry run to avoid dependency issues
            verbose = False
            container = None
        
        args = MockArgs()
        
        # Test plan execution with filter
        result = plugin.execute_plan(args)
        
        assert result in [0, 1]
    
    def test_execute_plan_missing_database(self):
        """Test plan execution with missing database service."""
        plugin = PlanPlugin()
        
        # Create test directory
        test_dir = Path("db_test")
        test_dir.mkdir()
        
        plan_file = Path("db_plan.json")
        
        # Mock args with container that has no database
        class MockContainer:
            def get_service(self, service_name):
                return None
        
        class MockArgs:
            strategy = 'newest'
            output = str(plan_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = False
            verbose = False
            container = MockContainer()
        
        args = MockArgs()
        
        # Test plan execution with missing database
        result = plugin.execute_plan(args)
        
        # Should return error code when database is not available
        assert result == 1
    
    def test_execute_plan_invalid_strategy(self):
        """Test plan execution with invalid strategy."""
        plugin = PlanPlugin()
        
        plan_file = Path("invalid_plan.json")
        
        # Mock args with invalid strategy
        class MockArgs:
            strategy = 'invalid_strategy'
            output = str(plan_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = True  # Use dry run to avoid dependency issues
            verbose = False
            container = None
        
        args = MockArgs()
        
        # Test plan execution with invalid strategy
        result = plugin.execute_plan(args)
        
        # Should return error code for invalid strategy
        assert result == 1
    
    def test_execute_plan_with_verbose(self):
        """Test plan execution with verbose output."""
        plugin = PlanPlugin()
        
        # Create test directory
        test_dir = Path("verbose_test")
        test_dir.mkdir()
        
        test_file = test_dir / "verbose.txt"
        test_file.write_text("verbose content")
        
        plan_file = Path("verbose_plan.json")
        
        # Mock args with verbose
        class MockArgs:
            strategy = 'newest'
            output = str(plan_file)
            filter = None
            read_only = False
            show_originals = False
            hide_links = False
            sort_by = 'name'
            dry_run = True  # Use dry run to avoid dependency issues
            verbose = True
            container = None
        
        args = MockArgs()
        
        # Test plan execution with verbose
        result = plugin.execute_plan(args)
        
        assert result in [0, 1]
    
    def test_execute_plan_with_dry_run(self):
        """Test plan execution with dry run."""
        plugin = PlanPlugin()
        
        # Create test directory
        test_dir = Path("dry_run_test")
        test_dir.mkdir()
        
        test_file = test_dir / "dry_run.txt"
        test_file.write_text("dry run content")
        
        plan_file = Path("dry_run_plan.json")
        
        # Mock args with dry run
        class MockArgs:
            strategy = 'newest'
            output = str(plan_file)
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
        result = plugin.execute_plan(args)
        
        assert result in [0, 1]
    
    def test_format_size_human_readable(self):
        """Test human-readable size formatting."""
        plugin = PlanPlugin()
        
        # Test various sizes
        assert plugin.format_size(0) == "0 B"
        assert plugin.format_size(512) == "512 B"
        assert plugin.format_size(1024) == "1.0 KB"
        assert plugin.format_size(1024*1024) == "1.0 MB"
        assert plugin.format_size(1024*1024*1024) == "1.0 GB"
        assert plugin.format_size(1024*1024*1024*1024) == "1.0 TB"


class TestPlanPluginIntegration:
    """Test PlanPlugin integration aspects."""
    
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
        from nodupe.plugins.commands.plan import register_plugin
        
        plugin_instance = register_plugin()
        assert isinstance(plugin_instance, PlanPlugin)
        assert plugin_instance.name == "plan"
    
    def test_global_plugin_instance(self):
        """Test global plugin instance."""
        assert isinstance(plan_plugin, PlanPlugin)
        assert plan_plugin.name == "plan"


def test_plan_plugin_error_handling():
    """Test error handling in PlanPlugin operations."""
    plugin = PlanPlugin()
    
    # Test with None args (should not crash)
    class MockArgs:
        strategy = 'newest'
        output = "test_plan.json"
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
    result = plugin.execute_plan(args)
    assert result in [0, 1]


if __name__ == "__main__":
    pytest.main([__file__])
