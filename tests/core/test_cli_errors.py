# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""CLI Error Handling Tests - Error conditions and edge cases.

This module tests CLI error handling including:
- Invalid arguments
- Missing required arguments
- File system errors
- Permission errors
- Command validation
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from nodupe.core.main import CLIHandler
from nodupe.plugins.commands.scan import ScanPlugin
from nodupe.plugins.commands.apply import ApplyPlugin
from nodupe.plugins.commands.similarity import SimilarityCommandPlugin as SimilarityPlugin

class TestCLIArgumentValidation:
    """Test CLI argument validation errors."""

    def test_scan_missing_paths(self):
        """Test scan command with missing paths."""
        scan_plugin = ScanPlugin()

        # Mock args without paths
        args = MagicMock()
        args.paths = []  # Empty paths

        # This should fail validation
        result = scan_plugin.execute_scan(args)
        assert result != 0

    def test_apply_missing_input(self):
        """Test apply command with missing input file."""
        apply_plugin = ApplyPlugin()

        # Mock args without input
        args = MagicMock()
        args.action = "list"
        args.input = None  # Missing input

        # This should fail validation
        result = apply_plugin.execute_apply(args)
        assert result != 0

    def test_similarity_missing_query_file(self):
        """Test similarity command with missing query file."""
        similarity_plugin = SimilarityPlugin()

        # Mock args without query file
        args = MagicMock()
        args.query_file = None  # Missing query file

        # This should fail validation
        result = similarity_plugin.execute_similarity(args)
        assert result != 0

    def test_apply_invalid_action(self):
        """Test apply command with invalid action."""
        apply_plugin = ApplyPlugin()

        # Mock args with invalid action
        args = MagicMock()
        args.action = "invalid_action"
        args.input = "/nonexistent/file.json"
        args.target_dir = None
        args.dry_run = True
        args.verbose = False

        # This should fail validation
        result = apply_plugin.execute_apply(args)
        assert result != 0

class TestCLIFileSystemErrors:
    """Test CLI file system error handling."""

    def test_scan_nonexistent_directory(self):
        """Test scan command with nonexistent directory."""
        scan_plugin = ScanPlugin()

        # Mock args with nonexistent path
        args = MagicMock()
        args.paths = ["/nonexistent/directory"]
        args.min_size = 0
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = False
        args.container = None

        # This should fail
        result = scan_plugin.execute_scan(args)
        assert result != 0

    def test_apply_nonexistent_input_file(self):
        """Test apply command with nonexistent input file."""
        apply_plugin = ApplyPlugin()

        # Mock args with nonexistent input file
        args = MagicMock()
        args.action = "list"
        args.input = "/nonexistent/input.json"
        args.target_dir = None
        args.dry_run = True
        args.verbose = False

        # This should fail
        result = apply_plugin.execute_apply(args)
        assert result != 0

    def test_similarity_nonexistent_query_file(self):
        """Test similarity command with nonexistent query file."""
        similarity_plugin = SimilarityPlugin()

        # Mock args with nonexistent query file
        args = MagicMock()
        args.query_file = "/nonexistent/query.txt"
        args.database = None
        args.k = 5
        args.threshold = 0.8
        args.backend = "brute_force"
        args.output = "text"
        args.verbose = False

        # This should fail
        result = similarity_plugin.execute_similarity(args)
        assert result != 0

    def test_apply_nonexistent_target_directory(self):
        """Test apply command with nonexistent target directory."""
        apply_plugin = ApplyPlugin()

        # Mock args with nonexistent target directory
        args = MagicMock()
        args.action = "move"
        args.input = "/nonexistent/input.json"
        args.target_dir = "/nonexistent/target"
        args.dry_run = True
        args.verbose = False

        # This should fail validation
        result = apply_plugin.execute_apply(args)
        assert result != 0

class TestCLIPermissionErrors:
    """Test CLI permission error handling."""

    def test_scan_permission_denied(self):
        """Test scan command with permission denied."""
        scan_plugin = ScanPlugin()

        # Mock args with root directory (likely permission denied)
        args = MagicMock()
        args.paths = ["/root"]
        args.min_size = 0
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = False
        args.container = None

        # This might succeed on some systems, but shouldn't crash
        result = scan_plugin.execute_scan(args)
        assert isinstance(result, int)

    def test_apply_permission_denied(self):
        """Test apply command with permission denied."""
        apply_plugin = ApplyPlugin()

        # Mock args with root target directory
        args = MagicMock()
        args.action = "move"
        args.input = "/nonexistent/input.json"
        args.target_dir = "/root"
        args.dry_run = True
        args.verbose = False

        # This should handle permission issues gracefully
        result = apply_plugin.execute_apply(args)
        assert isinstance(result, int)

