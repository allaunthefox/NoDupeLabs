# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""CLI Commands Tests - Individual command execution and functionality.

This module tests the specific CLI commands including:
- Scan command
- Apply command
- Similarity command
- Plugin commands
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from nodupe.core.main import CLIHandler
from nodupe.plugins.commands.scan import ScanPlugin
from nodupe.plugins.commands.apply import ApplyPlugin
from nodupe.plugins.commands.similarity import SimilarityPlugin

class TestScanCommand:
    """Test scan command functionality."""

    def test_scan_command_initialization(self):
        """Test scan plugin initialization."""
        plugin = ScanPlugin()
        assert plugin.name == "scan"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Scan directories for duplicate files"

    def test_scan_command_registration(self):
        """Test scan command registration."""
        mock_subparsers = MagicMock()
        plugin = ScanPlugin()
        plugin.register_commands(mock_subparsers)
        assert mock_subparsers.add_parser.called

    def test_scan_command_execution(self):
        """Test scan command execution with mock data."""
        # Create a temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file1 = os.path.join(temp_dir, "test1.txt")
            test_file2 = os.path.join(temp_dir, "test2.txt")

            with open(test_file1, "w") as f:
                f.write("test content")
            with open(test_file2, "w") as f:
                f.write("test content")

            # Mock the container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Mock the args
            args = MagicMock()
            args.paths = [temp_dir]
            args.min_size = 0
            args.max_size = None
            args.extensions = None
            args.exclude = None
            args.verbose = False
            args.container = mock_container

            # Execute scan
            plugin = ScanPlugin()
            result = plugin.execute_scan(args)

            # Should return 0 for success
            assert result == 0

class TestApplyCommand:
    """Test apply command functionality."""

    def test_apply_command_initialization(self):
        """Test apply plugin initialization."""
        plugin = ApplyPlugin()
        assert plugin.name == "apply"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Apply actions to duplicate files"

    def test_apply_command_registration(self):
        """Test apply command registration."""
        mock_subparsers = MagicMock()
        plugin = ApplyPlugin()
        plugin.register_commands(mock_subparsers)
        assert mock_subparsers.add_parser.called

    def test_apply_command_execution(self):
        """Test apply command execution with mock data."""
        # Create a temporary directory and test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file1 = os.path.join(temp_dir, "test1.txt")
            test_file2 = os.path.join(temp_dir, "test2.txt")

            with open(test_file1, "w") as f:
                f.write("test content")
            with open(test_file2, "w") as f:
                f.write("test content")

            # Create a duplicates JSON file
            duplicates_file = os.path.join(temp_dir, "duplicates.json")
            duplicates_data = {
                "files": [
                    {"path": test_file1, "size": 12, "hash": "abc123"},
                    {"path": test_file2, "size": 12, "hash": "abc123"}
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(duplicates_data, f)

            # Mock the args
            args = MagicMock()
            args.action = "list"
            args.input = duplicates_file
            args.target_dir = None
            args.dry_run = True
            args.verbose = False

            # Execute apply
            plugin = ApplyPlugin()
            result = plugin.execute_apply(args)

            # Should return 0 for success
            assert result == 0

class TestSimilarityCommand:
    """Test similarity command functionality."""

    def test_similarity_command_initialization(self):
        """Test similarity plugin initialization."""
        plugin = SimilarityPlugin()
        assert plugin.name == "similarity"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Find similar files using vector similarity search"

    def test_similarity_command_registration(self):
        """Test similarity command registration."""
        mock_subparsers = MagicMock()
        plugin = SimilarityPlugin()
        plugin.register_commands(mock_subparsers)
        assert mock_subparsers.add_parser.called

    def test_similarity_command_execution(self):
        """Test similarity command execution with mock data."""
        # Create a temporary directory and test file
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "query.txt")
            with open(test_file, "w") as f:
                f.write("query content")

            # Mock the args
            args = MagicMock()
            args.query_file = test_file
            args.database = None
            args.k = 5
            args.threshold = 0.8
            args.backend = "brute_force"
            args.output = "text"
            args.verbose = False

            # Execute similarity
            plugin = SimilarityPlugin()
            result = plugin.execute_similarity(args)

            # Should return 0 for success
            assert result == 0

class TestPluginCommands:
    """Test plugin command functionality."""

    def test_plugin_command_list(self):
        """Test plugin list command."""
        mock_loader = MagicMock()
        mock_plugin_registry = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.version = "1.0.0"
        mock_plugin_registry.get_plugins.return_value = [mock_plugin]

        mock_loader.plugin_registry = mock_plugin_registry

        cli = CLIHandler(mock_loader)

        # Mock args for plugin list command
        args = MagicMock()
        args.list = True

        # Execute plugin command
        result = cli._cmd_plugin(args)
        assert result == 0

    def test_plugin_command_no_list(self):
        """Test plugin command without list flag."""
        mock_loader = MagicMock()
        mock_plugin_registry = MagicMock()
        mock_plugin_registry.get_plugins.return_value = []

        mock_loader.plugin_registry = mock_plugin_registry

        cli = CLIHandler(mock_loader)

        # Mock args for plugin command without list
        args = MagicMock()
        args.list = False

        # Execute plugin command
        result = cli._cmd_plugin(args)
        assert result == 0

class TestCommandIntegration:
    """Test command integration scenarios."""

    def test_scan_apply_workflow(self):
        """Test scan and apply workflow integration."""
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

            # Test apply (list action)
            apply_plugin = ApplyPlugin()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = os.path.join(temp_dir, "duplicates.json")
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_plugin.execute_apply(apply_args)
            assert apply_result == 0

    def test_command_error_handling(self):
        """Test command error handling."""
        # Test scan with invalid path
        scan_plugin = ScanPlugin()
        scan_args = MagicMock()
        scan_args.paths = ["/nonexistent/path"]
        scan_args.min_size = 0
        scan_args.max_size = None
        scan_args.extensions = None
        scan_args.exclude = None
        scan_args.verbose = False
        scan_args.container = None

        scan_result = scan_plugin.execute_scan(scan_args)
        assert scan_result != 0

        # Test apply with invalid input file
        apply_plugin = ApplyPlugin()
        apply_args = MagicMock()
        apply_args.action = "list"
        apply_args.input = "/nonexistent/file.json"
        apply_args.target_dir = None
        apply_args.dry_run = True
        apply_args.verbose = False

        apply_result = apply_plugin.execute_apply(apply_args)
        assert apply_result != 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
