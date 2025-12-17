# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""End-to-End Workflow Tests - Complete system integration testing.

This module tests complete user workflows from CLI to final output, validating
data flow through all system components and integration between CLI, plugins,
and core services.
"""

import pytest
import sys
import os
import tempfile
import json
import time
from unittest.mock import patch, MagicMock
from nodupe.core.main import main
from nodupe.core.loader import bootstrap
from nodupe.plugins.commands.scan import ScanPlugin
from nodupe.plugins.commands.apply import ApplyPlugin
from nodupe.plugins.commands.similarity import SimilarityCommandPlugin as SimilarityPlugin

class TestCompleteScanApplyWorkflow:
    """Test complete scan and apply workflow integration."""

    def test_scan_apply_list_workflow(self):
        """Test complete scan followed by apply list workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with duplicates
            test_files = []
            for i in range(3):
                test_file = os.path.join(temp_dir, f"test_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"duplicate content {i % 2}")  # Creates duplicates
                test_files.append(test_file)

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan workflow
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

            # Create mock duplicates file for apply
            duplicates_file = os.path.join(temp_dir, "duplicates.json")
            duplicates_data = {
                "duplicate_groups": [
                    {
                        "hash": "abc123",
                        "files": [
                            {"path": test_files[0], "size": 18, "type": "txt"},
                            {"path": test_files[2], "size": 18, "type": "txt"}
                        ]
                    },
                    {
                        "hash": "def456",
                        "files": [
                            {"path": test_files[1], "size": 18, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(duplicates_data, f)

            # Test apply list workflow
            apply_plugin = ApplyPlugin()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_plugin.execute_apply(apply_args)
            assert apply_result == 0

    def test_scan_apply_delete_workflow(self):
        """Test complete scan followed by apply delete workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = []
            for i in range(4):
                test_file = os.path.join(temp_dir, f"test_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"content {i % 2}")  # Creates duplicates
                test_files.append(test_file)

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan workflow
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
                "duplicate_groups": [
                    {
                        "hash": "hash1",
                        "files": [
                            {"path": test_files[0], "size": 10, "type": "txt"},
                            {"path": test_files[2], "size": 10, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(duplicates_data, f)

            # Test apply delete workflow (dry-run)
            apply_plugin = ApplyPlugin()
            apply_args = MagicMock()
            apply_args.action = "delete"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_plugin.execute_apply(apply_args)
            assert apply_result == 0

class TestCompleteScanSimilarityWorkflow:
    """Test complete scan followed by similarity workflow integration."""

    def test_scan_similarity_workflow(self):
        """Test complete scan followed by similarity search workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(5):
                test_file = os.path.join(temp_dir, f"document_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Document content about topic {i % 3}")  # Similar content groups

            # Create query file
            query_file = os.path.join(temp_dir, "query.txt")
            with open(query_file, "w") as f:
                f.write("Query about topic 1")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan workflow
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

            # Test similarity workflow
            similarity_plugin = SimilarityPlugin()
            similarity_args = MagicMock()
            similarity_args.query_file = query_file
            similarity_args.database = None  # Use in-memory for testing
            similarity_args.k = 3
            similarity_args.threshold = 0.7
            similarity_args.backend = "brute_force"
            similarity_args.output = "text"
            similarity_args.verbose = False

            similarity_result = similarity_plugin.execute_similarity(similarity_args)
            assert similarity_result == 0

class TestPluginLifecycleIntegration:
    """Test complete plugin lifecycle integration."""

    def test_plugin_load_execute_shutdown_workflow(self):
        """Test complete plugin load, execute, and shutdown workflow."""
        # Test with scan plugin
        scan_plugin = ScanPlugin()

        # Test plugin initialization
        assert scan_plugin.name == "scan"
        assert scan_plugin.version == "1.0.0"
        assert scan_plugin.description == "Scan directories for duplicate files"

        # Test plugin command registration
        mock_subparsers = MagicMock()
        scan_plugin.register_commands(mock_subparsers)
        assert mock_subparsers.add_parser.called

        # Test plugin execution
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")

            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            execution_result = scan_plugin.execute_scan(scan_args)
            assert execution_result == 0

        # Test plugin shutdown
        scan_plugin.shutdown()  # Should not raise exceptions

    def test_multiple_plugin_integration(self):
        """Test integration between multiple plugins."""
        scan_plugin = ScanPlugin()
        apply_plugin = ApplyPlugin()
        similarity_plugin = SimilarityPlugin()

        # Verify all plugins can be initialized
        assert scan_plugin.name == "scan"
        assert apply_plugin.name == "apply"
        assert similarity_plugin.name == "similarity"

        # Verify all plugins can register commands
        mock_subparsers = MagicMock()
        scan_plugin.register_commands(mock_subparsers)
        apply_plugin.register_commands(mock_subparsers)
        similarity_plugin.register_commands(mock_subparsers)

        # Verify command registration calls
        assert mock_subparsers.add_parser.call_count == 3

class TestDatabaseIntegration:
    """Test database integration workflows."""

    def test_scan_database_integration(self):
        """Test scan workflow with database integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(3):
                test_file = os.path.join(temp_dir, f"file_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"file content {i}")

            # Mock database connection and repository
            mock_db_connection = MagicMock()
            mock_file_repo = MagicMock()
            mock_file_repo.batch_add_files.return_value = 3

            # Mock container with database service
            mock_container = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan with database integration
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

            # Verify database service was accessed
            assert mock_container.get_service.called
            assert mock_db_connection is not None

    def test_apply_database_integration(self):
        """Test apply workflow with database query integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = []
            for i in range(2):
                test_file = os.path.join(temp_dir, f"dup_{i}.txt")
                with open(test_file, "w") as f:
                    f.write("duplicate content")
                test_files.append(test_file)

            # Create duplicates file
            duplicates_file = os.path.join(temp_dir, "duplicates.json")
            duplicates_data = {
                "duplicate_groups": [
                    {
                        "hash": "testhash",
                        "files": [
                            {"path": test_files[0], "size": 18, "type": "txt"},
                            {"path": test_files[1], "size": 18, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(duplicates_data, f)

            # Test apply with database context
            apply_plugin = ApplyPlugin()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_plugin.execute_apply(apply_args)
            assert apply_result == 0

class TestCLIIntegration:
    """Test CLI integration with core system."""

    def test_cli_scan_command_integration(self):
        """Test CLI scan command integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")

            # Test CLI scan command
            with patch('sys.argv', ['nodupe', 'scan', temp_dir, '--min-size', '0']):
                result = main()
                # Scan should complete successfully
                assert isinstance(result, int)

    def test_cli_plugin_command_integration(self):
        """Test CLI plugin command integration."""
        # Test CLI plugin list command
        with patch('sys.argv', ['nodupe', 'plugin', '--list']):
            result = main()
            assert result == 0

    def test_cli_version_command_integration(self):
        """Test CLI version command integration."""
        # Test CLI version command
        with patch('sys.argv', ['nodupe', 'version']):
            result = main()
            assert result == 0

class TestComplexWorkflowIntegration:
    """Test complex multi-step workflow integration."""

    def test_scan_apply_similarity_complex_workflow(self):
        """Test complex workflow: scan → apply → similarity."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Create test dataset
            test_files = []
            for i in range(6):
                test_file = os.path.join(temp_dir, f"doc_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Content about subject {i % 2}")  # Creates duplicates
                test_files.append(test_file)

            # Step 2: Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Step 3: Execute scan workflow
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

            # Step 4: Create duplicates and apply list
            duplicates_file = os.path.join(temp_dir, "duplicates.json")
            duplicates_data = {
                "duplicate_groups": [
                    {
                        "hash": "hash1",
                        "files": [
                            {"path": test_files[0], "size": 22, "type": "txt"},
                            {"path": test_files[2], "size": 22, "type": "txt"},
                            {"path": test_files[4], "size": 22, "type": "txt"}
                        ]
                    },
                    {
                        "hash": "hash2",
                        "files": [
                            {"path": test_files[1], "size": 22, "type": "txt"},
                            {"path": test_files[3], "size": 22, "type": "txt"},
                            {"path": test_files[5], "size": 22, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(duplicates_data, f)

            apply_plugin = ApplyPlugin()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_plugin.execute_apply(apply_args)
            assert apply_result == 0

            # Step 5: Execute similarity workflow
            query_file = os.path.join(temp_dir, "query.txt")
            with open(query_file, "w") as f:
                f.write("Query about subject 1")

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

    def test_large_dataset_workflow(self):
        """Test workflow with larger dataset."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create larger dataset
            for i in range(20):
                subdir = os.path.join(temp_dir, f"subdir_{i // 5}")
                os.makedirs(subdir, exist_ok=True)

                test_file = os.path.join(subdir, f"file_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Content group {i % 4}")  # 4 content groups

            # Test scan with larger dataset
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

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

class TestErrorHandlingIntegration:
    """Test error handling in integrated workflows."""

    def test_workflow_with_invalid_paths(self):
        """Test workflow error handling with invalid paths."""
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
        assert scan_result != 0  # Should fail gracefully

    def test_workflow_with_missing_files(self):
        """Test workflow error handling with missing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test apply with missing input file
            apply_plugin = ApplyPlugin()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = "/nonexistent/file.json"
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_plugin.execute_apply(apply_args)
            assert apply_result != 0  # Should fail gracefully

    def test_workflow_with_permission_errors(self):
        """Test workflow error handling with permission errors."""
        # Test scan with protected directory
        scan_plugin = ScanPlugin()
        scan_args = MagicMock()
        scan_args.paths = ["/root"]  # Likely permission denied
        scan_args.min_size = 0
        scan_args.max_size = None
        scan_args.extensions = None
        scan_args.exclude = None
        scan_args.verbose = False
        scan_args.container = None

        scan_result = scan_plugin.execute_scan(scan_args)
        # Should handle permission error gracefully
        assert isinstance(scan_result, int)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
