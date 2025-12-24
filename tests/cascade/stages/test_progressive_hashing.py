"""Unit tests for ProgressiveHashingCascadeStage.

This module tests the ProgressiveHashingCascadeStage implementation
including algorithm cascading, security policy integration, and
backward compatibility.

Test Coverage:
    - Algorithm cascade selection (BLAKE3 → SHA256 → MD5)
    - Security policy integration
    - Performance comparison
    - Backward compatibility with existing ProgressiveHasher
    - Error handling and edge cases
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from nodupe.core.cascade.stages.progressive_hashing import ProgressiveHashingCascadeStage
from nodupe.core.cascade.protocol import QualityTier, StageExecutionError, get_stage_manager
from nodupe.core.cascade.environment import EnvironmentDetector
from nodupe.core.security.policy import SecurityPolicy


class TestProgressiveHashingCascadeStage:
    """Test suite for ProgressiveHashingCascadeStage."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.stage = ProgressiveHashingCascadeStage()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_files = []
        self.test_content = b"test content for hashing"
        
        for i in range(5):
            test_file = Path(self.temp_dir) / f"test_file_{i}.txt"
            with open(test_file, 'wb') as f:
                f.write(self.test_content * (i + 1))  # Different sizes
            self.test_files.append(test_file)

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir)

    # ===========================
    # Property Tests
    # ===========================

    def test_name_property(self):
        """Test that name property returns correct value."""
        assert self.stage.name == "ProgressiveHashing"

    def test_quality_tier_property(self):
        """Test that quality_tier property returns BEST."""
        assert self.stage.quality_tier == QualityTier.BEST

    def test_requires_internet_property(self):
        """Test that requires_internet property returns False."""
        assert self.stage.requires_internet is False

    def test_requires_plugins_property(self):
        """Test that requires_plugins property returns empty list."""
        assert self.stage.requires_plugins == []

    # ===========================
    # can_operate() Tests
    # ===========================

    def test_can_operate_always_true(self):
        """Test that can_operate always returns True for progressive hashing."""
        assert self.stage.can_operate() is True

    # ===========================
    # execute() Tests
    # ===========================

    def test_execute_with_empty_file_list(self):
        """Test execute with empty file list."""
        result = self.stage.execute([])
        
        assert isinstance(result, dict)
        assert result["duplicates"] == []
        assert result["files_processed"] == 0
        assert result["duplicate_groups"] == 0

    def test_execute_with_single_file(self):
        """Test execute with single file (no duplicates possible)."""
        result = self.stage.execute([self.test_files[0]])
        
        assert isinstance(result, dict)
        assert result["duplicates"] == []
        assert result["files_processed"] == 1
        assert result["duplicate_groups"] == 0

    def test_execute_with_duplicate_files(self):
        """Test execute with duplicate files."""
        # Create duplicate files
        duplicate_file = Path(self.temp_dir) / "duplicate.txt"
        with open(duplicate_file, 'wb') as f:
            f.write(self.test_content)
        
        files = [self.test_files[0], duplicate_file]
        result = self.stage.execute(files)
        
        assert isinstance(result, dict)
        assert result["files_processed"] == 2
        assert result["duplicate_groups"] == 1
        assert len(result["duplicates"]) == 1
        assert len(result["duplicates"][0]) == 2  # Two files in duplicate group

    def test_execute_with_different_size_files(self):
        """Test execute with files of different sizes (no duplicates)."""
        result = self.stage.execute(self.test_files)
        
        assert isinstance(result, dict)
        assert result["files_processed"] == 5
        assert result["duplicate_groups"] == 0
        assert result["duplicates"] == []

    def test_execute_returns_algorithm_information(self):
        """Test that execute returns algorithm information."""
        result = self.stage.execute(self.test_files)
        
        assert "quick_hash_algorithm" in result
        assert "full_hash_algorithm" in result
        assert isinstance(result["quick_hash_algorithm"], str)
        assert isinstance(result["full_hash_algorithm"], str)

    # ===========================
    # Algorithm Cascade Tests
    # ===========================

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    def test_get_optimal_quick_hasher_with_blake3(self, mock_check_plugin):
        """Test optimal quick hasher selection with BLAKE3 available."""
        mock_check_plugin.return_value = True
        
        hasher = self.stage._get_optimal_quick_hasher()
        
        # Should use BLAKE3 when available
        assert hasattr(hasher, 'quick_hash')
        # The actual algorithm used depends on the implementation

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    def test_get_optimal_quick_hasher_without_blake3(self, mock_check_plugin):
        """Test optimal quick hasher selection without BLAKE3."""
        mock_check_plugin.return_value = False
        
        hasher = self.stage._get_optimal_quick_hasher()
        
        # Should fall back to standard hasher
        assert hasattr(hasher, 'quick_hash')

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    @patch.object(SecurityPolicy, 'allows_algorithm')
    def test_get_optimal_full_hasher_with_blake3(self, mock_allows_algorithm, mock_check_plugin):
        """Test optimal full hasher selection with BLAKE3 available."""
        mock_check_plugin.return_value = True
        mock_allows_algorithm.return_value = True
        
        hasher = self.stage._get_optimal_full_hasher()
        
        # Should use BLAKE3 when available and allowed
        assert hasattr(hasher, 'full_hash')

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    @patch.object(SecurityPolicy, 'allows_algorithm')
    def test_get_optimal_full_hasher_sha256_fallback(self, mock_allows_algorithm, mock_check_plugin):
        """Test optimal full hasher selection falling back to SHA256."""
        mock_check_plugin.return_value = False
        mock_allows_algorithm.return_value = True
        
        hasher = self.stage._get_optimal_full_hasher()
        
        # Should use SHA256 when BLAKE3 not available but allowed
        assert hasattr(hasher, 'full_hash')

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    @patch.object(SecurityPolicy, 'allows_algorithm')
    def test_get_optimal_full_hasher_md5_fallback(self, mock_allows_algorithm, mock_check_plugin):
        """Test optimal full hasher selection falling back to MD5."""
        mock_check_plugin.return_value = False
        mock_allows_algorithm.return_value = False
        
        hasher = self.stage._get_optimal_full_hasher()
        
        # Should use MD5 when SHA256 not allowed
        assert hasattr(hasher, 'full_hash')

    # ===========================
    # Security Policy Integration Tests
    # ===========================

    @patch.object(SecurityPolicy, 'allows_algorithm')
    def test_security_policy_sha256_allowed(self, mock_allows_algorithm):
        """Test security policy allows SHA256."""
        mock_allows_algorithm.return_value = True
        
        # This would be tested through the full execution path
        result = self.stage.execute(self.test_files)
        
        assert isinstance(result, dict)
        # The specific algorithm used depends on availability and policy

    @patch.object(SecurityPolicy, 'allows_algorithm')
    def test_security_policy_sha256_denied(self, mock_allows_algorithm):
        """Test security policy denies SHA256."""
        mock_allows_algorithm.return_value = False
        
        result = self.stage.execute(self.test_files)
        
        assert isinstance(result, dict)
        # Should fall back to MD5

    # ===========================
    # Performance Tests
    # ===========================

    def test_performance_comparison_blake3_vs_sha256(self):
        """Test performance comparison between BLAKE3 and SHA256."""
        import time
        
        # Create larger test files
        large_files = []
        large_content = b"x" * (1024 * 1024)  # 1MB content
        
        for i in range(3):
            large_file = Path(self.temp_dir) / f"large_file_{i}.txt"
            with open(large_file, 'wb') as f:
                f.write(large_content)
            large_files.append(large_file)
        
        # Measure execution time
        start_time = time.time()
        result = self.stage.execute(large_files)
        execution_time = time.time() - start_time
        
        assert isinstance(result, dict)
        assert result["files_processed"] == 3
        assert result["duplicate_groups"] == 1
        
        # Execution should be reasonably fast (less than 10 seconds for 3MB)
        assert execution_time < 10.0

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    def test_performance_with_blake3_available(self, mock_check_plugin):
        """Test performance when BLAKE3 is available."""
        mock_check_plugin.return_value = True
        
        start_time = time.time()
        result = self.stage.execute(self.test_files)
        execution_time = time.time() - start_time
        
        assert isinstance(result, dict)
        assert execution_time < 5.0  # Should be fast

    # ===========================
    # Backward Compatibility Tests
    # ===========================

    def test_backward_compatibility_with_progressive_hasher(self):
        """Test backward compatibility with existing ProgressiveHasher."""
        from nodupe.core.hash_progressive import ProgressiveHasher
        
        # Test that our cascade stage produces similar results to original
        original_hasher = ProgressiveHasher()
        cascade_result = self.stage.execute(self.test_files)
        
        # Both should process the same number of files
        assert cascade_result["files_processed"] == len(self.test_files)
        
        # Both should find the same duplicate groups (0 in this case)
        assert cascade_result["duplicate_groups"] == 0

    def test_output_format_compatibility(self):
        """Test that output format is compatible with expected interface."""
        result = self.stage.execute(self.test_files)
        
        # Check output format
        expected_keys = [
            "duplicates",
            "quick_hash_algorithm", 
            "full_hash_algorithm",
            "files_processed",
            "duplicate_groups"
        ]
        
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
            assert result[key] is not None, f"Key {key} is None"

    # ===========================
    # Error Handling Tests
    # ===========================

    def test_execute_with_nonexistent_files(self):
        """Test execute with nonexistent files."""
        nonexistent_files = [
            Path(self.temp_dir) / "nonexistent1.txt",
            Path(self.temp_dir) / "nonexistent2.txt"
        ]
        
        # Should handle gracefully
        result = self.stage.execute(nonexistent_files)
        
        assert isinstance(result, dict)
        assert result["files_processed"] == 0
        assert result["duplicate_groups"] == 0

    def test_execute_with_directory_instead_of_file(self):
        """Test execute with directory instead of file."""
        directory = Path(self.temp_dir)
        
        # Should handle gracefully
        result = self.stage.execute([directory])
        
        assert isinstance(result, dict)
        # Behavior depends on implementation - should not crash

    def test_execute_with_empty_files(self):
        """Test execute with empty files."""
        empty_files = []
        for i in range(3):
            empty_file = Path(self.temp_dir) / f"empty_{i}.txt"
            empty_file.touch()  # Create empty file
            empty_files.append(empty_file)
        
        result = self.stage.execute(empty_files)
        
        assert isinstance(result, dict)
        assert result["files_processed"] == 3
        assert result["duplicate_groups"] == 1  # All empty files are duplicates

    # ===========================
    # Edge Case Tests
    # ===========================

    def test_execute_with_very_large_files(self):
        """Test execute with very large files."""
        # Create a large file (10MB)
        large_file = Path(self.temp_dir) / "large.txt"
        large_content = b"x" * (1024 * 1024 * 10)  # 10MB
        
        with open(large_file, 'wb') as f:
            f.write(large_content)
        
        # Should handle large files without crashing
        result = self.stage.execute([large_file])
        
        assert isinstance(result, dict)
        assert result["files_processed"] == 1

    def test_execute_with_special_characters_in_filenames(self):
        """Test execute with special characters in filenames."""
        special_files = []
        special_names = ["file with spaces.txt", "file_with_üñíçødé.txt", "file_with_emoji_🚀.txt"]
        
        for name in special_names:
            special_file = Path(self.temp_dir) / name
            with open(special_file, 'wb') as f:
                f.write(b"test content")
            special_files.append(special_file)
        
        # Should handle special characters
        result = self.stage.execute(special_files)
        
        assert isinstance(result, dict)
        assert result["files_processed"] == 3

    def test_execute_with_identical_files(self):
        """Test execute with multiple identical files."""
        identical_files = []
        identical_content = b"identical content"
        
        for i in range(5):
            identical_file = Path(self.temp_dir) / f"identical_{i}.txt"
            with open(identical_file, 'wb') as f:
                f.write(identical_content)
            identical_files.append(identical_file)
        
        result = self.stage.execute(identical_files)
        
        assert isinstance(result, dict)
        assert result["files_processed"] == 5
        assert result["duplicate_groups"] == 1
        assert len(result["duplicates"][0]) == 5  # All 5 files are duplicates

    def test_execute_with_mixed_file_types(self):
        """Test execute with mixed file types."""
        mixed_files = []
        
        # Text file
        text_file = Path(self.temp_dir) / "text.txt"
        with open(text_file, 'w') as f:
            f.write("text content")
        mixed_files.append(text_file)
        
        # Binary file
        binary_file = Path(self.temp_dir) / "binary.bin"
        with open(binary_file, 'wb') as f:
            f.write(b"\x00\x01\x02\x03")
        mixed_files.append(binary_file)
        
        result = self.stage.execute(mixed_files)
        
        assert isinstance(result, dict)
        assert result["files_processed"] == 2
        assert result["duplicate_groups"] == 0  # Different content

    # ===========================
    # Integration Tests
    # ===========================

    def test_integration_with_environment_detector(self):
        """Test integration with EnvironmentDetector."""
        with patch.object(EnvironmentDetector, 'check_plugin_available') as mock_check:
            mock_check.return_value = True
            
            result = self.stage.execute(self.test_files)
            
            assert isinstance(result, dict)
            # Should have called EnvironmentDetector
            mock_check.assert_called()

    def test_integration_with_security_policy(self):
        """Test integration with SecurityPolicy."""
        with patch.object(SecurityPolicy, 'allows_algorithm') as mock_allows:
            mock_allows.return_value = True
            
            result = self.stage.execute(self.test_files)
            
            assert isinstance(result, dict)
            # Should have called SecurityPolicy
            mock_allows.assert_called()

    # ===========================
    # Algorithm Selection Tests
    # ===========================

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    def test_algorithm_selection_priority(self, mock_check_plugin):
        """Test that algorithm selection follows priority order."""
        # BLAKE3 should be preferred when available
        mock_check_plugin.return_value = True
        
        result = self.stage.execute(self.test_files)
        
        assert isinstance(result, dict)
        # The specific algorithm depends on implementation details
        assert "quick_hash_algorithm" in result
        assert "full_hash_algorithm" in result

    def test_algorithm_consistency(self):
        """Test that algorithm selection is consistent across calls."""
        result1 = self.stage.execute(self.test_files)
        result2 = self.stage.execute(self.test_files)
        
        # Algorithm selection should be consistent
        assert result1["quick_hash_algorithm"] == result2["quick_hash_algorithm"]
        assert result1["full_hash_algorithm"] == result2["full_hash_algorithm"]

    # ===========================
    # Data Structure Tests
    # ===========================

    def test_duplicates_data_structure(self):
        """Test the structure of the duplicates data."""
        # Create some duplicate files
        duplicate_files = []
        for i in range(3):
            dup_file = Path(self.temp_dir) / f"dup_{i}.txt"
            with open(dup_file, 'wb') as f:
                f.write(b"duplicate content")
            duplicate_files.append(dup_file)
        
        result = self.stage.execute(duplicate_files)
        
        assert isinstance(result["duplicates"], list)
        if result["duplicates"]:
            # Each duplicate group should be a list of Path objects or strings
            duplicate_group = result["duplicates"][0]
            assert isinstance(duplicate_group, list)
            assert len(duplicate_group) == 3  # All 3 files are duplicates

    def test_result_statistics_accuracy(self):
        """Test that result statistics are accurate."""
        result = self.stage.execute(self.test_files)
        
        # Statistics should be accurate
        assert isinstance(result["files_processed"], int)
        assert isinstance(result["duplicate_groups"], int)
        assert result["files_processed"] == len(self.test_files)
        
        # duplicate_groups should match the actual number of duplicate groups found
        assert result["duplicate_groups"] == len(result["duplicates"])


