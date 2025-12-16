"""
Hash Algorithm Autotune Module
Automatically selects the optimal hash algorithm based on system characteristics and performance benchmarks.
"""

import time
import hashlib
from typing import Dict, Tuple, Callable, Any

# Check for optional dependencies


def _check_blake3():
    try:
        import importlib.util
        spec = importlib.util.find_spec("blake3")
        if spec is not None:
            import blake3  # type: ignore
            return True, blake3
        else:
            return False, None
    except ImportError:
        return False, None


def _check_xxhash():
    try:
        import importlib.util
        spec = importlib.util.find_spec("xxhash")
        if spec is not None:
            import xxhash  # type: ignore
            return True, xxhash
        else:
            return False, None
    except ImportError:
        return False, None


HAS_BLAKE3, BLAKE3_MODULE = _check_blake3()
HAS_XXHASH, XXHASH_MODULE = _check_xxhash()

# Type aliases for better type checking
HashFunction = Callable[[bytes], str]


class HashAutotuner:
    """Automatic hash algorithm tuner that benchmarks and selects optimal algorithm."""

    def __init__(self, sample_size: int = 1024 * 1024):  # 1MB sample
        """Initialize the hash autotuner.

        Args:
            sample_size: Size of test data in bytes for benchmarking
        """
        self.sample_size = sample_size
        self.available_algorithms = self._get_available_algorithms()

    def _get_available_algorithms(self) -> Dict[str, Any]:
        """Get all available hash algorithms including optional ones."""
        algorithms: Dict[str, Any] = {}

        # Standard library algorithms
        for algo in hashlib.algorithms_available:
            try:
                hashlib.new(algo)

                def create_hashlib_func(algorithm_name: str) -> HashFunction:
                    def hash_func(data: bytes) -> str:
                        hasher = hashlib.new(algorithm_name)
                        hasher.update(data)
                        # Handle SHAKE algorithms that require length parameter
                        if algorithm_name.startswith('shake_'):
                            # SHAKE algorithms require length parameter for both digest() and hexdigest()
                            # Use hexdigest(32) for SHAKE - suppress Pylance warning as this is correct
                            return hasher.hexdigest(32)  # type: ignore
                        else:
                            return hasher.hexdigest()
                    return hash_func

                algorithms[algo] = create_hashlib_func(algo)
            except Exception:
                continue

        # Add BLAKE3 if available
        if HAS_BLAKE3 and BLAKE3_MODULE is not None:
            def blake3_func(data: bytes) -> str:
                if BLAKE3_MODULE:
                    return BLAKE3_MODULE.blake3(data).hexdigest()
                return hashlib.sha256(data).hexdigest()  # fallback
            algorithms['blake3'] = blake3_func

        # Add xxHash if available
        if HAS_XXHASH and XXHASH_MODULE is not None:
            def xxh3_func(data: bytes) -> str:
                if XXHASH_MODULE:
                    return XXHASH_MODULE.xxh3_64(data).hexdigest()
                return hashlib.sha256(data).hexdigest()  # fallback

            def xxh64_func(data: bytes) -> str:
                if XXHASH_MODULE:
                    return XXHASH_MODULE.xxh64(data).hexdigest()
                return hashlib.sha256(data).hexdigest()  # fallback

            def xxh128_func(data: bytes) -> str:
                if XXHASH_MODULE:
                    return XXHASH_MODULE.xxh128(data).hexdigest()
                return hashlib.sha256(data).hexdigest()  # fallback

            algorithms['xxh3'] = xxh3_func
            algorithms['xxh64'] = xxh64_func
            algorithms['xxh128'] = xxh128_func

        return algorithms

    def _generate_test_data(self) -> bytes:
        """Generate test data for benchmarking."""
        # Create predictable test data to ensure consistent benchmarks
        data = b""
        chunk = b"x" * min(self.sample_size, 65536)  # 64KB chunks
        remaining = self.sample_size

        while remaining > 0:
            chunk_size = min(remaining, len(chunk))
            data += chunk[:chunk_size]
            remaining -= chunk_size

        return data

    def benchmark_algorithm(self, algorithm_name: str, test_data: bytes,
                            iterations: int = 10) -> float:
        """Benchmark a single hash algorithm.

        Args:
            algorithm_name: Name of the algorithm to benchmark
            test_data: Test data to hash
            iterations: Number of iterations for averaging

        Returns:
            Average time per hash operation in seconds
        """
        if algorithm_name not in self.available_algorithms:
            raise ValueError(f"Algorithm {algorithm_name} not available")

        algorithm_func = self.available_algorithms[algorithm_name]

        start_time = time.time()

        for _ in range(iterations):
            _ = algorithm_func(test_data)

        total_time = time.time() - start_time
        avg_time = total_time / iterations

        return avg_time

    def benchmark_all_algorithms(self, iterations: int = 10) -> Dict[str, float]:
        """Benchmark all available algorithms.

        Args:
            iterations: Number of iterations for each algorithm

        Returns:
            Dictionary mapping algorithm names to average execution times
        """
        test_data = self._generate_test_data()
        results: Dict[str, float] = {}

        for algorithm_name in self.available_algorithms:
            try:
                avg_time = self.benchmark_algorithm(algorithm_name, test_data, iterations)
                results[algorithm_name] = avg_time
            except Exception as e:
                print(f"[WARNING] Failed to benchmark {algorithm_name}: {e}")
                continue

        return results

    def select_optimal_algorithm(self, iterations: int = 10,
                                 memory_constrained: bool = False) -> Tuple[str, Dict[str, float]]:
        """Select the optimal hash algorithm based on benchmark results.

        Args:
            iterations: Number of iterations for benchmarking
            memory_constrained: Whether to prioritize memory-efficient algorithms

        Returns:
            Tuple of (optimal_algorithm_name, benchmark_results)
        """
        benchmark_results = self.benchmark_all_algorithms(iterations)

        if not benchmark_results:
            # Fallback to SHA-256 if no algorithms are available
            return 'sha256', {'sha256': float('inf')}

        # Sort by fastest performance
        sorted_algorithms = sorted(benchmark_results.items(), key=lambda x: x[1])

        # Consider additional factors for selection
        optimal_algorithm = sorted_algorithms[0][0]

        # If memory constrained and BLAKE3 is fast, prefer it
        if memory_constrained and 'blake3' in benchmark_results:
            blake3_time = benchmark_results['blake3']
            sha256_time = benchmark_results.get('sha256', float('inf'))

            # If BLAKE3 is competitive and more memory efficient
            if blake3_time <= sha256_time * 1.2:  # Within 20% of SHA-256
                optimal_algorithm = 'blake3'

        return optimal_algorithm, benchmark_results

    def get_algorithm_recommendation(self, file_size_threshold: int = 10 * 1024 * 1024) -> Dict[str, str]:
        """Get algorithm recommendations based on file size characteristics.

        Args:
            file_size_threshold: Threshold in bytes to determine algorithm choice

        Returns:
            Dictionary with recommendations for different scenarios
        """
        recommendations: Dict[str, str] = {}

        # For small files, speed is most important
        small_files_algo, _ = self.select_optimal_algorithm(iterations=5)
        recommendations['small_files'] = small_files_algo

        # For large files, consider streaming efficiency
        if HAS_BLAKE3:
            recommendations['large_files'] = 'blake3'
        elif 'sha256' in self.available_algorithms:
            recommendations['large_files'] = 'sha256'
        else:
            recommendations['large_files'] = small_files_algo

        # Overall recommendation
        overall_algo, _ = self.select_optimal_algorithm(iterations=10)
        recommendations['overall'] = overall_algo

        return recommendations


