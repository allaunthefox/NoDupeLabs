# Performance Test Utilities
# Helper functions for performance benchmarking and testing

import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
import contextlib
import os
import sys
from unittest.mock import MagicMock, patch

# Platform-specific imports with fallback
try:
    import resource
    RESOURCE_AVAILABLE = True
except ImportError:
    RESOURCE_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

def benchmark_function_performance(
    func: Callable,
    iterations: int = 100,
    warmup_iterations: int = 10,
    *args,
    **kwargs
) -> Dict[str, float]:
    """
    Benchmark a function's performance.

    Args:
        func: Function to benchmark
        iterations: Number of benchmark iterations
        warmup_iterations: Number of warmup iterations
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Dictionary of performance metrics
    """
    # Warmup
    for _ in range(warmup_iterations):
        func(*args, **kwargs)

    # Benchmark
    start_time = time.time()

    for _ in range(iterations):
        func(*args, **kwargs)

    end_time = time.time()

    total_time = end_time - start_time
    avg_time = total_time / iterations
    ops_per_sec = iterations / total_time

    return {
        "total_time": total_time,
        "average_time": avg_time,
        "operations_per_second": ops_per_sec,
        "iterations": iterations
    }

def measure_memory_usage(
    func: Callable,
    iterations: int = 10,
    *args,
    **kwargs
) -> Dict[str, float]:
    """
    Measure memory usage of a function.

    Args:
        func: Function to measure
        iterations: Number of iterations
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Dictionary of memory usage metrics
    """
    if not PSUTIL_AVAILABLE:
        # Fallback implementation when psutil is not available
        # Run the function but return mock memory values
        for _ in range(iterations):
            func(*args, **kwargs)

        return {
            "initial_memory": 0,
            "final_memory": 0,
            "total_memory_used": 0,
            "average_memory_per_call": 0,
            "iterations": iterations,
            "warning": "psutil not available, using fallback implementation"
        }

    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_mem = process.memory_info().rss

    # Run function multiple times
    for _ in range(iterations):
        func(*args, **kwargs)

    # Get final memory usage
    final_mem = process.memory_info().rss

    # Calculate memory usage
    total_memory_used = final_mem - initial_mem
    avg_memory_per_call = total_memory_used / iterations

    return {
        "initial_memory": initial_mem,
        "final_memory": final_mem,
        "total_memory_used": total_memory_used,
        "average_memory_per_call": avg_memory_per_call,
        "iterations": iterations
    }

def create_performance_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create performance test scenarios.

    Returns:
        List of performance test scenarios
    """
    return [
        {
            "name": "small_dataset",
            "data_size": 100,
            "expected_max_time": 0.1,
            "expected_max_memory": 1024 * 1024  # 1MB
        },
        {
            "name": "medium_dataset",
            "data_size": 10000,
            "expected_max_time": 1.0,
            "expected_max_memory": 10 * 1024 * 1024  # 10MB
        },
        {
            "name": "large_dataset",
            "data_size": 1000000,
            "expected_max_time": 10.0,
            "expected_max_memory": 100 * 1024 * 1024  # 100MB
        }
    ]

def simulate_resource_constraints(
    cpu_limit: Optional[float] = None,
    memory_limit: Optional[int] = None
) -> Callable:
    """
    Create a context manager to simulate resource constraints.

    Args:
        cpu_limit: CPU limit (percentage)
        memory_limit: Memory limit in bytes

    Returns:
        Context manager for resource constraints
    """
    @contextlib.contextmanager
    def resource_context():
        original_limits = {}

        try:
            if cpu_limit is not None:
                # Simulate CPU limit by adding artificial delay
                original_limits['cpu'] = cpu_limit

            if memory_limit is not None and RESOURCE_AVAILABLE:
                # Set memory limit using resource module
                if hasattr(resource, 'RLIMIT_AS'):
                    original_limits['memory'] = resource.getrlimit(resource.RLIMIT_AS)
                    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
                else:
                    # Resource module available but RLIMIT_AS not supported
                    print("Warning: RLIMIT_AS not available on this platform")
            elif memory_limit is not None and not RESOURCE_AVAILABLE:
                print("Warning: resource module not available, memory limits will not be enforced")

            yield

        finally:
            # Restore original limits
            if 'memory' in original_limits and RESOURCE_AVAILABLE and hasattr(resource, 'RLIMIT_AS'):
                resource.setrlimit(resource.RLIMIT_AS, original_limits['memory'])

    return resource_context

def create_load_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create load test scenarios.

    Returns:
        List of load test scenarios
    """
    return [
        {
            "name": "low_load",
            "concurrent_users": 10,
            "request_rate": 100,
            "duration": 60,
            "expected_response_time": 0.1
        },
        {
            "name": "medium_load",
            "concurrent_users": 100,
            "request_rate": 1000,
            "duration": 300,
            "expected_response_time": 0.5
        },
        {
            "name": "high_load",
            "concurrent_users": 1000,
            "request_rate": 10000,
            "duration": 600,
            "expected_response_time": 1.0
        }
    ]

