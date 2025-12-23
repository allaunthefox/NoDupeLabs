"""
Test suite for parallel processing functionality.
Tests parallel operations from nodupe.core.parallel.
"""

import os
import tempfile
import shutil
from pathlib import Path
import time
import pytest
from unittest.mock import patch

from nodupe.core.parallel import Parallel, ParallelError, ParallelProgress, parallel_map, parallel_filter, parallel_partition, parallel_starmap


class TestParallel:
    """Test Parallel functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parallel_initialization(self):
        """Test Parallel class initialization."""
        # Parallel is a utility class with static methods, so just verify it exists
        assert Parallel is not None
        assert hasattr(Parallel, 'get_cpu_count')
        assert hasattr(Parallel, 'process_in_parallel')
        assert hasattr(Parallel, 'map_parallel')
        assert hasattr(Parallel, 'smart_map')
    
    def test_get_cpu_count(self):
        """Test getting CPU count."""
        cpu_count = Parallel.get_cpu_count()
        assert isinstance(cpu_count, int)
        assert cpu_count > 0
    
    def test_is_free_threaded(self):
        """Test free-threaded mode detection."""
        result = Parallel.is_free_threaded()
        assert isinstance(result, bool)
    
    def test_get_python_version_info(self):
        """Test getting Python version info."""
        version = Parallel.get_python_version_info()
        assert isinstance(version, tuple)
        assert len(version) == 2
        assert isinstance(version[0], int)
        assert isinstance(version[1], int)
        assert version[0] >= 3  # Python 3.x
    
    def test_supports_interpreter_pool(self):
        """Test interpreter pool support detection."""
        result = Parallel.supports_interpreter_pool()
        assert isinstance(result, bool)
    
    def test_process_in_parallel_basic(self):
        """Test basic parallel processing."""
        def square(x):
            return x * x
        
        items = [1, 2, 3, 4, 5]
        results = Parallel.process_in_parallel(square, items, workers=2)
        
        assert results == [1, 4, 9, 16, 25]
        assert len(results) == len(items)
    
    def test_process_in_parallel_with_threads(self):
        """Test parallel processing with threads."""
        def add_one(x):
            return x + 1
        
        items = [1, 2, 3, 4]
        results = Parallel.process_in_parallel(add_one, items, workers=2, use_processes=False)
        
        assert results == [2, 3, 4, 5]
        assert len(results) == len(items)
    
    def test_process_in_parallel_with_processes(self):
        """Test parallel processing with processes."""
        def multiply_by_two(x):
            return x * 2
        
        items = [1, 2, 3, 4]
        results = Parallel.process_in_parallel(multiply_by_two, items, workers=2, use_processes=True)
        
        assert results == [2, 4, 6, 8]
        assert len(results) == len(items)
    
    def test_process_in_parallel_empty_list(self):
        """Test parallel processing with empty list."""
        def identity(x):
            return x
        
        results = Parallel.process_in_parallel(identity, [], workers=2)
        assert results == []
    
    def test_process_in_parallel_single_item(self):
        """Test parallel processing with single item."""
        def identity(x):
            return x
        
        results = Parallel.process_in_parallel(identity, [42], workers=1)
        assert results == [42]
    
    def test_process_in_parallel_timeout(self):
        """Test parallel processing with timeout."""
        def slow_func(x):
            time.sleep(0.1)
            return x * 2
        
        items = [1, 2]
        
        # Should work with sufficient timeout
        results = Parallel.process_in_parallel(slow_func, items, workers=2, timeout=0.5)
        assert results == [2, 4]
        
        # Test with timeout that's too short (this might raise an exception in real usage)
        with pytest.raises(ParallelError):
            Parallel.process_in_parallel(slow_func, items, workers=2, timeout=0.01)
    
    def test_map_parallel_basic(self):
        """Test basic parallel mapping."""
        def square(x):
            return x * x
        
        items = [1, 2, 3, 4, 5]
        results = Parallel.map_parallel(square, items, workers=2)
        
        assert results == [1, 4, 9, 16, 25]
        assert len(results) == len(items)
    
    def test_map_parallel_with_processes(self):
        """Test parallel mapping with processes."""
        def cube(x):
            return x ** 3
        
        items = [1, 2, 3]
        results = Parallel.map_parallel(cube, items, workers=2, use_processes=True)
        
        assert results == [1, 8, 27]
        assert len(results) == len(items)
    
    def test_map_parallel_with_interpreters(self):
        """Test parallel mapping with interpreters (fallback to threads)."""
        def identity(x):
            return x
        
        items = [1, 2, 3]
        results = Parallel.map_parallel(identity, items, workers=2, use_interpreters=True)
        
        assert results == [1, 2, 3]
        assert len(results) == len(items)
    
    def test_map_parallel_chunk_size(self):
        """Test parallel mapping with chunk size."""
        def identity(x):
            return x
        
        items = [1, 2, 3, 4, 5]
        results = Parallel.map_parallel(identity, items, workers=2, chunk_size=2)
        
        assert results == [1, 2, 3, 4, 5]
        assert len(results) == len(items)
    
    def test_map_parallel_empty_list(self):
        """Test parallel mapping with empty list."""
        def identity(x):
            return x
        
        results = Parallel.map_parallel(identity, [], workers=2)
        assert results == []
    
    def test_map_parallel_unordered_basic(self):
        """Test basic unordered parallel mapping."""
        def square(x):
            return x * x
        
        items = [1, 2, 3, 4, 5]
        results = list(Parallel.map_parallel_unordered(square, items, workers=2))
        
        assert set(results) == {1, 4, 9, 16, 25}
        assert len(results) == len(items)
    
    def test_map_parallel_unordered_with_processes(self):
        """Test unordered parallel mapping with processes."""
        def double(x):
            return x * 2
        
        items = [1, 2, 3, 4]
        results = list(Parallel.map_parallel_unordered(double, items, workers=2, use_processes=True))
        
        assert set(results) == {2, 4, 6, 8}
        assert len(results) == len(items)
    
    def test_map_parallel_unordered_empty_list(self):
        """Test unordered parallel mapping with empty list."""
        def identity(x):
            return x
        
        results = list(Parallel.map_parallel_unordered(identity, [], workers=2))
        assert results == []
    
    def test_smart_map_cpu_bound(self):
        """Test smart map for CPU-bound tasks."""
        def cpu_intensive(x):
            # Simulate CPU-intensive work
            result = 0
            for i in range(1000):
                result += i * x
            return result
        
        items = [1, 2, 3]
        results = Parallel.smart_map(cpu_intensive, items, task_type='cpu', workers=2)
        
        assert len(results) == len(items)
        assert all(isinstance(r, int) for r in results)
    
    def test_smart_map_io_bound(self):
        """Test smart map for I/O-bound tasks."""
        def io_simulation(x):
            time.sleep(0.01)  # Simulate I/O delay
            return x + 100
        
        items = [1, 2, 3]
        results = Parallel.smart_map(io_simulation, items, task_type='io', workers=2)
        
        assert results == [101, 102, 103]
        assert len(results) == len(items)
    
    def test_smart_map_auto_detect(self):
        """Test smart map with auto detection."""
        def simple_add(x):
            return x + 1
        
        items = [1, 2, 3, 4]
        results = Parallel.smart_map(simple_add, items, task_type='auto', workers=2)
        
        assert results == [2, 3, 4, 5]
        assert len(results) == len(items)
    
    def test_get_optimal_workers_cpu_task(self):
        """Test getting optimal workers for CPU tasks."""
        workers = Parallel.get_optimal_workers('cpu')
        assert isinstance(workers, int)
        assert workers > 0
    
    def test_get_optimal_workers_io_task(self):
        """Test getting optimal workers for I/O tasks."""
        workers = Parallel.get_optimal_workers('io')
        assert isinstance(workers, int)
        assert workers > 0
    
    def test_process_batches(self):
        """Test processing items in batches."""
        def sum_batch(batch):
            return sum(batch)
        
        items = [1, 2, 3, 4, 5, 6, 7, 8]
        results = Parallel.process_batches(sum_batch, items, batch_size=3, workers=2)
        
        # Should have 3 batches: [1,2,3], [4,5,6], [7,8]
        assert len(results) == 3
        assert results == [6, 15, 15]  # [1+2+3, 4+5+6, 7+8]
    
    def test_process_batches_single_batch(self):
        """Test processing items in single batch."""
        def sum_batch(batch):
            return sum(batch)
        
        items = [1, 2, 3]
        results = Parallel.process_batches(sum_batch, items, batch_size=10, workers=1)
        
        assert results == [6]  # Single batch with sum of all items
        assert len(results) == 1
    
    def test_reduce_parallel(self):
        """Test parallel reduce operation."""
        def square(x):
            return x * x
        
        def add(x, y):
            return x + y
        
        items = [1, 2, 3, 4]  # Squares: [1, 4, 9, 16], sum: 30
        result = Parallel.reduce_parallel(square, add, items, initial=0, workers=2)
        
        assert result == 30  # 1 + 4 + 9 + 16 = 30
    
    def test_reduce_parallel_no_initial(self):
        """Test parallel reduce without initial value."""
        def identity(x):
            return x
        
        def add(x, y):
            return x + y
        
        items = [1, 2, 3, 4]
        result = Parallel.reduce_parallel(identity, add, items, workers=2)
        
        assert result == 10  # 1 + 2 + 3 + 4 = 10
    
    def test_reduce_parallel_empty_list(self):
        """Test parallel reduce with empty list and initial value."""
        def identity(x):
            return x
        
        def add(x, y):
            return x + y
        
        result = Parallel.reduce_parallel(identity, add, [], initial=5, workers=1)
        
        assert result == 5


class TestParallelProgress:
    """Test ParallelProgress functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parallel_progress_initialization(self):
        """Test ParallelProgress initialization."""
        progress = ParallelProgress(total=100)
        
        assert progress.total == 100
        assert progress.completed == 0
        assert progress.failed == 0
        
        completed, failed, percentage = progress.get_progress()
        assert completed == 0
        assert failed == 0
        assert percentage == 0.0
        assert progress.is_complete is False
    
    def test_parallel_progress_increment_success(self):
        """Test incrementing progress for successful tasks."""
        progress = ParallelProgress(total=10)
        
        progress.increment(success=True)
        progress.increment(success=True)
        
        completed, failed, percentage = progress.get_progress()
        assert completed == 2
        assert failed == 0
        assert percentage == 20.0  # 2/10 = 20%
    
    def test_parallel_progress_increment_failure(self):
        """Test incrementing progress for failed tasks."""
        progress = ParallelProgress(total=10)
        
        progress.increment(success=False)
        progress.increment(success=True)
        
        completed, failed, percentage = progress.get_progress()
        assert completed == 1
        assert failed == 1
        assert percentage == 20.0  # 2/10 = 20%
    
    def test_parallel_progress_completion(self):
        """Test progress completion tracking."""
        progress = ParallelProgress(total=5)
        
        # Complete all items
        for _ in range(5):
            progress.increment(success=True)
        
        assert progress.is_complete is True
        
        completed, failed, percentage = progress.get_progress()
        assert completed == 5
        assert failed == 0
        assert percentage == 100.0
    
    def test_parallel_progress_thread_safety(self):
        """Test thread safety of progress tracking."""
        import threading
        progress = ParallelProgress(total=100)
        
        def worker():
            for i in range(10):
                progress.increment(success=True)
        
        threads = []
        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        completed, failed, percentage = progress.get_progress()
        assert completed == 100
        assert percentage == 100.0
        assert progress.is_complete is True


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parallel_map_convenience(self):
        """Test parallel_map convenience function."""
        def square(x):
            return x * x
        
        items = [1, 2, 3, 4, 5]
        results = parallel_map(square, items, workers=2)
        
        assert results == [1, 4, 9, 16, 25]
        assert len(results) == len(items)
    
    def test_parallel_filter(self):
        """Test parallel_filter function."""
        def is_even(x):
            return x % 2 == 0
        
        items = [1, 2, 3, 4, 5, 6, 7, 8]
        results = parallel_filter(is_even, items, workers=2)
        
        assert results == [2, 4, 6, 8]
        assert all(x % 2 == 0 for x in results)
    
    def test_parallel_partition(self):
        """Test parallel_partition function."""
        def is_positive(x):
            return x > 0
        
        items = [-2, -1, 0, 1, 2, 3]
        true_items, false_items = parallel_partition(is_positive, items, workers=2)
        
        assert set(true_items) == {1, 2, 3}
        assert set(false_items) == {-2, -1, 0}
        assert len(true_items) + len(false_items) == len(items)
    
    def test_parallel_starmap(self):
        """Test parallel_starmap function."""
        def add(a, b):
            return a + b
        
        args_list = [(1, 2), (3, 4), (5, 6), (7, 8)]
        results = parallel_starmap(add, args_list, workers=2)
        
        assert results == [3, 7, 11, 15]  # [1+2, 3+4, 5+6, 7+8]
        assert len(results) == len(args_list)
    
    def test_parallel_starmap_empty_args(self):
        """Test parallel_starmap with empty arguments list."""
        def add(a, b):
            return a + b
        
        results = parallel_starmap(add, [], workers=1)
        assert results == []


def test_parallel_error_exception():
    """Test ParallelError exception."""
    try:
        raise ParallelError("Test error")
    except ParallelError as e:
        assert str(e) == "Test error"
        assert isinstance(e, Exception)


def test_parallel_error_handling():
    """Test error handling in Parallel operations."""
    def failing_func(x):
        if x == 2:
            raise ValueError("Test failure")
        return x * 2
    
    items = [1, 2, 3]
    
    # Test that errors are properly handled and wrapped
    with pytest.raises(ParallelError):
        Parallel.process_in_parallel(failing_func, items, workers=2)


if __name__ == "__main__":
    pytest.main([__file__])