def autotune_hash_algorithm(sample_size: int = 1024 * 1024,
                            file_size_threshold: int = 10 * 1024 * 1024,
                            iterations: int = 10) -> Dict[str, Any]:
    """Convenience function to autotune hash algorithm.

    Args:
        sample_size: Size of test data in bytes
        file_size_threshold: Threshold for file size recommendations
        iterations: Number of benchmark iterations

    Returns:
        Dictionary containing optimal algorithm and benchmark results
    """
    tuner = HashAutotuner(sample_size)

    optimal_algorithm, benchmark_results = tuner.select_optimal_algorithm(iterations)
    recommendations = tuner.get_algorithm_recommendation(file_size_threshold)

    return {
        'optimal_algorithm': optimal_algorithm,
        'benchmark_results': benchmark_results,
        'recommendations': recommendations,
        'available_algorithms': list(tuner.available_algorithms.keys()),
        'has_blake3': HAS_BLAKE3,
        'has_xxhash': HAS_XXHASH
    }


def create_autotuned_hasher(**kwargs: Any) -> Tuple[Any, Dict[str, Any]]:
    """Create a FileHasher with autotuned algorithm and return tuning results.

    Args:
        **kwargs: Arguments passed to autotune_hash_algorithm

    Returns:
        Tuple of (FileHasher instance, autotune results)
    """
    import hashlib
    from .hasher import FileHasher  # Import at function level to avoid circular import

    autotune_results = autotune_hash_algorithm(**kwargs)

    # Filter to only use algorithms available in standard library for FileHasher
    available_algorithms = set(hashlib.algorithms_available)
    all_benchmark_results = autotune_results['benchmark_results']

    # Find the best performing algorithm that's available in standard library
    filtered_results = {algo: time for algo, time in all_benchmark_results.items()
                        if algo in available_algorithms}

    if filtered_results:
        # Use the best performing standard library algorithm
        optimal_algorithm = min(filtered_results.keys(), key=lambda k: filtered_results[k])
    else:
        # Fallback to SHA-256 if no standard algorithms are available
        optimal_algorithm = 'sha256'

    hasher = FileHasher(algorithm=optimal_algorithm)

    # Update the autotune results to reflect the actual algorithm used
    updated_results = autotune_results.copy()
    updated_results['optimal_algorithm'] = optimal_algorithm

    result = (hasher, updated_results)  # type: ignore
    return result