def benchmark_file_operations(
    file_size: int = 1024 * 1024,  # 1MB
    operations: List[str] = None,
    iterations: int = 100
) -> Dict[str, float]:
    """
    Benchmark file operations performance.

    Args:
        file_size: Size of test file in bytes
        operations: List of operations to benchmark
        iterations: Number of iterations

    Returns:
        Dictionary of file operation timings
    """
    if operations is None:
        operations = ["read", "write", "copy", "delete"]

    results = {}
    temp_dir = Path(tempfile.mkdtemp())

    try:
        test_file = temp_dir / "test_file.dat"
        test_file_copy = temp_dir / "test_file_copy.dat"

        # Create test file
        with open(test_file, "wb") as f:
            f.write(os.urandom(file_size))

        for op in operations:
            if op == "read":
                def read_operation():
                    with open(test_file, "rb") as f:
                        f.read()

                results[op] = benchmark_function_performance(
                    read_operation, iterations
                )["average_time"]

            elif op == "write":
                def write_operation():
                    with open(test_file, "wb") as f:
                        f.write(os.urandom(file_size))

                results[op] = benchmark_function_performance(
                    write_operation, iterations
                )["average_time"]

            elif op == "copy":
                def copy_operation():
                    import shutil
                    shutil.copy2(test_file, test_file_copy)
                    if test_file_copy.exists():
                        test_file_copy.unlink()

                results[op] = benchmark_function_performance(
                    copy_operation, iterations
                )["average_time"]

            elif op == "delete":
                def delete_operation():
                    test_file.unlink()
                    with open(test_file, "wb") as f:
                        f.write(os.urandom(file_size))

                results[op] = benchmark_function_performance(
                    delete_operation, iterations
                )["average_time"]

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

    return results

def create_performance_monitor() -> Callable:
    """
    Create a performance monitor context manager.

    Returns:
        Context manager for performance monitoring
    """
    @contextlib.contextmanager
    def monitor_context():
        start_time = time.time()

        if PSUTIL_AVAILABLE:
            start_mem = psutil.Process(os.getpid()).memory_info().rss

        yield

        end_time = time.time()

        if PSUTIL_AVAILABLE:
            end_mem = psutil.Process(os.getpid()).memory_info().rss
            memory_used = end_mem - start_mem
            cpu_usage = psutil.cpu_percent(interval=0.1)
        else:
            memory_used = 0
            cpu_usage = 0

        elapsed_time = end_time - start_time

        print(f"Performance Monitor Results:")
        print(f"  Execution Time: {elapsed_time:.4f} seconds")

        if PSUTIL_AVAILABLE:
            print(f"  Memory Used: {memory_used / 1024 / 1024:.2f} MB")
            print(f"  CPU Usage: {cpu_usage}%")
        else:
            print(f"  Memory Used: N/A (psutil not available)")
            print(f"  CPU Usage: N/A (psutil not available)")

    return monitor_context

def simulate_slow_operations(
    delay: float = 0.1,
    variability: float = 0.05
) -> Callable:
    """
    Create a context manager to simulate slow operations.

    Args:
        delay: Base delay in seconds
        variability: Random variability in delay

    Returns:
        Context manager for slow operation simulation
    """
    import random

    @contextlib.contextmanager
    def slow_context():
        original_time = time.time

        def slow_time():
            actual_time = original_time()
            variability_factor = 1.0 + random.uniform(-variability, variability)
            return actual_time + (delay * variability_factor)

        # Patch time functions
        with patch('time.time', side_effect=slow_time):
            with patch('time.sleep', side_effect=lambda x: time.sleep(x * 10)):
                yield

    return slow_context

