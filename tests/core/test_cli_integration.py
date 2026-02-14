# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""CLI Integration Tests - End-to-end workflows and system integration.

This module tests CLI integration scenarios including:
- End-to-end workflows
- Command chaining
- Plugin integration
- System integration
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from nodupe.core.main import main, CLIHandler
from nodupe.core.loader import bootstrap
from nodupe.plugins.commands.scan import ScanPlugin
from nodupe.plugins.commands.apply import ApplyPlugin
from nodupe.plugins.commands.similarity import SimilarityCommandPlugin as SimilarityPlugin

class TestCLIEndToEndWorkflows:
    """Test end-to-end CLI workflows."""

    def test_scan_apply_workflow_integration(self):
        """Test complete scan and apply workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file1 = os.path.join(temp_dir, "test1.txt")
            test_file2 = os.path.join(temp_dir, "test2.txt")

            with open(test_file1, "w") as f:
                f.write("test content")
            with open(test_file2, "w") as f:
                f.write("test content")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan
            scan_plugin = ScanPlugin()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_result = scan_plugin.execute_scan(scan_args)
            assert scan_result == 0

            # Create a mock duplicates file for apply
            duplicates_file = os.path.join(temp_dir, "duplicates.json")
            duplicates_data = {
                "files": [
                    {"path": test_file1, "size": 12, "hash": "abc123"},
                    {"path": test_file2, "size": 12, "hash": "abc123"}
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(duplicates_data, f)

            # Test apply
            apply_plugin = ApplyPlugin()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_plugin.execute_apply(apply_args)
            assert apply_result == 0

    def test_scan_similarity_workflow_integration(self):
        """Test scan and similarity workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file1 = os.path.join(temp_dir, "test1.txt")
            test_file2 = os.path.join(temp_dir, "test2.txt")
            query_file = os.path.join(temp_dir, "query.txt")

            with open(test_file1, "w") as f:
                f.write("test content")
            with open(test_file2, "w") as f:
                f.write("test content")
            with open(query_file, "w") as f:
                f.write("query content")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan
            scan_plugin = ScanPlugin()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_result = scan_plugin.execute_scan(scan_args)
            assert scan_result == 0

            # Test similarity
            similarity_plugin = SimilarityPlugin()
            similarity_args = MagicMock()
            similarity_args.query_file = query_file
            similarity_args.database = None
            similarity_args.k = 5
            similarity_args.threshold = 0.8
            similarity_args.backend = "brute_force"
            similarity_args.output = "text"
            similarity_args.verbose = False

            similarity_result = similarity_plugin.execute_similarity(similarity_args)
            assert similarity_result == 0

