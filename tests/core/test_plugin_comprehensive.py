# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Comprehensive plugin system tests.

This module provides comprehensive testing for the plugin system,
covering all major scenarios and edge cases.
"""

import time
import pytest
from unittest.mock import Mock, patch
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.plugin_system.registry import PluginRegistry
from nodupe.core.plugin_system.loader import PluginLoader
from nodupe.plugins.commands.scan import ScanPlugin
from nodupe.plugins.commands.verify import VerifyPlugin

class TestPluginBaseClass:
    """Test the base Plugin class and its requirements."""

    def test_plugin_abstract_methods(self):
        """Test that Plugin abstract methods are properly defined."""
        # Verify that Plugin is abstract and requires implementation
        with pytest.raises(TypeError):
            Plugin()  # Should fail - can't instantiate abstract class

    def test_plugin_required_properties(self):
        """Test that plugins must implement required properties."""
        # These should be abstract properties that require implementation
        assert hasattr(Plugin, 'name')
        assert hasattr(Plugin, 'version')
        assert hasattr(Plugin, 'dependencies')

    def test_plugin_required_methods(self):
        """Test that plugins must implement required methods."""
        # These should be abstract methods that require implementation
        assert hasattr(Plugin, 'initialize')
        assert hasattr(Plugin, 'shutdown')
        assert hasattr(Plugin, 'teardown')
        assert hasattr(Plugin, 'get_capabilities')

class TestScanPlugin:
    """Comprehensive tests for ScanPlugin."""

    def test_scan_plugin_instantiation(self):
        """Test that ScanPlugin can be instantiated."""
        plugin = ScanPlugin()
        assert plugin is not None
        assert isinstance(plugin, Plugin)

    def test_scan_plugin_properties(self):
        """Test ScanPlugin properties."""
        plugin = ScanPlugin()
        assert plugin.name == "scan"
        assert plugin.version == "1.0.0"
        assert plugin.dependencies == []

    def test_scan_plugin_methods(self):
        """Test ScanPlugin method implementations."""
        plugin = ScanPlugin()

        # Test that all required methods exist and are callable
        assert hasattr(plugin, 'initialize')
        assert hasattr(plugin, 'shutdown')
        assert hasattr(plugin, 'teardown')
        assert hasattr(plugin, 'get_capabilities')
        assert hasattr(plugin, 'register_commands')
        assert hasattr(plugin, 'execute_scan')

        # Test method calls don't raise exceptions
        plugin.initialize(Mock())
        plugin.shutdown()
        plugin.teardown()

        capabilities = plugin.get_capabilities()
        assert 'commands' in capabilities
        assert 'scan' in capabilities['commands']

    def test_scan_plugin_command_registration(self):
        """Test ScanPlugin command registration."""
        plugin = ScanPlugin()
        mock_subparsers = Mock()

        # Test command registration
        plugin.register_commands(mock_subparsers)

        # Verify that add_parser was called
        mock_subparsers.add_parser.assert_called_once()
        call_args = mock_subparsers.add_parser.call_args
        assert call_args[0][0] == 'scan'
        assert 'Scan directories for duplicates' in call_args[1]['help']

    def test_scan_plugin_execute_scan_validation(self):
        """Test ScanPlugin execute_scan method validation."""
        plugin = ScanPlugin()

        # Test with no paths - should return error
        mock_args = Mock()
        mock_args.paths = []
        result = plugin.execute_scan(mock_args)
        assert result == 1  # Should return error code

        # Test with invalid paths - should return error
        mock_args.paths = ['/nonexistent/path']
        with patch('os.path.exists', return_value=False):
            result = plugin.execute_scan(mock_args)
            assert result == 1  # Should return error code

    def test_scan_plugin_execute_scan_success(self):
        """Test ScanPlugin execute_scan method success path."""
        plugin = ScanPlugin()

        # Mock all the dependencies and paths
        mock_args = Mock()
        mock_args.paths = ['/valid/path']
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False

        with patch('os.path.exists', return_value=True), \
             patch.object(plugin, '_on_scan_start'), \
             patch.object(plugin, '_on_scan_complete'), \
             patch('nodupe.plugins.commands.scan.FileRepository') as mock_repo_class:

            # Mock container and database
            mock_container = Mock()
            mock_db = Mock()
            mock_args.container = mock_container
            mock_container.get_service.return_value = mock_db

            # Mock the FileWalker and FileProcessor where they're actually used
            with patch('nodupe.plugins.commands.scan.FileWalker') as mock_walker_class, \
                 patch('nodupe.plugins.commands.scan.FileProcessor') as mock_processor_class:

                # Mock FileWalker instance
                mock_walker_instance = Mock()
                mock_walker_class.return_value = mock_walker_instance

                # Mock FileProcessor instance and its process_files method
                mock_processor_instance = Mock()
                mock_processor_class.return_value = mock_processor_instance
                mock_processor_instance.process_files.return_value = [
                    {'path': '/valid/path/file1.txt', 'size': 100, 'extension': '.txt', 'hash': 'abc123', 'modified_time': int(time.monotonic())},
                    {'path': '/valid/path/file2.txt', 'size': 200, 'extension': '.txt', 'hash': 'def456', 'modified_time': int(time.monotonic())}
                ]

                # Create mock repository instance
                mock_repo_instance = Mock()
                mock_repo_class.return_value = mock_repo_instance  # This mocks the constructor call
                mock_repo_instance.batch_add_files.return_value = 2  # Return number of files added

                # Execute scan
                result = plugin.execute_scan(mock_args)

                # Should succeed
                assert result == 0

                # Verify calls were made
                mock_container.get_service.assert_called_with('database')
                mock_processor_instance.process_files.assert_called_once()
                mock_repo_instance.batch_add_files.assert_called_once()
                mock_walker_class.assert_called_once() # Verify FileWalker was instantiated
                mock_processor_class.assert_called_once_with(mock_walker_instance)  # Verify FileProcessor was called with FileWalker instance

    def test_scan_plugin_execute_scan_with_filters(self):
        """Test ScanPlugin execute_scan method with various filters."""
        plugin = ScanPlugin()

        # Test with size filters
        mock_args = Mock()
        mock_args.paths = ['/valid/path']
        mock_args.min_size = 100
        mock_args.max_size = 1000
        mock_args.extensions = ['.txt', '.py']
        mock_args.exclude = ['/tmp']
        mock_args.verbose = True

        with patch('os.path.exists', return_value=True), \
             patch.object(plugin, '_on_scan_start'), \
             patch.object(plugin, '_on_scan_complete'), \
             patch('nodupe.plugins.commands.scan.FileRepository') as mock_repo_class:

            mock_container = Mock()
            mock_db = Mock()
            mock_args.container = mock_container
            mock_container.get_service.return_value = mock_db

            with patch('nodupe.plugins.commands.scan.FileWalker') as mock_walker_class, \
                 patch('nodupe.plugins.commands.scan.FileProcessor') as mock_processor_class:

                mock_walker_instance = Mock()
                mock_walker_class.return_value = mock_walker_instance

                mock_processor_instance = Mock()
                mock_processor_class.return_value = mock_processor_instance
                mock_processor_instance.process_files.return_value = [
                    {'path': '/valid/path/small.txt', 'size': 50, 'extension': '.txt', 'hash': 'small123', 'modified_time': int(time.monotonic())},
                    {'path': '/valid/path/big.py', 'size': 2000, 'extension': '.py', 'hash': 'big456', 'modified_time': int(time.monotonic())},
                    {'path': '/valid/path/valid.txt', 'size': 500, 'extension': '.txt', 'hash': 'valid789', 'modified_time': int(time.monotonic())}
                ]

                mock_repo_instance = Mock()
                mock_repo_class.return_value = mock_repo_instance
                mock_repo_instance.batch_add_files.return_value = 1  # Only valid file should be added

                result = plugin.execute_scan(mock_args)
                assert result == 0

    def test_scan_plugin_execute_scan_database_error(self):
        """Test ScanPlugin execute_scan method with database error."""
        plugin = ScanPlugin()

        mock_args = Mock()
        mock_args.paths = ['/valid/path']
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False

        with patch('os.path.exists', return_value=True), \
             patch.object(plugin, '_on_scan_start'), \
             patch.object(plugin, '_on_scan_complete'), \
             patch('nodupe.plugins.commands.scan.FileRepository') as mock_repo_class:

            mock_container = Mock()
            mock_db = Mock()
            mock_args.container = mock_container
            mock_container.get_service.return_value = mock_db

            with patch('nodupe.plugins.commands.scan.FileWalker'), \
                 patch('nodupe.plugins.commands.scan.FileProcessor') as mock_processor_class:

                mock_processor_instance = Mock()
                mock_processor_class.return_value = mock_processor_instance
                mock_processor_instance.process_files.return_value = [
                    {'path': '/valid/path/file.txt', 'size': 100, 'extension': '.txt', 'hash': 'abc123', 'modified_time': int(time.monotonic())}
                ]

                # Mock repository to raise an error
                mock_repo_instance = Mock()
                mock_repo_class.return_value = mock_repo_instance
                mock_repo_instance.batch_add_files.side_effect = RuntimeError("Database error")

                result = plugin.execute_scan(mock_args)
                assert result == 1  # Should return error code on database failure

    def test_scan_plugin_execute_scan_file_processing_error(self):
        """Test ScanPlugin execute_scan method with file processing error."""
        plugin = ScanPlugin()

        mock_args = Mock()
        mock_args.paths = ['/valid/path']
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False

        with patch('os.path.exists', return_value=True), \
             patch.object(plugin, '_on_scan_start'), \
             patch.object(plugin, '_on_scan_complete'), \
             patch('nodupe.plugins.commands.scan.FileRepository'), \
             patch('nodupe.plugins.commands.scan.FileProcessor') as mock_processor_class:

            mock_container = Mock()
            mock_db = Mock()
            mock_args.container = mock_container
            mock_container.get_service.return_value = mock_db

            mock_processor_instance = Mock()
            mock_processor_class.return_value = mock_processor_instance
            mock_processor_instance.process_files.side_effect = PermissionError("Permission denied")

            result = plugin.execute_scan(mock_args)
            assert result == 1  # Should return error code on processing failure

class TestVerifyPlugin:
    """Comprehensive tests for VerifyPlugin."""

    def test_verify_plugin_instantiation(self):
        """Test that VerifyPlugin can be instantiated."""
        plugin = VerifyPlugin()
        assert plugin is not None
        assert isinstance(plugin, Plugin)

    def test_verify_plugin_properties(self):
        """Test VerifyPlugin properties."""
        plugin = VerifyPlugin()
        assert plugin.name == "verify"
        assert plugin.version == "1.0.0"
        assert plugin.dependencies == ["database"]

    def test_verify_plugin_methods(self):
        """Test VerifyPlugin method implementations."""
        plugin = VerifyPlugin()

        # Test that all required methods exist and are callable
        assert hasattr(plugin, 'initialize')
        assert hasattr(plugin, 'shutdown')
        assert hasattr(plugin, 'teardown')
        assert hasattr(plugin, 'get_capabilities')
        assert hasattr(plugin, 'register_commands')
        assert hasattr(plugin, 'execute_verify')

        # Test method calls don't raise exceptions
        plugin.initialize(Mock())
        plugin.shutdown()
        plugin.teardown()

        capabilities = plugin.get_capabilities()
        assert 'commands' in capabilities
        assert 'verify' in capabilities['commands']

    def test_verify_plugin_command_registration(self):
        """Test VerifyPlugin command registration."""
        plugin = VerifyPlugin()
        mock_subparsers = Mock()

        # Test command registration
        plugin.register_commands(mock_subparsers)

        # Verify that add_parser was called
        mock_subparsers.add_parser.assert_called_once()
        call_args = mock_subparsers.add_parser.call_args
        assert call_args[0][0] == 'verify'
        assert 'Verify file integrity and database consistency' in call_args[1]['help']

    def test_verify_plugin_execute_verify_validation(self):
        """Test VerifyPlugin execute_verify method validation."""
        plugin = VerifyPlugin()

        # Test with no container - should return error
        mock_args = Mock()
        mock_args.mode = 'all'
        mock_args.fast = False
        mock_args.verbose = False
        mock_args.repair = False
        mock_args.output = None

        # No container - should fail
        result = plugin.execute_verify(mock_args)
        assert result == 1  # Should return error code

    def test_verify_plugin_execute_verify_success(self):
        """Test VerifyPlugin execute_verify method success path."""
        plugin = VerifyPlugin()

        # Mock all the dependencies
        mock_args = Mock()
        mock_args.mode = 'all'
        mock_args.fast = False
        mock_args.verbose = False
        mock_args.repair = False
        mock_args.output = None

        # Mock container and database
        mock_container = Mock()
        mock_db = Mock()
        mock_args.container = mock_container
        mock_container.get_service.return_value = mock_db

        with patch.object(plugin, '_on_verify_start'), \
             patch.object(plugin, '_on_verify_complete'), \
             patch.object(plugin, '_verify_integrity', return_value={'checks': 1, 'errors': 0, 'warnings': 0}), \
             patch.object(plugin, '_verify_consistency', return_value={'checks': 1, 'errors': 0, 'warnings': 0}), \
             patch.object(plugin, '_verify_checksums', return_value={'checks': 1, 'errors': 0, 'warnings': 0}), \
             patch('nodupe.core.database.files.FileRepository') as mock_repo:

            # Mock repository
            mock_repo_instance = Mock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.get_all_files.return_value = []
            mock_repo_instance.get_duplicate_files.return_value = []
            mock_repo_instance.get_file.return_value = None

            # Execute verify
            result = plugin.execute_verify(mock_args)

            # Should succeed
            assert result == 0

            # Verify calls were made
            mock_container.get_service.assert_called_with('database')
            plugin._verify_integrity.assert_called_once()
            plugin._verify_consistency.assert_called_once()
            plugin._verify_checksums.assert_called_once()

class TestPluginRegistry:
    """Test the PluginRegistry functionality."""

    def test_plugin_registry_instantiation(self):
        """Test PluginRegistry instantiation."""
        registry = PluginRegistry()
        assert registry is not None

    def test_plugin_registry_operations(self):
        """Test PluginRegistry basic operations."""
        registry = PluginRegistry()
        plugin = ScanPlugin()

        # Test registration
        registry.register_plugin(plugin)

        # Test retrieval
        retrieved = registry.get_plugin('scan')
        assert retrieved is not None
        assert retrieved.name == 'scan'

        # Test listing
        plugins = registry.get_all_plugins()
        assert len(plugins) == 1
        assert plugins[0].name == 'scan'

        # Test unregistration
        registry.unregister_plugin('scan')
        assert registry.get_plugin('scan') is None

class TestPluginLoader:
    """Test the PluginLoader functionality."""

    def test_plugin_loader_instantiation(self):
        """Test PluginLoader instantiation."""
        loader = PluginLoader()
        assert loader is not None

    def test_plugin_loader_discovery(self):
        """Test PluginLoader discovery functionality."""
        loader = PluginLoader()

        # Test that it can find plugins in the expected locations
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Test")
            plugins = loader.discover_plugins()
            # Should handle import errors gracefully
            assert isinstance(plugins, list)

class TestPluginErrorHandling:
    """Test plugin error handling scenarios."""

    def test_plugin_initialization_errors(self):
        """Test error handling during plugin initialization."""
        registry = PluginRegistry()

        # Test registering a broken plugin
        class BrokenPlugin(Plugin):
            def __init__(self):
                raise RuntimeError("Initialization failed")

            @property
            def name(self):
                return "broken"

            @property
            def version(self):
                return "1.0.0"

            @property
            def dependencies(self):
                return []

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def teardown(self):
                pass

            def get_capabilities(self):
                return {}

        # This should handle the error gracefully
        with pytest.raises(RuntimeError):
            broken_plugin = BrokenPlugin()

    def test_plugin_method_errors(self):
        """Test error handling during plugin method calls."""
        plugin = ScanPlugin()

        # Test error in execute_scan
        mock_args = Mock()
        mock_args.paths = []  # This should cause an error

        # Should handle the error and return error code
        result = plugin.execute_scan(mock_args)
        assert result == 1  # Error code

    def test_plugin_missing_dependencies(self):
        """Test error handling for missing dependencies."""
        plugin = VerifyPlugin()

        # Test with missing container
        mock_args = Mock()
        mock_args.mode = 'all'
        mock_args.fast = False
        mock_args.verbose = False
        mock_args.repair = False
        mock_args.output = None

        # No container - should handle gracefully
        result = plugin.execute_verify(mock_args)
        assert result == 1  # Error code

class TestPluginIntegration:
    """Test plugin integration scenarios."""

    def test_multiple_plugins_registration(self):
        """Test registration of multiple plugins."""
        registry = PluginRegistry()
        scan_plugin = ScanPlugin()
        verify_plugin = VerifyPlugin()

        # Register both plugins
        registry.register_plugin(scan_plugin)
        registry.register_plugin(verify_plugin)

        # Verify both are registered
        assert registry.get_plugin('scan') is not None
        assert registry.get_plugin('verify') is not None

        # Verify capabilities
        all_plugins = registry.get_all_plugins()
        assert len(all_plugins) == 2

        # Verify commands
        scan_commands = scan_plugin.get_capabilities()['commands']
        verify_commands = verify_plugin.get_capabilities()['commands']

        assert 'scan' in scan_commands
        assert 'verify' in verify_commands

    def test_plugin_lifecycle(self):
        """Test complete plugin lifecycle."""
        plugin = ScanPlugin()
        mock_container = Mock()

        # Test lifecycle methods
        plugin.initialize(mock_container)
        plugin.shutdown()
        plugin.teardown()

        # All should complete without errors
        assert True

    def test_plugin_command_integration(self):
        """Test plugin command integration with argument parser."""
        scan_plugin = ScanPlugin()
        verify_plugin = VerifyPlugin()

        # Mock argument parser
        mock_parser = Mock()
        mock_subparsers = Mock()
        mock_parser.add_subparsers.return_value = mock_subparsers

        # Register commands from both plugins
        scan_plugin.register_commands(mock_subparsers)
        verify_plugin.register_commands(mock_subparsers)

        # Verify both commands were registered
        assert mock_subparsers.add_parser.call_count == 2

        # Verify the commands that were registered
        calls = mock_subparsers.add_parser.call_args_list
        command_names = [call[0][0] for call in calls]
        assert 'scan' in command_names
        assert 'verify' in command_names

class TestPluginErrorScenarios:
    """Test various error scenarios in plugins."""

    def test_scan_plugin_file_errors(self):
        """Test ScanPlugin error handling for file operations."""
        plugin = ScanPlugin()

        mock_args = Mock()
        mock_args.paths = ['/valid/path']
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False

        # Mock container and database
        mock_container = Mock()
        mock_db = Mock()
        mock_args.container = mock_container
        mock_container.get_service.return_value = mock_db

        with patch('os.path.exists', return_value=True), \
             patch.object(plugin, '_on_scan_start'), \
             patch.object(plugin, '_on_scan_complete'), \
             patch('nodupe.core.scan.processor.FileProcessor') as mock_processor, \
             patch('nodupe.core.database.files.FileRepository') as mock_repo:

            # Mock processor to raise an exception
            mock_processor_instance = Mock()
            mock_processor.return_value = mock_processor_instance
            mock_processor_instance.process_files.side_effect = RuntimeError("Processing failed")

            # Execute scan - should handle error gracefully
            result = plugin.execute_scan(mock_args)
            assert result == 1  # Should return error code

    def test_verify_plugin_file_errors(self):
        """Test VerifyPlugin error handling for file operations."""
        plugin = VerifyPlugin()

        mock_args = Mock()
        mock_args.mode = 'all'
        mock_args.fast = False
        mock_args.verbose = False
        mock_args.repair = False
        mock_args.output = None

        # Mock container and database
        mock_container = Mock()
        mock_db = Mock()
        mock_args.container = mock_container
        mock_container.get_service.return_value = mock_db

        with patch.object(plugin, '_on_verify_start'), \
             patch.object(plugin, '_on_verify_complete'), \
             patch.object(plugin, '_verify_integrity'), \
             patch.object(plugin, '_verify_consistency'), \
             patch.object(plugin, '_verify_checksums'), \
             patch('nodupe.core.database.files.FileRepository') as mock_repo:

            # Mock repository to raise an exception
            mock_repo_instance = Mock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.get_all_files.side_effect = RuntimeError("Database error")

            # Execute verify - should handle error gracefully
            result = plugin.execute_verify(mock_args)
            assert result == 1  # Should return error code

    def test_plugin_invalid_arguments(self):
        """Test plugin handling of invalid arguments."""
        scan_plugin = ScanPlugin()
        verify_plugin = VerifyPlugin()

        # Test ScanPlugin with invalid arguments
        mock_args = Mock()
        mock_args.paths = None  # Invalid

        result = scan_plugin.execute_scan(mock_args)
        assert result == 1  # Should handle None paths

        # Test VerifyPlugin with invalid mode
        mock_args.mode = 'invalid_mode'
        mock_args.fast = False
        mock_args.verbose = False
        mock_args.repair = False
        mock_args.output = None
        mock_args.container = None

        result = verify_plugin.execute_verify(mock_args)
        assert result == 1  # Should handle invalid mode gracefully

class TestPluginPerformance:
    """Test plugin performance characteristics."""

    def test_scan_plugin_performance(self):
        """Test ScanPlugin performance without benchmark fixture."""
        plugin = ScanPlugin()

        mock_args = Mock()
        mock_args.paths = ['/valid/path']
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False

        # Mock all dependencies for performance test
        with patch('os.path.exists', return_value=True), \
             patch.object(plugin, '_on_scan_start'), \
             patch.object(plugin, '_on_scan_complete'), \
             patch('nodupe.core.scan.processor.FileProcessor') as mock_processor, \
             patch('nodupe.core.database.files.FileRepository') as mock_repo:

            mock_container = Mock()
            mock_db = Mock()
            mock_args.container = mock_container
            mock_container.get_service.return_value = mock_db

            mock_processor_instance = Mock()
            mock_processor.return_value = mock_processor_instance
            mock_processor_instance.process_files.return_value = []

            mock_repo_instance = Mock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.batch_add_files.return_value = 0

            # Test performance by executing the method
            start_time = time.time()
            result = plugin.execute_scan(mock_args)
            elapsed = time.time() - start_time

            # Should succeed and complete in reasonable time
            assert result == 0  # Should succeed
            assert elapsed < 5.0  # Should complete within 5 seconds

    def test_verify_plugin_performance(self):
        """Test VerifyPlugin performance without benchmark fixture."""
        plugin = VerifyPlugin()

        mock_args = Mock()
        mock_args.mode = 'all'
        mock_args.fast = False
        mock_args.verbose = False
        mock_args.repair = False
        mock_args.output = None

        # Mock all dependencies for performance test
        with patch.object(plugin, '_on_verify_start'), \
             patch.object(plugin, '_on_verify_complete'), \
             patch.object(plugin, '_verify_integrity', return_value={'checks': 1, 'errors': 0, 'warnings': 0}), \
             patch.object(plugin, '_verify_consistency', return_value={'checks': 1, 'errors': 0, 'warnings': 0}), \
             patch.object(plugin, '_verify_checksums', return_value={'checks': 1, 'errors': 0, 'warnings': 0}), \
             patch('nodupe.core.database.files.FileRepository') as mock_repo:

            mock_container = Mock()
            mock_db = Mock()
            mock_args.container = mock_container
            mock_container.get_service.return_value = mock_db

            mock_repo_instance = Mock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.get_all_files.return_value = []
            mock_repo_instance.get_duplicate_files.return_value = []
            mock_repo_instance.get_file.return_value = None

            # Test performance by executing the method
            start_time = time.time()
            result = plugin.execute_verify(mock_args)
            elapsed = time.time() - start_time

            # Should succeed and complete in reasonable time
            assert result == 0  # Should succeed
            assert elapsed < 5.0  # Should complete within 5 seconds

class TestPluginEdgeCases:
    """Test plugin edge cases and boundary conditions."""

    def test_scan_plugin_empty_paths(self):
        """Test ScanPlugin with empty paths list."""
        plugin = ScanPlugin()
        mock_args = Mock()
        mock_args.paths = []  # Empty list

        result = plugin.execute_scan(mock_args)
        assert result == 1  # Should return error for empty paths

    def test_scan_plugin_nonexistent_paths(self):
        """Test ScanPlugin with nonexistent paths."""
        plugin = ScanPlugin()
        mock_args = Mock()
        mock_args.paths = ['/nonexistent/path1', '/nonexistent/path2']

        with patch('os.path.exists', return_value=False):
            result = plugin.execute_scan(mock_args)
            assert result == 1  # Should return error for nonexistent paths

    def test_verify_plugin_empty_database(self):
        """Test VerifyPlugin with empty database."""
        plugin = VerifyPlugin()

        mock_args = Mock()
        mock_args.mode = 'all'
        mock_args.fast = False
        mock_args.verbose = False
        mock_args.repair = False
        mock_args.output = None

        mock_container = Mock()
        mock_db = Mock()
        mock_args.container = mock_container
        mock_container.get_service.return_value = mock_db

        with patch.object(plugin, '_on_verify_start'), \
             patch.object(plugin, '_on_verify_complete'), \
             patch.object(plugin, '_verify_integrity', return_value={'checks': 0, 'errors': 0, 'warnings': 0}), \
             patch.object(plugin, '_verify_consistency', return_value={'checks': 0, 'errors': 0, 'warnings': 0}), \
             patch.object(plugin, '_verify_checksums', return_value={'checks': 0, 'errors': 0, 'warnings': 0}), \
             patch('nodupe.core.database.files.FileRepository') as mock_repo:

            mock_repo_instance = Mock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.get_all_files.return_value = []  # Empty database

            result = plugin.execute_verify(mock_args)
            assert result == 0  # Should succeed with empty database

    def test_plugin_unicode_handling(self):
        """Test plugin handling of unicode characters."""
        scan_plugin = ScanPlugin()
        verify_plugin = VerifyPlugin()

        # Test with unicode paths
        mock_args = Mock()
        mock_args.paths = ['/path/with/unicode/文件.txt']

        with patch('os.path.exists', return_value=True), \
             patch.object(scan_plugin, '_on_scan_start'), \
             patch.object(scan_plugin, '_on_scan_complete'), \
             patch('nodupe.core.scan.processor.FileProcessor') as mock_processor, \
             patch('nodupe.core.database.files.FileRepository') as mock_repo:

            mock_container = Mock()
            mock_db = Mock()
            mock_args.container = mock_container
            mock_container.get_service.return_value = mock_db

            mock_processor_instance = Mock()
            mock_processor.return_value = mock_processor_instance
            mock_processor_instance.process_files.return_value = []

            mock_repo_instance = Mock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.batch_add_files.return_value = 0

            result = scan_plugin.execute_scan(mock_args)
            assert result == 0  # Should handle unicode paths

    def test_plugin_long_paths(self):
        """Test plugin handling of long file paths."""
        scan_plugin = ScanPlugin()

        # Test with very long path
        long_path = '/very/' + 'long/' * 50 + 'path.txt'
        mock_args = Mock()
        mock_args.paths = [long_path]

        with patch('os.path.exists', return_value=True), \
             patch.object(scan_plugin, '_on_scan_start'), \
             patch.object(scan_plugin, '_on_scan_complete'), \
             patch('nodupe.core.scan.processor.FileProcessor') as mock_processor, \
             patch('nodupe.core.database.files.FileRepository') as mock_repo:

            mock_container = Mock()
            mock_db = Mock()
            mock_args.container = mock_container
            mock_container.get_service.return_value = mock_db

            mock_processor_instance = Mock()
            mock_processor.return_value = mock_processor_instance
            mock_processor_instance.process_files.return_value = []

            mock_repo_instance = Mock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.batch_add_files.return_value = 0

            result = scan_plugin.execute_scan(mock_args)
            assert result == 0  # Should handle long paths

class TestPluginSecurity:
    """Test plugin security scenarios."""

    def test_plugin_permission_errors(self):
        """Test plugin handling of permission errors."""
        scan_plugin = ScanPlugin()

        mock_args = Mock()
        mock_args.paths = ['/restricted/path']

        with patch('os.path.exists', return_value=True), \
             patch('nodupe.core.scan.processor.FileProcessor') as mock_processor, \
             patch('nodupe.core.database.files.FileRepository') as mock_repo:

            mock_container = Mock()
            mock_db = Mock()
            mock_args.container = mock_container
            mock_container.get_service.return_value = mock_db

            # Mock processor to raise permission error
            mock_processor_instance = Mock()
            mock_processor.return_value = mock_processor_instance
            mock_processor_instance.process_files.side_effect = PermissionError("Access denied")

            result = scan_plugin.execute_scan(mock_args)
            assert result == 1  # Should handle permission error gracefully

    def test_plugin_invalid_plugin_registration(self):
        """Test handling of invalid plugin registration."""
        registry = PluginRegistry()

        # Try to register None
        with pytest.raises(ValueError):
            registry.register_plugin(None)

        # Try to register non-plugin object
        with pytest.raises(ValueError):
            registry.register_plugin("not a plugin")

    def test_plugin_method_validation(self):
        """Test validation of plugin methods."""
        scan_plugin = ScanPlugin()
        verify_plugin = VerifyPlugin()

        # Test that all required methods return expected types
        capabilities = scan_plugin.get_capabilities()
        assert isinstance(capabilities, dict)
        assert 'commands' in capabilities

        capabilities = verify_plugin.get_capabilities()
        assert isinstance(capabilities, dict)
        assert 'commands' in capabilities

        # Test that methods don't raise unexpected exceptions
        scan_plugin.initialize(Mock())
        scan_plugin.shutdown()
        scan_plugin.teardown()

        verify_plugin.initialize(Mock())
        verify_plugin.shutdown()
        verify_plugin.teardown()
