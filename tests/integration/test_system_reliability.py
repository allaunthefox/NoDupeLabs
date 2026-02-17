# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""System Reliability Tests - Stability and continuous operation testing.

This module tests system stability under continuous operation, error recovery
mechanisms, resource management, and graceful degradation under stress.
"""

import json
import os
import sys
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.main import main
from nodupe.tools.commands.apply import ApplyTool
from nodupe.tools.commands.scan import ScanTool
from nodupe.tools.commands.similarity import SimilarityCommandTool as SimilarityTool


class TestContinuousOperation:
    """Test system stability under continuous operation."""

    def test_repeated_scan_operations(self):
        """Test stability with repeated scan operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test dataset
            for i in range(20):
                test_file = os.path.join(temp_dir, f"file_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Continuous operation test {i}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Perform 20 consecutive scan operations
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            success_count = 0
            for iteration in range(20):
                scan_result = scan_tool.execute_scan(scan_args)
                if scan_result == 0:
                    success_count += 1

                # Small delay between operations
                # time.sleep(0.1)  # Removed for performance - use mock time in tests

            # Should have high success rate
            assert success_count >= 18  # At least 90% success rate

    def test_repeated_apply_operations(self):
        """Test stability with repeated apply operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create duplicates file
            duplicates_file = os.path.join(temp_dir, "duplicates.json")
            duplicates_data = {
                "duplicate_groups": [
                    {
                        "hash": "continuous_hash",
                        "files": [
                            {"path": f"/tmp/file_{i}.txt", "size": 100 + i, "type": "txt"}
                            for i in range(5)
                        ]
                    }
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(duplicates_data, f)

            # Perform 15 consecutive apply operations
            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            success_count = 0
            for iteration in range(15):
                apply_result = apply_tool.execute_apply(apply_args)
                if apply_result == 0:
                    success_count += 1

                # time.sleep(0.1)  # Removed for performance - use mock time in tests

            # Should have high success rate
            assert success_count >= 14  # At least 93% success rate

    def test_repeated_similarity_operations(self):
        """Test stability with repeated similarity operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create query file
            query_file = os.path.join(temp_dir, "query.txt")
            with open(query_file, "w") as f:
                f.write("Continuous similarity test query")

            # Perform 10 consecutive similarity operations
            similarity_tool = SimilarityTool()
            similarity_args = MagicMock()
            similarity_args.query_file = query_file
            similarity_args.database = None
            similarity_args.k = 5
            similarity_args.threshold = 0.7
            similarity_args.backend = "brute_force"
            similarity_args.output = "text"
            similarity_args.verbose = False

            success_count = 0
            for iteration in range(10):
                similarity_result = similarity_tool.execute_similarity(similarity_args)
                if similarity_result == 0:
                    success_count += 1

                # time.sleep(0.1)  # Removed for performance - use mock time in tests

            # Should have high success rate
            assert success_count >= 9  # At least 90% success rate

class TestResourceStress:
    """Test system behavior under resource stress conditions."""

    def test_scan_with_large_file_count(self):
        """Test scan reliability with large number of files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create large number of files (300)
            for i in range(300):
                subdir = os.path.join(temp_dir, f"dir_{i // 100}")
                os.makedirs(subdir, exist_ok=True)

                test_file = os.path.join(subdir, f"file_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Stress test content {i}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan under stress
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
            assert scan_result == 0  # Should handle stress gracefully

    def test_apply_with_large_duplicate_groups(self):
        """Test apply reliability with large duplicate groups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create large duplicates file
            duplicates_file = os.path.join(temp_dir, "large_duplicates.json")
            large_data = {
                "duplicate_groups": []
            }

            # Create 1000 duplicate groups
            for i in range(1000):
                group = {
                    "hash": f"stress_hash_{i}",
                    "files": [
                        {"path": f"/data/file_{i}_{j}.txt", "size": 500 + i * j, "type": "txt"}
                        for j in range(3)
                    ],
                    "metadata": {
                        "additional_info": "x" * 200  # Some metadata
                    }
                }
                large_data["duplicate_groups"].append(group)

            with open(duplicates_file, "w") as f:
                json.dump(large_data, f)

            # Test apply under stress
            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_tool.execute_apply(apply_args)
            assert apply_result == 0  # Should handle large dataset gracefully

class TestErrorRecoveryMechanisms:
    """Test system error recovery mechanisms."""

    def test_scan_recovery_from_file_errors(self):
        """Test scan recovery from individual file errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mix of valid and potentially problematic files
            for i in range(20):
                test_file = os.path.join(temp_dir, f"file_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Valid content {i}")

            # Add some files with special characters in names
            special_files = [
                "file_with_spaces .txt",
                "file-with-dashes.txt",
                "file.with.dots.txt",
                "file_with_underscores.txt"
            ]

            for filename in special_files:
                test_file = os.path.join(temp_dir, filename)
                with open(test_file, "w") as f:
                    f.write("Special filename content")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan with mixed file types
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
            assert scan_result == 0  # Should handle file variations gracefully

    def test_apply_recovery_from_invalid_data(self):
        """Test apply recovery from invalid data formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create duplicates file with some invalid entries
            duplicates_file = os.path.join(temp_dir, "mixed_duplicates.json")
            mixed_data = {
                "duplicate_groups": [
                    {
                        "hash": "valid_hash_1",
                        "files": [
                            {"path": "/tmp/valid1.txt", "size": 100, "type": "txt"},
                            {"path": "/tmp/valid2.txt", "size": 100, "type": "txt"}
                        ]
                    },
                    {
                        "hash": "invalid_hash",
                        "files": []  # Empty files list
                    },
                    {
                        "hash": "valid_hash_2",
                        "files": [
                            {"path": "/tmp/valid3.txt", "size": 150, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(mixed_data, f)

            # Test apply with mixed valid/invalid data
            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_tool.execute_apply(apply_args)
            assert apply_result == 0  # Should handle invalid data gracefully

class TestGracefulDegradation:
    """Test graceful degradation under stress conditions."""

    def test_scan_graceful_degradation_with_missing_container(self):
        """Test scan graceful degradation when container is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(10):
                test_file = os.path.join(temp_dir, f"degradation_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Degradation test {i}")

            # Test scan without container (should degrade gracefully)
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = None  # Missing container

            scan_result = scan_tool.execute_scan(scan_args)
            # Should handle missing container gracefully
            assert isinstance(scan_result, int)

    def test_apply_graceful_degradation_with_missing_files(self):
        """Test apply graceful degradation when files are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create duplicates file with non-existent files
            duplicates_file = os.path.join(temp_dir, "missing_files.json")
            missing_data = {
                "duplicate_groups": [
                    {
                        "hash": "missing_hash",
                        "files": [
                            {"path": "/nonexistent/path/file1.txt", "size": 100, "type": "txt"},
                            {"path": "/nonexistent/path/file2.txt", "size": 100, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(missing_data, f)

            # Test apply with missing files
            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_tool.execute_apply(apply_args)
            # Should handle missing files gracefully
            assert isinstance(apply_result, int)

class TestLongRunningOperations:
    """Test reliability of long-running operations."""

    def test_long_running_scan_operation(self):
        """Test reliability of long-running scan operation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create large dataset for long operation
            for i in range(500):
                subdir = os.path.join(temp_dir, f"long_{i // 100}")
                os.makedirs(subdir, exist_ok=True)

                test_file = os.path.join(subdir, f"file_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Long running test content {i}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test long-running scan
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            start_time = time.time()
            scan_result = scan_tool.execute_scan(scan_args)
            end_time = time.time()

            assert scan_result == 0
            execution_time = end_time - start_time
            assert execution_time < 30.0  # Should complete within reasonable time

    def test_long_running_apply_operation(self):
        """Test reliability of long-running apply operation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create large duplicates file
            duplicates_file = os.path.join(temp_dir, "long_duplicates.json")
            long_data = {
                "duplicate_groups": []
            }

            # Create 2000 duplicate groups for long operation
            for i in range(2000):
                group = {
                    "hash": f"long_hash_{i}",
                    "files": [
                        {"path": f"/data/long_file_{i}_{j}.txt", "size": 200 + i * j, "type": "txt"}
                        for j in range(2)
                    ]
                }
                long_data["duplicate_groups"].append(group)

            with open(duplicates_file, "w") as f:
                json.dump(long_data, f)

            # Test long-running apply
            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            start_time = time.time()
            apply_result = apply_tool.execute_apply(apply_args)
            end_time = time.time()

            assert apply_result == 0
            execution_time = end_time - start_time
            assert execution_time < 15.0  # Should handle large dataset efficiently

class TestResourceManagement:
    """Test system resource management and cleanup."""

    def test_resource_cleanup_after_scan(self):
        """Test proper resource cleanup after scan operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(20):
                test_file = os.path.join(temp_dir, f"cleanup_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Resource cleanup test {i}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Perform multiple scan operations to test cleanup
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            for iteration in range(5):
                scan_result = scan_tool.execute_scan(scan_args)
                assert scan_result == 0

                # Small delay
                # time.sleep(0.1)  # Removed for performance - use mock time in tests

            # System should still be responsive after multiple operations
            final_scan_result = scan_tool.execute_scan(scan_args)
            assert final_scan_result == 0

    def test_resource_cleanup_after_apply(self):
        """Test proper resource cleanup after apply operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create duplicates file
            duplicates_file = os.path.join(temp_dir, "cleanup_duplicates.json")
            cleanup_data = {
                "duplicate_groups": [
                    {
                        "hash": f"cleanup_hash_{i}",
                        "files": [
                            {"path": f"/tmp/cleanup_{i}_1.txt", "size": 150 + i, "type": "txt"},
                            {"path": f"/tmp/cleanup_{i}_2.txt", "size": 150 + i, "type": "txt"}
                        ]
                    }
                    for i in range(50)
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(cleanup_data, f)

            # Perform multiple apply operations to test cleanup
            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            for iteration in range(5):
                apply_result = apply_tool.execute_apply(apply_args)
                assert apply_result == 0

                # time.sleep(0.1)  # Removed for performance - use mock time in tests

            # System should still be responsive
            final_apply_result = apply_tool.execute_apply(apply_args)
            assert final_apply_result == 0

class TestSystemStability:
    """Test overall system stability and reliability."""

    def test_comprehensive_system_stability(self):
        """Test comprehensive system stability with mixed operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test dataset
            for i in range(50):
                test_file = os.path.join(temp_dir, f"stability_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"System stability test {i}")

            # Create duplicates file
            duplicates_file = os.path.join(temp_dir, "stability_duplicates.json")
            stability_data = {
                "duplicate_groups": [
                    {
                        "hash": f"stability_hash_{i}",
                        "files": [
                            {"path": f"{temp_dir}/stability_{i}.txt", "size": 200 + i, "type": "txt"},
                            {"path": f"{temp_dir}/stability_{i+1}.txt", "size": 200 + i, "type": "txt"}
                        ]
                    }
                    for i in range(0, 40, 2)
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(stability_data, f)

            # Create query file
            query_file = os.path.join(temp_dir, "stability_query.txt")
            with open(query_file, "w") as f:
                f.write("System stability query")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Perform mixed operations
            scan_tool = ScanTool()
            apply_tool = ApplyTool()
            similarity_tool = SimilarityTool()

            operations = [
                ("scan", scan_tool, None),
                ("apply", apply_tool, duplicates_file),
                ("similarity", similarity_tool, query_file),
                ("scan", scan_tool, None),
                ("apply", apply_tool, duplicates_file)
            ]

            success_count = 0
            for op_name, tool, extra_data in operations:
                if op_name == "scan":
                    scan_args = MagicMock()
                    scan_args.paths = [temp_dir]
                    scan_args.min_size = 0
                    scan_args.max_size = None
                    scan_args.extensions = None
                    scan_args.exclude = None
                    scan_args.verbose = False
                    scan_args.container = mock_container

                    result = tool.execute_scan(scan_args)

                elif op_name == "apply":
                    apply_args = MagicMock()
                    apply_args.action = "list"
                    apply_args.input = extra_data
                    apply_args.target_dir = None
                    apply_args.dry_run = True
                    apply_args.verbose = False

                    result = tool.execute_apply(apply_args)

                elif op_name == "similarity":
                    similarity_args = MagicMock()
                    similarity_args.query_file = extra_data
                    similarity_args.database = None
                    similarity_args.k = 5
                    similarity_args.threshold = 0.7
                    similarity_args.backend = "brute_force"
                    similarity_args.output = "text"
                    similarity_args.verbose = False

                    result = tool.execute_similarity(similarity_args)

                if result == 0:
                    success_count += 1

                # time.sleep(0.1)  # Removed for performance - use mock time in tests

            # Should have high success rate for mixed operations
            assert success_count >= 4  # At least 80% success rate

    def test_system_reliability_under_load(self):
        """Test system reliability under sustained load."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test dataset
            for i in range(100):
                test_file = os.path.join(temp_dir, f"load_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Load test content {i}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Perform sustained operations
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            # 10 consecutive operations under load
            success_count = 0
            for iteration in range(10):
                scan_result = scan_tool.execute_scan(scan_args)
                if scan_result == 0:
                    success_count += 1

                # No delay to simulate load
                # time.sleep(0.01)

            # System should maintain reliability under load
            assert success_count >= 8  # At least 80% success rate under load

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