class TestCLICommandChaining:
    """Test command chaining scenarios."""

    def test_multiple_scan_commands(self):
        """Test multiple scan commands in sequence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test directories
            dir1 = os.path.join(temp_dir, "dir1")
            dir2 = os.path.join(temp_dir, "dir2")
            os.makedirs(dir1)
            os.makedirs(dir2)

            # Create test files
            with open(os.path.join(dir1, "test1.txt"), "w") as f:
                f.write("test content")
            with open(os.path.join(dir2, "test2.txt"), "w") as f:
                f.write("test content")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test multiple scans
            scan_plugin = ScanPlugin()

            for scan_dir in [dir1, dir2]:
                scan_args = MagicMock()
                scan_args.paths = [scan_dir]
                scan_args.min_size = 0
                scan_args.max_size = None
                scan_args.extensions = None
                scan_args.exclude = None
                scan_args.verbose = False
                scan_args.container = mock_container

                scan_result = scan_plugin.execute_scan(scan_args)
                assert scan_result == 0

    def test_scan_apply_chain(self):
        """Test scan followed by apply command chain."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file1 = os.path.join(temp_dir, "test1.txt")
            test_file2 = os.path.join(temp_dir, "test2.txt")

            with open(test_file1, "w") as f:
                f.write("test content")
            with open(test_file2, "w") as f:
                f.write("test content")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan
            scan_plugin = ScanPlugin()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_result = scan_plugin.execute_scan(scan_args)
            assert scan_result == 0

            # Create duplicates file
            duplicates_file = os.path.join(temp_dir, "duplicates.json")
            duplicates_data = {
                "files": [
                    {"path": test_file1, "size": 12, "hash": "abc123"},
                    {"path": test_file2, "size": 12, "hash": "abc123"}
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(duplicates_data, f)

            # Test apply with different actions
            apply_plugin = ApplyPlugin()

            for action in ["list", "delete", "move"]:
                apply_args = MagicMock()
                apply_args.action = action
                apply_args.input = duplicates_file
                apply_args.target_dir = temp_dir if action != "list" else None
                apply_args.dry_run = True
                apply_args.verbose = False

                apply_result = apply_plugin.execute_apply(apply_args)
                assert apply_result == 0

class TestCLIPluginIntegration:
    """Test CLI plugin integration."""

    def test_plugin_command_registration(self):
        """Test plugin command registration with CLI."""
        # Create mock plugins
        mock_plugin1 = MagicMock()
        mock_plugin1.name = "test_plugin1"
        mock_plugin1.register_commands = MagicMock()

        mock_plugin2 = MagicMock()
        mock_plugin2.name = "test_plugin2"
        mock_plugin2.register_commands = MagicMock()

        # Create mock loader with plugins
        mock_loader = MagicMock()
        mock_plugin_registry = MagicMock()
        mock_plugin_registry.get_plugins.return_value = [mock_plugin1, mock_plugin2]
        mock_loader.plugin_registry = mock_plugin_registry

        # Create CLI handler
        cli = CLIHandler(mock_loader)

        # Verify plugins were asked to register commands
        assert mock_plugin1.register_commands.called
        assert mock_plugin2.register_commands.called

    def test_plugin_command_execution(self):
        """Test plugin command execution."""
        # Create a real scan plugin
        scan_plugin = ScanPlugin()

        # Create mock loader with scan plugin
        mock_loader = MagicMock()
        mock_plugin_registry = MagicMock()
        mock_plugin_registry.get_plugins.return_value = [scan_plugin]
        mock_loader.plugin_registry = mock_plugin_registry

        # Create CLI handler
        cli = CLIHandler(mock_loader)

        # Verify the plugin registered commands
        assert scan_plugin.register_commands.called

    def test_multiple_plugins_integration(self):
        """Test integration with multiple plugins."""
        # Create multiple real plugins
        scan_plugin = ScanPlugin()
        apply_plugin = ApplyPlugin()
        similarity_plugin = SimilarityPlugin()

        # Create mock loader with plugins
        mock_loader = MagicMock()
        mock_plugin_registry = MagicMock()
        mock_plugin_registry.get_plugins.return_value = [scan_plugin, apply_plugin, similarity_plugin]
        mock_loader.plugin_registry = mock_plugin_registry

        # Create CLI handler
        cli = CLIHandler(mock_loader)

        # Verify all plugins registered commands
        assert scan_plugin.register_commands.called
        assert apply_plugin.register_commands.called
        assert similarity_plugin.register_commands.called

class TestCLISystemIntegration:
    """Test CLI system integration."""

    def test_cli_with_real_bootstrap(self):
        """Test CLI with real bootstrap system."""
        # Test version command with real bootstrap
        with patch('sys.argv', ['nodupe', 'version']):
            result = main()
            assert result == 0

        # Test plugin command with real bootstrap
        with patch('sys.argv', ['nodupe', 'plugin', '--list']):
            result = main()
            assert result == 0

    def test_cli_error_handling_integration(self):
        """Test CLI error handling with real system."""
        # Test invalid command
        with patch('sys.argv', ['nodupe', 'invalid_command']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code != 0

        # Test missing arguments
        with patch('sys.argv', ['nodupe', 'scan']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code != 0

    def test_cli_help_integration(self):
        """Test CLI help system integration."""
        # Test main help
        with patch('sys.argv', ['nodupe', '--help']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0

        # Test version help
        with patch('sys.argv', ['nodupe', 'version', '--help']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0

        # Test plugin help
        with patch('sys.argv', ['nodupe', 'plugin', '--help']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0

class TestCLIPerformanceIntegration:
    """Test CLI performance-related integration."""

    def test_performance_overrides_integration(self):
        """Test performance override flags integration."""
        # Test cores override
        with patch('sys.argv', ['nodupe', '--cores', '8', 'version']):
            result = main()
            assert result == 0

        # Test max-workers override
        with patch('sys.argv', ['nodupe', '--max-workers', '16', 'version']):
            result = main()
            assert result == 0

        # Test batch-size override
        with patch('sys.argv', ['nodupe', '--batch-size', '500', 'version']):
            result = main()
            assert result == 0

    def test_debug_logging_integration(self):
        """Test debug logging integration."""
        # Test debug flag
        with patch('sys.argv', ['nodupe', '--debug', 'version']):
            result = main()
            assert result == 0

        # Test debug with plugin command
        with patch('sys.argv', ['nodupe', '--debug', 'plugin', '--list']):
            result = main()
            assert result == 0

class TestCLIComplexScenarios:
    """Test complex CLI scenarios."""

    def test_large_directory_scan(self):
        """Test scan with large directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a large directory structure
            for i in range(10):
                subdir = os.path.join(temp_dir, f"subdir_{i}")
                os.makedirs(subdir)

                for j in range(5):
                    test_file = os.path.join(subdir, f"test_{j}.txt")
                    with open(test_file, "w") as f:
                        f.write(f"test content {i}_{j}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan
            scan_plugin = ScanPlugin()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_result = scan_plugin.execute_scan(scan_args)
            assert scan_result == 0

    def test_complex_file_types(self):
        """Test scan with various file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with different extensions
            file_types = [
                ("test.txt", "text content"),
                ("test.json", '{"key": "value"}'),
                ("test.csv", "col1,col2\nval1,val2"),
                ("test.py", "print('hello')"),
                ("test.md", "# Test File")
            ]

            for filename, content in file_types:
                filepath = os.path.join(temp_dir, filename)
                with open(filepath, "w") as f:
                    f.write(content)

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan with specific extensions
            scan_plugin = ScanPlugin()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = ["txt", "json", "py"]
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_result = scan_plugin.execute_scan(scan_args)
            assert scan_result == 0

    def test_complex_workflow(self):
        """Test complex workflow with multiple commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(3):
                test_file = os.path.join(temp_dir, f"test_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"test content {i}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan
            scan_plugin = ScanPlugin()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_result = scan_plugin.execute_scan(scan_args)
            assert scan_result == 0

            # Create duplicates file
            duplicates_file = os.path.join(temp_dir, "duplicates.json")
            duplicates_data = {
                "files": [
                    {"path": os.path.join(temp_dir, "test_0.txt"), "size": 14, "hash": "abc123"},
                    {"path": os.path.join(temp_dir, "test_1.txt"), "size": 14, "hash": "def456"},
                    {"path": os.path.join(temp_dir, "test_2.txt"), "size": 14, "hash": "ghi789"}
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(duplicates_data, f)

            # Test apply with different actions
            apply_plugin = ApplyPlugin()

            for action in ["list", "delete", "move"]:
                apply_args = MagicMock()
                apply_args.action = action
                apply_args.input = duplicates_file
                apply_args.target_dir = temp_dir if action != "list" else None
                apply_args.dry_run = True
                apply_args.verbose = False

                apply_result = apply_plugin.execute_apply(apply_args)
                assert apply_result == 0

            # Test similarity
            query_file = os.path.join(temp_dir, "query.txt")
            with open(query_file, "w") as f:
                f.write("query content")

            similarity_plugin = SimilarityPlugin()
            similarity_args = MagicMock()
            similarity_args.query_file = query_file
            similarity_args.database = None
            similarity_args.k = 3
            similarity_args.threshold = 0.7
            similarity_args.backend = "brute_force"
            similarity_args.output = "text"
            similarity_args.verbose = False

            similarity_result = similarity_plugin.execute_similarity(similarity_args)
            assert similarity_result == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
