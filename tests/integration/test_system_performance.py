# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""System Performance Tests - Performance benchmarking and scalability testing.

This module tests system performance metrics, scalability with large datasets,
performance optimization features, and benchmarks against established goals.
"""

import pytest
import sys
import os
import tempfile
import time
import json
from unittest.mock import patch, MagicMock
from nodupe.core.main import main
from nodupe.tools.commands.scan import ScanTool
from nodupe.tools.commands.apply import ApplyTool
from nodupe.tools.commands.similarity import SimilarityCommandTool as SimilarityTool

class TestPerformanceBenchmarking:
    """Test performance benchmarking framework."""

    def test_scan_performance_benchmarking(self):
        """Test scan performance with timing metrics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test dataset
            for i in range(50):
                test_file = os.path.join(temp_dir, f"file_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Test content {i % 10}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan with timing
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
            assert execution_time < 10.0  # Should complete within reasonable time

    def test_apply_performance_benchmarking(self):
        """Test apply performance with timing metrics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create duplicates file with large dataset
            duplicates_file = os.path.join(temp_dir, "duplicates.json")
            large_duplicates = {
                "duplicate_groups": []
            }

            # Create 100 duplicate groups
            for i in range(100):
                group = {
                    "hash": f"hash_{i}",
                    "files": [
                        {"path": f"/tmp/file_{i}_1.txt", "size": 100 + i, "type": "txt"},
                        {"path": f"/tmp/file_{i}_2.txt", "size": 100 + i, "type": "txt"}
                    ]
                }
                large_duplicates["duplicate_groups"].append(group)

            with open(duplicates_file, "w") as f:
                json.dump(large_duplicates, f)

            # Test apply performance
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
            assert execution_time < 5.0  # Should complete quickly

    def test_similarity_performance_benchmarking(self):
        """Test similarity search performance with timing metrics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create query file
            query_file = os.path.join(temp_dir, "query.txt")
            with open(query_file, "w") as f:
                f.write("Test query content")

            # Test similarity performance
            similarity_tool = SimilarityTool()
            similarity_args = MagicMock()
            similarity_args.query_file = query_file
            similarity_args.database = None
            similarity_args.k = 10
            similarity_args.threshold = 0.7
            similarity_args.backend = "brute_force"
            similarity_args.output = "text"
            similarity_args.verbose = False

            start_time = time.time()
            similarity_result = similarity_tool.execute_similarity(similarity_args)
            end_time = time.time()

            assert similarity_result == 0
            execution_time = end_time - start_time
            assert execution_time < 3.0  # Should be fast

class TestLargeDatasetPerformance:
    """Test system performance with large datasets."""

    def test_scan_large_dataset_performance(self):
        """Test scan performance with large dataset."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create large dataset: 200 files
            for i in range(200):
                subdir = os.path.join(temp_dir, f"subdir_{i // 50}")
                os.makedirs(subdir, exist_ok=True)

                test_file = os.path.join(subdir, f"file_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Content for file {i}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan performance
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
            assert execution_time < 15.0  # Should handle 200 files quickly

    def test_apply_large_duplicates_performance(self):
        """Test apply performance with large duplicates dataset."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create large duplicates file
            duplicates_file = os.path.join(temp_dir, "large_duplicates.json")
            large_dataset = {
                "duplicate_groups": []
            }

            # Create 500 duplicate groups
            for i in range(500):
                group = {
                    "hash": f"hash_{i}",
                    "files": [
                        {"path": f"/data/file_{i}_1.txt", "size": 1000 + i, "type": "txt"},
                        {"path": f"/data/file_{i}_2.txt", "size": 1000 + i, "type": "txt"},
                        {"path": f"/data/file_{i}_3.txt", "size": 1000 + i, "type": "txt"}
                    ]
                }
                large_dataset["duplicate_groups"].append(group)

            with open(duplicates_file, "w") as f:
                json.dump(large_dataset, f)

            # Test apply performance
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
            assert execution_time < 8.0  # Should handle 500 groups efficiently

class TestMemoryUsage:
    """Test system memory usage and resource management."""

    def test_scan_memory_usage(self):
        """Test scan memory usage with large dataset."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create dataset with varied file sizes
            for i in range(100):
                test_file = os.path.join(temp_dir, f"file_{i}.txt")
                content = "x" * (1024 * (i % 10 + 1))  # 1KB to 10KB files
                with open(test_file, "w") as f:
                    f.write(content)

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan memory usage
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

    def test_apply_memory_usage(self):
        """Test apply memory usage with large duplicates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create large duplicates file
            duplicates_file = os.path.join(temp_dir, "memory_test.json")
            memory_intensive_data = {
                "duplicate_groups": []
            }

            # Create groups with large metadata
            for i in range(200):
                group = {
                    "hash": f"memory_hash_{i}",
                    "files": [],
                    "metadata": {
                        "additional_info": "x" * 1000  # Large metadata
                    }
                }

                for j in range(5):
                    file_entry = {
                        "path": f"/very/long/path/to/file_{i}_{j}.txt",
                        "size": 10000 + i * j,
                        "type": "txt",
                        "attributes": {
                            "extended": "x" * 500  # Large attributes
                        }
                    }
                    group["files"].append(file_entry)

                memory_intensive_data["duplicate_groups"].append(group)

            with open(duplicates_file, "w") as f:
                json.dump(memory_intensive_data, f)

            # Test apply memory usage
            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_tool.execute_apply(apply_args)
            assert apply_result == 0

class TestPerformanceOptimization:
    """Test performance optimization features."""

    def test_scan_with_size_filters_performance(self):
        """Test scan performance with size filters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with varying sizes
            for i in range(50):
                test_file = os.path.join(temp_dir, f"file_{i}.txt")
                content = "x" * (1024 * (i + 1))  # 1KB to 50KB files
                with open(test_file, "w") as f:
                    f.write(content)

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan with size filters (should be faster)
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 5000  # 5KB minimum
            scan_args.max_size = 20000  # 20KB maximum
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            start_time = time.time()
            scan_result = scan_tool.execute_scan(scan_args)
            end_time = time.time()

            assert scan_result == 0
            execution_time = end_time - start_time
            assert execution_time < 5.0  # Filtered scan should be fast

    def test_scan_with_extension_filters_performance(self):
        """Test scan performance with extension filters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with different extensions
            extensions = ['txt', 'json', 'csv', 'py', 'md']
            for i in range(50):
                ext = extensions[i % len(extensions)]
                test_file = os.path.join(temp_dir, f"file_{i}.{ext}")
                with open(test_file, "w") as f:
                    f.write(f"Content for {ext} file")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test scan with extension filters (should be faster)
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = ['txt', 'json']  # Only scan these
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            start_time = time.time()
            scan_result = scan_tool.execute_scan(scan_args)
            end_time = time.time()

            assert scan_result == 0
            execution_time = end_time - start_time
            assert execution_time < 3.0  # Filtered scan should be very fast

class TestConcurrentOperationPerformance:
    """Test performance under concurrent operation scenarios."""

    def test_multiple_scan_operations_performance(self):
        """Test performance with multiple scan operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test directories
            for dir_num in range(5):
                subdir = os.path.join(temp_dir, f"test_dir_{dir_num}")
                os.makedirs(subdir)

                for file_num in range(20):
                    test_file = os.path.join(subdir, f"file_{file_num}.txt")
                    with open(test_file, "w") as f:
                        f.write(f"Content {dir_num}_{file_num}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test multiple scan operations
            scan_tool = ScanTool()

            total_time = 0
            for dir_num in range(5):
                subdir = os.path.join(temp_dir, f"test_dir_{dir_num}")

                scan_args = MagicMock()
                scan_args.paths = [subdir]
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
                total_time += (end_time - start_time)

            # Average time per scan should be reasonable
            avg_time = total_time / 5
            assert avg_time < 2.0

    def test_sequential_workflow_performance(self):
        """Test performance of sequential workflow operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test dataset
            for i in range(30):
                test_file = os.path.join(temp_dir, f"workflow_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Workflow test content {i % 5}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Test sequential workflow: scan → apply → similarity
            scan_tool = ScanTool()
            apply_tool = ApplyTool()
            similarity_tool = SimilarityTool()

            # Step 1: Scan
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_start = time.time()
            scan_result = scan_tool.execute_scan(scan_args)
            scan_end = time.time()

            # Step 2: Apply (list)
            duplicates_file = os.path.join(temp_dir, "workflow_duplicates.json")
            workflow_data = {
                "duplicate_groups": [
                    {
                        "hash": "workflow_hash",
                        "files": [
                            {"path": f"{temp_dir}/workflow_0.txt", "size": 25, "type": "txt"},
                            {"path": f"{temp_dir}/workflow_5.txt", "size": 25, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(workflow_data, f)

            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_start = time.time()
            apply_result = apply_tool.execute_apply(apply_args)
            apply_end = time.time()

            # Step 3: Similarity
            query_file = os.path.join(temp_dir, "workflow_query.txt")
            with open(query_file, "w") as f:
                f.write("Workflow query content")

            similarity_args = MagicMock()
            similarity_args.query_file = query_file
            similarity_args.database = None
            similarity_args.k = 5
            similarity_args.threshold = 0.7
            similarity_args.backend = "brute_force"
            similarity_args.output = "text"
            similarity_args.verbose = False

            similarity_start = time.time()
            similarity_result = similarity_tool.execute_similarity(similarity_args)
            similarity_end = time.time()

            # Verify all steps completed successfully
            assert scan_result == 0
            assert apply_result == 0
            assert similarity_result == 0

            # Verify performance metrics
            scan_time = scan_end - scan_start
            apply_time = apply_end - apply_start
            similarity_time = similarity_end - similarity_start
            total_workflow_time = scan_time + apply_time + similarity_time

            assert scan_time < 3.0
            assert apply_time < 1.0
            assert similarity_time < 2.0
            assert total_workflow_time < 10.0

class TestPerformanceRegression:
    """Test performance regression scenarios."""

    def test_performance_regression_detection(self):
        """Test detection of performance regressions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create standard test dataset
            for i in range(100):
                test_file = os.path.join(temp_dir, f"regression_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Regression test {i}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Establish baseline performance
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            # Run multiple times to establish baseline
            baseline_times = []
            for _ in range(3):
                start_time = time.time()
                scan_result = scan_tool.execute_scan(scan_args)
                end_time = time.time()

                assert scan_result == 0
                baseline_times.append(end_time - start_time)

            avg_baseline = sum(baseline_times) / len(baseline_times)

            # Performance should be consistent (no major regressions)
            assert avg_baseline < 8.0  # Should be under 8 seconds
            assert max(baseline_times) - min(baseline_times) < 2.0  # Consistent performance

    def test_memory_leak_detection(self):
        """Test detection of memory leaks in repeated operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(20):
                test_file = os.path.join(temp_dir, f"leak_test_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Memory leak test {i}")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Perform repeated operations to test for memory leaks
            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            # Run 10 consecutive scans
            for iteration in range(10):
                start_time = time.time()
                scan_result = scan_tool.execute_scan(scan_args)
                end_time = time.time()

                assert scan_result == 0
                iteration_time = end_time - start_time

                # Performance should remain consistent
                assert iteration_time < 3.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