def create_stress_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create stress test scenarios.

    Returns:
        List of stress test scenarios
    """
    return [
        {
            "name": "memory_stress",
            "type": "memory",
            "target": "high_memory_usage",
            "duration": 300,
            "expected_behavior": "graceful_degradation"
        },
        {
            "name": "cpu_stress",
            "type": "cpu",
            "target": "high_cpu_usage",
            "duration": 180,
            "expected_behavior": "resource_throttling"
        },
        {
            "name": "io_stress",
            "type": "io",
            "target": "high_disk_usage",
            "duration": 240,
            "expected_behavior": "queue_management"
        }
    ]

def benchmark_database_operations(
    db_connection: Any,
    queries: List[str],
    iterations: int = 100
) -> Dict[str, float]:
    """
    Benchmark database operations performance.

    Args:
        db_connection: Database connection
        queries: List of SQL queries to benchmark
        iterations: Number of iterations

    Returns:
        Dictionary of database operation timings
    """
    results = {}

    for i, query in enumerate(queries):
        def query_operation():
            cursor = db_connection.cursor()
            cursor.execute(query)
            cursor.fetchall()
            cursor.close()

        timing = benchmark_function_performance(
            query_operation, iterations
        )["average_time"]

        results[f"query_{i}"] = timing

    return results

def create_network_performance_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create network performance test scenarios.

    Returns:
        List of network performance test scenarios
    """
    return [
        {
            "name": "low_latency",
            "latency": 10,  # ms
            "bandwidth": 100,  # Mbps
            "packet_loss": 0.0  # 0%
        },
        {
            "name": "medium_latency",
            "latency": 100,  # ms
            "bandwidth": 10,  # Mbps
            "packet_loss": 0.1  # 1%
        },
        {
            "name": "high_latency",
            "latency": 500,  # ms
            "bandwidth": 1,  # Mbps
            "packet_loss": 0.5  # 5%
        }
    ]

def measure_concurrency_performance(
    func: Callable,
    worker_counts: List[int] = [1, 2, 4, 8, 16],
    iterations: int = 100,
    *args,
    **kwargs
) -> Dict[int, float]:
    """
    Measure performance with different levels of concurrency.

    Args:
        func: Function to test
        worker_counts: List of worker counts to test
        iterations: Number of iterations per worker count
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Dictionary mapping worker counts to performance metrics
    """
    import concurrent.futures

    results = {}

    for workers in worker_counts:
        def concurrent_operation():
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(func, *args, **kwargs) for _ in range(iterations)]
                concurrent.futures.wait(futures)

        timing = benchmark_function_performance(
            concurrent_operation, 1
        )["total_time"]

        results[workers] = {
            "total_time": timing,
            "throughput": iterations / timing
        }

    return results

def create_performance_regression_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create performance regression test scenarios.

    Returns:
        List of performance regression test scenarios
    """
    return [
        {
            "name": "baseline_performance",
            "description": "Establish baseline performance metrics",
            "metrics": {
                "max_response_time": 0.5,
                "max_memory_usage": 50 * 1024 * 1024,  # 50MB
                "min_throughput": 100  # operations per second
            }
        },
        {
            "name": "regression_detection",
            "description": "Detect performance regressions",
            "thresholds": {
                "response_time_increase": 0.2,  # 20% increase
                "memory_increase": 0.1,  # 10% increase
                "throughput_decrease": 0.15  # 15% decrease
            }
        }
    ]

def simulate_performance_degradation(
    degradation_factor: float = 0.1,
    degradation_type: str = "linear"
) -> Callable:
    """
    Create a context manager to simulate performance degradation.

    Args:
        degradation_factor: Performance degradation factor
        degradation_type: Type of degradation (linear, exponential)

    Returns:
        Context manager for performance degradation simulation
    """
    @contextlib.contextmanager
    def degradation_context():
        call_count = 0

        original_time = time.time
        original_sleep = time.sleep

        def degraded_time():
            nonlocal call_count
            call_count += 1

            if degradation_type == "linear":
                degradation = degradation_factor * call_count
            else:  # exponential
                degradation = degradation_factor ** call_count

            return original_time() + degradation

        def degraded_sleep(seconds):
            original_sleep(seconds * (1 + degradation_factor))

        with patch('time.time', side_effect=degraded_time):
            with patch('time.sleep', side_effect=degraded_sleep):
                yield

    return degradation_context

def create_resource_monitoring_scenarios() -> List[Dict[str, Any]]:
    """
    Create resource monitoring test scenarios.

    Returns:
        List of resource monitoring test scenarios
    """
    return [
        {
            "name": "normal_operation",
            "expected_cpu_usage": 0.3,  # 30%
            "expected_memory_usage": 100 * 1024 * 1024,  # 100MB
            "expected_disk_io": 1024 * 1024  # 1MB/s
        },
        {
            "name": "high_load_operation",
            "expected_cpu_usage": 0.8,  # 80%
            "expected_memory_usage": 500 * 1024 * 1024,  # 500MB
            "expected_disk_io": 10 * 1024 * 1024  # 10MB/s
        },
        {
            "name": "resource_leak_detection",
            "monitoring_duration": 300,  # 5 minutes
            "leak_threshold": 0.05  # 5% increase
        }
    ]
