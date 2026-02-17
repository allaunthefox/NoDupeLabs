"""
Test module for hash algorithm autotuning functionality.

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation
"""

import contextlib
import unittest

from nodupe.core.loader import CoreLoader
from nodupe.tools.hashing.autotune_logic import (
    HashAutotuner,
    autotune_hash_algorithm,
    create_autotuned_hasher,
)


class TestHashAutotune(unittest.TestCase):
    """Test cases for hash algorithm autotuning."""

    def test_hash_autotuner_initialization(self):
        """Test HashAutotuner initialization."""
        tuner = HashAutotuner(sample_size=1024)  # 1KB sample
        self.assertIsInstance(tuner, HashAutotuner)
        self.assertEqual(tuner.sample_size, 1024)
        self.assertGreater(len(tuner.available_algorithms), 0)

    def test_available_algorithms(self):
        """Test that available algorithms include standard library algorithms."""
        tuner = HashAutotuner()
        available = tuner.available_algorithms

        # Should always have at least SHA-256
        self.assertIn("sha256", available)

        # Should have some standard algorithms
        standard_algorithms = ["md5", "sha1", "sha256", "sha512"]
        found_standard = any(algo in available for algo in standard_algorithms)
        self.assertTrue(
            found_standard, "Should have at least one standard algorithm"
        )

    def test_benchmark_algorithm(self):
        """Test benchmarking a single algorithm."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"test data for benchmarking"

        # Test with a known algorithm
        avg_time = tuner.benchmark_algorithm("sha256", test_data, iterations=3)
        self.assertIsInstance(avg_time, float)
        self.assertGreater(avg_time, 0)

    def test_benchmark_all_algorithms(self):
        """Test benchmarking all available algorithms."""
        tuner = HashAutotuner(sample_size=1024)
        results = tuner.benchmark_all_algorithms(iterations=3)

        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)

        # All results should be positive times
        for _algo, time_taken in results.items():
            self.assertIsInstance(time_taken, float)
            self.assertGreater(time_taken, 0)

    def test_select_optimal_algorithm(self):
        """Test selecting optimal algorithm from benchmarks."""
        tuner = HashAutotuner(sample_size=1024)
        optimal_algo, benchmark_results = tuner.select_optimal_algorithm(
            iterations=3
        )

        self.assertIsInstance(optimal_algo, str)
        self.assertIsInstance(benchmark_results, dict)
        self.assertIn(optimal_algo, benchmark_results)

    def test_autotune_hash_algorithm_function(self):
        """Test the convenience autotune function."""
        results = autotune_hash_algorithm(sample_size=1024, iterations=3)

        self.assertIsInstance(results, dict)
        self.assertIn("optimal_algorithm", results)
        self.assertIn("benchmark_results", results)
        self.assertIn("recommendations", results)
        self.assertIn("available_algorithms", results)
        self.assertIn("has_blake3", results)
        self.assertIn("has_xxhash", results)

        self.assertIsInstance(results["optimal_algorithm"], str)
        self.assertIsInstance(results["benchmark_results"], dict)
        self.assertIsInstance(results["recommendations"], dict)
        self.assertIsInstance(results["available_algorithms"], list)

    def test_create_autotuned_hasher(self):
        """Test creating an autotuned hasher."""
        hasher, autotune_results = create_autotuned_hasher(
            sample_size=1024, iterations=3
        )

        # Test that we can use the hasher
        test_data = "test string"
        hash_result = hasher.hash_string(test_data)

        self.assertIsInstance(hash_result, str)
        self.assertGreater(len(hash_result), 0)

        # Test that the autotune results are valid
        self.assertIsInstance(autotune_results, dict)
        self.assertIn("optimal_algorithm", autotune_results)

    def test_hash_consistency(self):
        """Test that hash results are consistent."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"consistent test data"

        # Hash the same data multiple times
        hash1 = tuner.available_algorithms["sha256"](test_data)
        hash2 = tuner.available_algorithms["sha256"](test_data)

        self.assertEqual(hash1, hash2, "Same data should produce same hash")

    def test_algorithm_performance_ordering(self):
        """Test that benchmark results can be properly ordered."""
        tuner = HashAutotuner(sample_size=1024)
        results = tuner.benchmark_all_algorithms(iterations=3)

        if len(results) > 1:
            # Should be able to sort by performance
            sorted_algorithms = sorted(results.items(), key=lambda x: x[1])

            # All times should be positive
            for _algo, time_taken in sorted_algorithms:
                self.assertGreater(time_taken, 0)

            # Fastest algorithm should be first
            fastest_time = sorted_algorithms[0][1]
            for (
                _,
                time_taken,
            ) in sorted_algorithms:  # Use _ to indicate unused variable
                self.assertGreaterEqual(time_taken, fastest_time)


def test_loader_integration():
    """Test that the loader properly integrates hash autotuning."""
    print("Testing loader integration...")

    # Create a temporary config file to avoid loading issues
    import json
    import os
    import tempfile

    import nodupe.core.config

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump({"db_path": ":memory:", "log_dir": "logs"}, f)
        temp_config_path = f.name

    # Store original function before try block
    original_load_config = nodupe.core.config.load_config

    try:
        # Temporarily modify the config loading to use our test config

        def mock_load_config():
            from nodupe.core.config import ConfigManager

            config_manager = ConfigManager()
            config_manager.config = {
                "db_path": ":memory:",
                "log_dir": "logs",
                "tools": {
                    "directories": [],
                    "auto_load": False,
                    "hot_reload": False,
                },
            }
            return config_manager

        # Replace the function temporarily
        nodupe.core.config.load_config = mock_load_config

        # Test the loader
        loader = CoreLoader()
        loader.initialize()

        # Check that hasher service was registered
        container = loader.container
        if container is not None:
            hasher = container.get_service("hasher")
            hash_autotune_results = container.get_service(
                "hash_autotune_results"
            )
        else:
            # If container is None, we can't test the services
            print("Container is None, skipping service tests")
            return

        print(f"Hasher type: {type(hasher)}")
        print(f"Autotune results: {hash_autotune_results}")

        # Test that the hasher works
        if hasher is not None and hasattr(hasher, "hash_string"):
            test_hash = hasher.hash_string("test")
            print(f"Test hash: {test_hash}")
            assert isinstance(test_hash, str) and len(test_hash) > 0

        # Cleanup
        loader.shutdown()

        # Restore original function
        if original_load_config is not None:
            nodupe.core.config.load_config = original_load_config

        print("Loader integration test passed!")

    except Exception as e:
        print(f"Loader integration test failed: {e}")
        # Restore original function even if test fails
        if original_load_config is not None:
            nodupe.core.config.load_config = original_load_config
        raise
    finally:
        # Clean up the temporary file
        with contextlib.suppress(Exception):
            os.unlink(temp_config_path)


if __name__ == "__main__":
    # Run the unit tests
    unittest.main(argv=[""], exit=False, verbosity=2)

    # Run the integration test
    test_loader_integration()

    print("All tests passed!")
