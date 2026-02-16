# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""CLI Commands Tests - Individual command execution and functionality.

This module tests the specific CLI commands including:
- Scan command
- Apply command
- Similarity command
- Tool commands
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from nodupe.core.main import CLIHandler
from nodupe.tools.commands.scan import ScanTool
from nodupe.tools.commands.apply import ApplyTool
from nodupe.tools.commands.similarity import SimilarityCommandTool as SimilarityTool

class TestScanCommand:
    """Test scan command functionality."""

    def test_scan_command_initialization(self):
        """Test scan tool initialization."""
        tool = ScanTool()
        assert tool.name == "scan"
        assert tool.version == "1.0.0"
        assert tool.description == "Scan directories for duplicate files"

    def test_scan_command_registration(self):
        """Test scan command registration."""
        mock_subparsers = MagicMock()
        tool = ScanTool()
        tool.register_commands(mock_subparsers)
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
            tool = ScanTool()
            result = tool.execute_scan(args)

            # Should return 0 for success
            assert result == 0

class TestApplyCommand:
    """Test apply command functionality."""

    def test_apply_command_initialization(self):
        """Test apply tool initialization."""
        tool = ApplyTool()
        assert tool.name == "apply"
        assert tool.version == "1.0.0"
        assert tool.description == "Apply actions to duplicate files"

    def test_apply_command_registration(self):
        """Test apply command registration."""
        mock_subparsers = MagicMock()
        tool = ApplyTool()
        tool.register_commands(mock_subparsers)
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
            tool = ApplyTool()
            result = tool.execute_apply(args)

            # Should return 0 for success
            assert result == 0

class TestSimilarityCommand:
    """Test similarity command functionality."""

    def test_similarity_command_initialization(self):
        """Test similarity tool initialization."""
        tool = SimilarityTool()
        assert tool.name == "similarity_command"
        assert tool.version == "1.0.0"
        assert tool.description == "Find similar files using various metrics"

    def test_similarity_command_registration(self):
        """Test similarity command registration."""
        mock_subparsers = MagicMock()
        tool = SimilarityTool()
        tool.register_commands(mock_subparsers)
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
            args.metric = "name"
            args.database = None
            args.k = 5
            args.threshold = 0.8
            args.backend = "brute_force"
            args.output = "text"
            args.verbose = False

            # Execute similarity
            tool = SimilarityTool()
            result = tool.execute_similarity(args)

            # Should return 0 for success
            assert result == 0

class TestToolCommands:
    """Test tool command functionality."""

    def test_tool_command_list(self):
        """Test tool list command."""
        mock_loader = MagicMock()
        mock_tool_registry = MagicMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.version = "1.0.0"
        mock_tool_registry.get_tools.return_value = [mock_tool]

        mock_loader.tool_registry = mock_tool_registry

        cli = CLIHandler(mock_loader)

        # Mock args for tool list command
        args = MagicMock()
        args.list = True

        # Execute tool command
        result = cli._cmd_tool(args)
        assert result == 0

    def test_tool_command_no_list(self):
        """Test tool command without list flag."""
        mock_loader = MagicMock()
        mock_tool_registry = MagicMock()
        mock_tool_registry.get_tools.return_value = []

        mock_loader.tool_registry = mock_tool_registry

        cli = CLIHandler(mock_loader)

        # Mock args for tool command without list
        args = MagicMock()
        args.list = False

        # Execute tool command
        result = cli._cmd_tool(args)
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
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_result = scan_tool.execute_scan(scan_args)
            assert scan_result == 0

            # Test apply (list action)
            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            # Create a dummy file to satisfy the check
            dummy_input = os.path.join(temp_dir, "dummy.json")
            with open(dummy_input, "w") as f:
                f.write("{}")
            apply_args.input = dummy_input
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_tool.execute_apply(apply_args)
            assert apply_result == 0

    def test_command_error_handling(self):
        """Test command error handling."""
        # Test scan with invalid path
        scan_tool = ScanTool()
        scan_args = MagicMock()
        scan_args.paths = ["/nonexistent/path"]
        scan_args.min_size = 0
        scan_args.max_size = None
        scan_args.extensions = None
        scan_args.exclude = None
        scan_args.verbose = False
        scan_args.container = None

        scan_result = scan_tool.execute_scan(scan_args)
        assert scan_result != 0

        # Test apply with invalid input file
        apply_tool = ApplyTool()
        apply_args = MagicMock()
        apply_args.action = "list"
        apply_args.input = "/nonexistent/file.json"
        apply_args.target_dir = None
        apply_args.dry_run = True
        apply_args.verbose = False

        apply_result = apply_tool.execute_apply(apply_args)
        assert apply_result != 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