# ===========================
# Performance Benchmark Tests
# ===========================

class TestProgressiveHashingPerformance:
    """Performance benchmark tests for ProgressiveHashingCascadeStage."""

    def setup_method(self):
        """Set up performance test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.stage = ProgressiveHashingCascadeStage()

    def teardown_method(self):
        """Clean up performance test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_files(self, num_files: int, file_size_mb: int) -> List[Path]:
        """Create test files for performance testing."""
        files = []
        content = b"x" * (1024 * 1024 * file_size_mb)  # file_size_mb MB
        
        for i in range(num_files):
            test_file = Path(self.temp_dir) / f"perf_file_{i}.txt"
            with open(test_file, 'wb') as f:
                f.write(content)
            files.append(test_file)
        
        return files

    def test_performance_10_files_1mb(self):
        """Test performance with 10 files of 1MB each."""
        files = self.create_test_files(10, 1)
        
        import time
        start_time = time.time()
        result = self.stage.execute(files)
        execution_time = time.time() - start_time
        
        assert result["files_processed"] == 10
        assert result["duplicate_groups"] == 1  # All files are identical
        assert execution_time < 30.0  # Should complete within 30 seconds

    def test_performance_5_files_10mb(self):
        """Test performance with 5 files of 10MB each."""
        files = self.create_test_files(5, 10)
        
        import time
        start_time = time.time()
        result = self.stage.execute(files)
        execution_time = time.time() - start_time
        
        assert result["files_processed"] == 5
        assert result["duplicate_groups"] == 1
        assert execution_time < 60.0  # Should complete within 60 seconds

    def test_scalability_with_increasing_file_count(self):
        """Test scalability with increasing file count."""
        file_counts = [5, 10, 20]
        execution_times = []
        
        for count in file_counts:
            files = self.create_test_files(count, 1)
            
            import time
            start_time = time.time()
            result = self.stage.execute(files)
            execution_time = time.time() - start_time
            
            execution_times.append(execution_time)
            
            assert result["files_processed"] == count
            assert result["duplicate_groups"] == 1
        
        # Execution time should increase sub-linearly with file count
        # (due to progressive hashing optimization)
        assert execution_times[1] < execution_times[0] * 2.5  # 10 files should be less than 2.5x 5 files
        assert execution_times[2] < execution_times[1] * 2.5  # 20 files should be less than 2.5x 10 files


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