class TestCLICommandValidation:
    """Test command-specific validation logic."""

    def test_scan_invalid_size_constraints(self):
        """Test scan command with invalid size constraints."""
        scan_plugin = ScanPlugin()

        # Mock args with invalid size constraints
        args = MagicMock()
        args.paths = ["."]
        args.min_size = 1000  # min > max
        args.max_size = 100
        args.extensions = None
        args.exclude = None
        args.verbose = False
        args.container = None

        # This should fail validation
        result = scan_plugin.execute_scan(args)
        assert result != 0

    def test_similarity_invalid_threshold(self):
        """Test similarity command with invalid threshold."""
        similarity_plugin = SimilarityPlugin()

        # Mock args with invalid threshold
        args = MagicMock()
        args.query_file = "/nonexistent/query.txt"
        args.database = None
        args.k = 5
        args.threshold = 1.5  # > 1.0
        args.backend = "brute_force"
        args.output = "text"
        args.verbose = False

        # This should fail validation
        result = similarity_plugin.execute_similarity(args)
        assert result != 0

    def test_similarity_invalid_k(self):
        """Test similarity command with invalid k value."""
        similarity_plugin = SimilarityPlugin()

        # Mock args with invalid k
        args = MagicMock()
        args.query_file = "/nonexistent/query.txt"
        args.database = None
        args.k = 0  # Must be positive
        args.threshold = 0.8
        args.backend = "brute_force"
        args.output = "text"
        args.verbose = False

        # This should fail validation
        result = similarity_plugin.execute_similarity(args)
        assert result != 0

class TestCLIEdgeCases:
    """Test CLI edge cases and boundary conditions."""

    def test_scan_empty_directory(self):
        """Test scan command with empty directory."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty directory
            empty_dir = os.path.join(temp_dir, "empty")
            os.makedirs(empty_dir)

            scan_plugin = ScanPlugin()

            # Mock args with empty directory
            args = MagicMock()
            args.paths = [empty_dir]
            args.min_size = 0
            args.max_size = None
            args.extensions = None
            args.exclude = None
            args.verbose = False
            args.container = None

            # This should succeed but find no files
            result = scan_plugin.execute_scan(args)
            assert result == 0

    def test_apply_empty_input_file(self):
        """Test apply command with empty input file."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty input file
            empty_file = os.path.join(temp_dir, "empty.json")
            with open(empty_file, "w") as f:
                f.write("[]")  # Empty array

            apply_plugin = ApplyPlugin()

            # Mock args with empty input file
            args = MagicMock()
            args.action = "list"
            args.input = empty_file
            args.target_dir = None
            args.dry_run = True
            args.verbose = False

            # This should handle empty input gracefully
            result = apply_plugin.execute_apply(args)
            assert result == 0

    def test_similarity_empty_database(self):
        """Test similarity command with empty database."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create query file
            query_file = os.path.join(temp_dir, "query.txt")
            with open(query_file, "w") as f:
                f.write("query content")

            similarity_plugin = SimilarityPlugin()

            # Mock args with empty database
            args = MagicMock()
            args.query_file = query_file
            args.database = None  # No database
            args.k = 5
            args.threshold = 0.8
            args.backend = "brute_force"
            args.output = "text"
            args.verbose = False

            # This should handle empty database gracefully
            result = similarity_plugin.execute_similarity(args)
            assert result == 0

class TestCLIErrorRecovery:
    """Test CLI error recovery and graceful degradation."""

    def test_scan_with_missing_container(self):
        """Test scan command with missing container."""
        scan_plugin = ScanPlugin()

        # Mock args without container
        args = MagicMock()
        args.paths = ["."]
        args.min_size = 0
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = False
        args.container = None  # Missing container

        # This should handle missing container gracefully
        result = scan_plugin.execute_scan(args)
        assert isinstance(result, int)

    def test_apply_with_missing_container(self):
        """Test apply command with missing container."""
        apply_plugin = ApplyPlugin()

        # Mock args without container
        args = MagicMock()
        args.action = "list"
        args.input = "/nonexistent/input.json"
        args.target_dir = None
        args.dry_run = True
        args.verbose = False
        # No container needed for apply

        # This should handle missing input file gracefully
        result = apply_plugin.execute_apply(args)
        assert isinstance(result, int)

    def test_similarity_with_missing_container(self):
        """Test similarity command with missing container."""
        similarity_plugin = SimilarityPlugin()

        # Mock args without container
        args = MagicMock()
        args.query_file = "/nonexistent/query.txt"
        args.database = None
        args.k = 5
        args.threshold = 0.8
        args.backend = "brute_force"
        args.output = "text"
        args.verbose = False
        # No container needed for similarity

        # This should handle missing query file gracefully
        result = similarity_plugin.execute_similarity(args)
        assert isinstance(result, int)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
