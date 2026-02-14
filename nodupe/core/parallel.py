"""Parallel Module.

Parallel processing utilities using standard library only.

Key Features:
    - Process pool for CPU-bound tasks
    - Thread pool for I/O-bound tasks
    - Interpreter pool for Python 3.14+ free-threaded tasks
    - Parallel map operations
    - Progress tracking
    - Error handling in parallel tasks
    - Standard library only (no external dependencies)

Dependencies:
    - multiprocessing (standard library)
    - concurrent.futures (standard library)
    - threading (standard library)
    - sys (for GIL detection)
"""

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import cpu_count
from typing import Callable, List, Any, Optional, Iterator, Tuple
import threading
import sys
import time
import logging
import os


def _process_batch_worker(func_and_batch):
    """Worker that processes a batch of items with a provided function.

    Accepts a (func, batch) tuple so the callable is a top-level object and can be
    pickled for ProcessPoolExecutor.
    """
    func, batch = func_and_batch
    return [func(x) for x in batch]


class ParallelError(Exception):
    """Parallel processing error"""


class Parallel:
    """Handle parallel processing operations.

    Provides both thread-based and process-based parallelism
    with support for mapping functions over iterables.
    """

    @staticmethod
    def get_cpu_count() -> int:
        """Get number of CPU cores.

        Returns:
            Number of CPU cores
        """
        try:
            return cpu_count()
        except Exception:
            return 1  # Fallback to single core

    @staticmethod
    def is_free_threaded() -> bool:
        """Check if running in free-threaded mode (Python 3.13+ with --disable-gil).

        Returns:
            True if running in free-threaded mode, False otherwise
        """
        return hasattr(sys, 'flags') and getattr(sys.flags, 'gil', 1) == 0

    @staticmethod
    def get_python_version_info() -> Tuple[int, int]:
        """Get current Python version as (major, minor) tuple.

        Returns:
            Tuple of (major, minor) version numbers
        """
        return (sys.version_info.major, sys.version_info.minor)

    @staticmethod
    def supports_interpreter_pool() -> bool:
        """Check if current Python version supports InterpreterPoolExecutor.

        Returns:
            True if InterpreterPoolExecutor is available, False otherwise
        """
        major, minor = Parallel.get_python_version_info()
        return major >= 3 and minor >= 14

    @staticmethod
    def process_in_parallel(
        func: Callable,
        items: List[Any],
        workers: Optional[int] = None,
        use_processes: bool = False,
        use_interpreters: bool = False,
        timeout: Optional[float] = None
    ) -> List[Any]:
        """Process items in parallel.

        Args:
            func: Function to apply to each item
            items: List of items to process
            workers: Number of workers (None = CPU count)
            use_processes: Use processes instead of threads
            use_interpreters: Use interpreters instead of threads/processes (Python 3.14+)
            timeout: Maximum time per task in seconds

        Returns:
            List of results in same order as items

        Raises:
            ParallelError: If parallel processing fails
        """
        try:
            # Determine number of workers
            if workers is None:
                workers = Parallel.get_cpu_count() if use_processes else min(32, len(items))

            # Choose executor based on options
            if use_interpreters and Parallel.supports_interpreter_pool():
                try:
                    from concurrent.futures import InterpreterPoolExecutor
                    executor_class = InterpreterPoolExecutor
                except ImportError:
                    # Fallback to ThreadPoolExecutor if InterpreterPoolExecutor not available
                    executor_class = ThreadPoolExecutor
            elif use_processes:
                executor_class = ProcessPoolExecutor
            else:
                executor_class = ThreadPoolExecutor

            # Process in parallel (instrumented)
            with executor_class(max_workers=workers) as executor:
                start_submit = time.monotonic()
                futures = [executor.submit(func, item) for item in items]
                submit_end = time.monotonic()
                logging.getLogger(__name__).debug(
                    "Submitted %d tasks in %.3fs", len(futures), submit_end - start_submit
                )

                results = []

                for idx, future in enumerate(futures):
                    try:
                        t0 = time.monotonic()
                        result = future.result(timeout=timeout)
                        t1 = time.monotonic()
                        logging.getLogger(__name__).debug(
                            "Task %d completed in %.3fs", idx, t1 - t0
                        )
                        results.append(result)
                    except Exception as e:
                        logging.getLogger(__name__).exception("Task %d failed", idx)
                        raise ParallelError(f"Task failed: {e}") from e

                return results

        except Exception as e:
            if isinstance(e, ParallelError):
                raise
            raise ParallelError(f"Parallel processing failed: {e}") from e

    @staticmethod
    def map_parallel(
        func: Callable,
        items: List[Any],
        workers: Optional[int] = None,
        use_processes: bool = False,
        use_interpreters: bool = False,
        chunk_size: int = 1
    ) -> List[Any]:
        """Map function over items in parallel.

        Args:
            func: Function to map
            items: Items to map over
            workers: Number of workers
            use_processes: Use processes instead of threads
            use_interpreters: Use interpreters instead of threads/processes (Python 3.14+)
            chunk_size: Items per chunk for process pool

        Returns:
            List of results

        Raises:
            ParallelError: If mapping fails
        """
        try:
            # Determine number of workers
            if workers is None:
                workers = Parallel.get_cpu_count() if use_processes else min(32, len(items))

            # Choose executor based on options
            if use_interpreters and Parallel.supports_interpreter_pool():
                try:
                    from concurrent.futures import InterpreterPoolExecutor
                    executor_class = InterpreterPoolExecutor
                except ImportError:
                    # Fallback to ThreadPoolExecutor if InterpreterPoolExecutor not available
                    executor_class = ThreadPoolExecutor
            elif use_processes:
                executor_class = ProcessPoolExecutor
            else:
                executor_class = ThreadPoolExecutor

            # Map in parallel
            with executor_class(max_workers=workers) as executor:
                if use_interpreters or use_processes:
                    results = list(executor.map(func, items, chunksize=chunk_size))
                else:
                    results = list(executor.map(func, items))

                return results

        except Exception as e:
            raise ParallelError(f"Parallel map failed: {e}") from e

    @staticmethod
    def map_parallel_unordered(
        func: Callable,
        items: List[Any],
        workers: Optional[int] = None,
        use_processes: bool = False,
        use_interpreters: bool = False,
        timeout: Optional[float] = None,
        prefer_map: bool = True,
        prefer_batches: bool = True
    ) -> Iterator[Any]:
        """Map function over items in parallel, yielding results as completed.

        Args:
            func: Function to map
            items: Items to map over
            workers: Number of workers
            use_processes: Use processes instead of threads
            use_interpreters: Use interpreters instead of threads/processes (Python 3.14+)
            timeout: Maximum time per task
            prefer_map: When True, prefer executor.map for process pools (lower per-task overhead)
            prefer_batches: When True, prefer batch-processing (coarse batches) for process pools

        Yields:
            Results as they complete

        Raises:
            ParallelError: If mapping fails
        """
        try:
            # Runtime knobs via environment variables
            try:
                batch_divisor = int(os.getenv("NODUPE_BATCH_DIVISOR", "256"))
            except Exception:
                batch_divisor = 256
            try:
                chunk_factor = int(os.getenv("NODUPE_CHUNK_FACTOR", "1024"))
            except Exception:
                chunk_factor = 1024
            batch_logging = os.getenv("NODUPE_BATCH_LOG", "0") in ("1", "true", "True", "yes", "on")
            # Determine number of workers
            if workers is None:
                workers = Parallel.get_cpu_count() if use_processes else min(32, len(items))

            # For process pools, avoid oversubscription: cap workers to (cpu_count - 1) if possible
            if use_processes:
                try:
                    cpu = Parallel.get_cpu_count()
                    workers = min(workers, max(1, cpu - 1))
                except Exception:
                    # keep provided workers if cpu count fails
                    pass

            # Choose executor based on options
            if use_interpreters and Parallel.supports_interpreter_pool():
                try:
                    from concurrent.futures import InterpreterPoolExecutor
                    executor_class = InterpreterPoolExecutor
                except ImportError:
                    # Fallback to ThreadPoolExecutor if InterpreterPoolExecutor not available
                    executor_class = ThreadPoolExecutor
            elif use_processes:
                executor_class = ProcessPoolExecutor
            else:
                executor_class = ThreadPoolExecutor

            # Submit tasks; for process pools prefer executor.map or batch mapping to reduce overhead
            with executor_class(max_workers=workers) as executor:
                if use_processes and prefer_batches:
                    try:
                        batch_size = max(1, len(items) // (max(1, workers) * batch_divisor))
                    except Exception:
                        batch_size = 1

                    if batch_size <= 1:
                        # Fallback to chunksize mapping if batches would be size 1
                        try:
                            chunksize = max(1, len(items) // (max(1, workers) * chunk_factor))
                        except Exception:
                            chunksize = 1
                        for result in executor.map(func, items, chunksize=chunksize):
                            yield result
                    else:
                        # Map batches using a top-level helper so callables are picklable
                        batches = [items[i:i + batch_size]
                                   for i in range(0, len(items), batch_size)]
                        paired = [(func, b) for b in batches]
                        prev = time.monotonic()
                        for batch_result in executor.map(_process_batch_worker, paired):
                            now = time.monotonic()
                            duration = now - prev
                            prev = now
                            if batch_logging:
                                try:
                                    logging.getLogger(__name__).debug(
                                        "batch size=%d processed in %.3fs", len(
                                            batch_result), duration
                                    )
                                except Exception:
                                    pass
                            for r in batch_result:
                                yield r
                elif use_processes and prefer_map:
                    # Auto-balance chunksize: smaller chunks reduce per-task overhead but increase scheduling;
                    # use a conservative factor to amortize pickling/IPC work.
                    try:
                        chunksize = max(1, len(items) // (max(1, workers) * chunk_factor))
                    except Exception:
                        chunksize = 1
                    for result in executor.map(func, items, chunksize=chunksize):
                        yield result
                else:
                    # Use bounded submission for threads or when prefer_map is False for processes
                    it = iter(items)
                    futures = set()

                    # Submit initial batch up to worker count
                    try:
                        for _ in range(min(workers, len(items))):
                            futures.add(executor.submit(func, next(it)))
                    except StopIteration:
                        pass

                    # Iterate, yielding as futures complete and submitting new tasks
                    while futures:
                        for future in concurrent.futures.as_completed(futures, timeout=timeout):
                            try:
                                result = future.result()
                                yield result
                            except Exception as e:
                                raise ParallelError(f"Task failed: {e}") from e
                            finally:
                                # Remove completed future and submit next item if available
                                try:
                                    futures.remove(future)
                                except KeyError:
                                    pass

                                try:
                                    nxt = next(it)
                                    futures.add(executor.submit(func, nxt))
                                except StopIteration:
                                    pass

        except Exception as e:
            if isinstance(e, ParallelError):
                raise
            raise ParallelError(f"Parallel map failed: {e}") from e

    @staticmethod
    def smart_map(
        func: Callable,
        items: List[Any],
        task_type: str = 'auto',
        workers: Optional[int] = None,
        timeout: Optional[float] = None
    ) -> List[Any]:
        """Smart map that automatically chooses the best executor based on Python version and task type.

        Args:
            func: Function to map
            items: Items to map over
            task_type: 'cpu', 'io', or 'auto' - type of task
            workers: Number of workers (None = auto-detect)
            timeout: Maximum time per task

        Returns:
            List of results

        Raises:
            ParallelError: If mapping fails
        """
        # Auto-detect task type if needed
        if task_type == 'auto':
            # For now, assume CPU-bound if not specified
            # In real implementation, you might inspect the function
            import inspect
            sig = inspect.signature(func)
            task_type = 'cpu'  # Default assumption

        # Determine best executor strategy
        if task_type == 'cpu':
            if Parallel.supports_interpreter_pool():
                # Use InterpreterPoolExecutor for Python 3.14+
                return Parallel.map_parallel(
                    func=func,
                    items=items,
                    workers=workers,
                    use_interpreters=True
                )
            elif Parallel.is_free_threaded():
                # Use threads in free-threaded mode
                return Parallel.map_parallel(
                    func=func,
                    items=items,
                    workers=workers,
                    use_processes=False
                )
            else:
                # Use processes for traditional GIL-locked Python
                return Parallel.map_parallel(
                    func=func,
                    items=items,
                    workers=workers,
                    use_processes=True
                )
        else:  # I/O-bound
            # Always use threads for I/O-bound tasks
            return Parallel.map_parallel(
                func=func,
                items=items,
                workers=workers,
                use_processes=False
            )

    @staticmethod
    def get_optimal_workers(task_type: str = 'cpu') -> int:
        """Get optimal number of workers based on system and Python version.

        Args:
            task_type: 'cpu' or 'io' - type of workload

        Returns:
            Optimal number of workers
        """
        try:
            cpu_count = Parallel.get_cpu_count()
        except Exception:
            # Handle the exception gracefully and use fallback value
            cpu_count = 1

        if Parallel.is_free_threaded():
            # In free-threaded mode, can use more threads efficiently
            if task_type == 'cpu':
                return cpu_count * 2
            else:
                return min(32, cpu_count * 2)
        elif Parallel.supports_interpreter_pool():
            # For interpreter pools, use CPU count as baseline
            return cpu_count
        else:
            # Traditional GIL mode - be more conservative
            if task_type == 'cpu':
                return min(32, cpu_count)  # Avoid GIL contention with too many processes
            else:
                return min(32, cpu_count * 2)  # More I/O workers allowed

    @staticmethod
    def process_batches(
        func: Callable,
        items: List[Any],
        batch_size: int,
        workers: Optional[int] = None,
        use_processes: bool = False,
        use_interpreters: bool = False
    ) -> List[Any]:
        """Process items in batches in parallel.

        Args:
            func: Function to apply to each batch
            items: Items to process
            batch_size: Size of each batch
            workers: Number of workers
            use_processes: Use processes instead of threads
            use_interpreters: Use interpreters instead of threads/processes (Python 3.14+)

        Returns:
            List of results from each batch

        Raises:
            ParallelError: If batch processing fails
        """
        try:
            # Create batches
            batches = [
                items[i:i + batch_size]
                for i in range(0, len(items), batch_size)
            ]

            # Process batches in parallel
            return Parallel.process_in_parallel(
                func=func,
                items=batches,
                workers=workers,
                use_processes=use_processes,
                use_interpreters=use_interpreters
            )

        except Exception as e:
            raise ParallelError(f"Batch processing failed: {e}") from e

    @staticmethod
    def reduce_parallel(
        map_func: Callable,
        reduce_func: Callable,
        items: List[Any],
        initial: Any = None,
        workers: Optional[int] = None,
        use_processes: bool = False,
        use_interpreters: bool = False
    ) -> Any:
        """Parallel map-reduce operation.

        Args:
            map_func: Function to map over items
            reduce_func: Function to reduce results (takes two args)
            items: Items to process
            initial: Initial value for reduction
            workers: Number of workers
            use_processes: Use processes instead of threads
            use_interpreters: Use interpreters instead of threads/processes (Python 3.14+)

        Returns:
            Final reduced result

        Raises:
            ParallelError: If map-reduce fails
        """
        try:
            # Map phase
            mapped = Parallel.map_parallel(
                func=map_func,
                items=items,
                workers=workers,
                use_processes=use_processes,
                use_interpreters=use_interpreters
            )

            # Reduce phase
            if initial is not None:
                result = initial
                for item in mapped:
                    result = reduce_func(result, item)
            else:
                if not mapped:
                    raise ParallelError("Cannot reduce empty sequence without initial value")
                result = mapped[0]
                for item in mapped[1:]:
                    result = reduce_func(result, item)

            return result

        except Exception as e:
            if isinstance(e, ParallelError):
                raise
            raise ParallelError(f"Map-reduce failed: {e}") from e


class ParallelProgress:
    """Track progress of parallel operations."""

    def __init__(self, total: int):
        """Initialize progress tracker.

        Args:
            total: Total number of items to process
        """
        self.total = total
        self.completed = 0
        self.failed = 0
        self._lock = threading.Lock()

    def increment(self, success: bool = True) -> None:
        """Increment progress counter.

        Args:
            success: Whether the task succeeded
        """
        with self._lock:
            if success:
                self.completed += 1
            else:
                self.failed += 1

    def get_progress(self) -> Tuple[int, int, float]:
        """Get current progress.

        Returns:
            Tuple of (completed, failed, percentage)
        """
        with self._lock:
            total_processed = self.completed + self.failed
            percentage = (total_processed / self.total * 100) if self.total > 0 else 0
            return (self.completed, self.failed, percentage)

    @property
    def is_complete(self) -> bool:
        """Check if all items processed.

        Returns:
            True if complete
        """
        with self._lock:
            return (self.completed + self.failed) >= self.total


def parallel_map(
    func: Callable,
    items: List[Any],
    workers: Optional[int] = None,
    use_processes: bool = False,
    use_interpreters: bool = False
) -> List[Any]:
    """Convenience function for parallel map.

    Args:
        func: Function to map
        items: Items to map over
        workers: Number of workers
        use_processes: Use processes instead of threads
        use_interpreters: Use interpreters instead of threads/processes (Python 3.14+)

    Returns:
        List of results
    """
    return Parallel.map_parallel(func, items, workers, use_processes, use_interpreters)


def parallel_filter(
    predicate: Callable[[Any], bool],
    items: List[Any],
    workers: Optional[int] = None,
    use_processes: bool = False,
    use_interpreters: bool = False
) -> List[Any]:
    """Parallel filter operation.

    Args:
        predicate: Function returning True to keep item
        items: Items to filter
        workers: Number of workers
        use_processes: Use processes instead of threads
        use_interpreters: Use interpreters instead of threads/processes (Python 3.14+)

    Returns:
        Filtered list of items
    """
    # Create pairs of (item, keep_bool)
    def check_item(item):
        """TODO: Document check_item."""
        return (item, predicate(item))

    results = Parallel.map_parallel(check_item, items, workers, use_processes, use_interpreters)

    # Filter based on predicate results
    return [item for item, keep in results if keep]


def parallel_partition(
    predicate: Callable[[Any], bool],
    items: List[Any],
    workers: Optional[int] = None,
    use_processes: bool = False,
    use_interpreters: bool = False
) -> Tuple[List[Any], List[Any]]:
    """Partition items based on predicate in parallel.

    Args:
        predicate: Function returning True for first partition
        items: Items to partition
        workers: Number of workers
        use_processes: Use processes instead of threads
        use_interpreters: Use interpreters instead of threads/processes (Python 3.14+)

    Returns:
        Tuple of (true_items, false_items)
    """
    # Create pairs of (item, predicate_result)
    def check_item(item):
        """TODO: Document check_item."""
        return (item, predicate(item))

    results = Parallel.map_parallel(check_item, items, workers, use_processes, use_interpreters)

    # Partition based on predicate
    true_items = [item for item, result in results if result]
    false_items = [item for item, result in results if not result]

    return (true_items, false_items)


def parallel_starmap(
    func: Callable,
    args_list: List[Tuple],
    workers: Optional[int] = None,
    use_processes: bool = False,
    use_interpreters: bool = False
) -> List[Any]:
    """Parallel starmap operation (func with multiple arguments).

    Args:
        func: Function to apply
        args_list: List of argument tuples
        workers: Number of workers
        use_processes: Use processes instead of threads
        use_interpreters: Use interpreters instead of threads/processes (Python 3.14+)

    Returns:
        List of results

    Example:
        def add(a, b):
            return a + b

        results = parallel_starmap(add, [(1, 2), (3, 4), (5, 6)])
        # Returns [3, 7, 11]
    """
    def wrapper(args):
        """TODO: Document wrapper."""
        return func(*args)

    return Parallel.map_parallel(wrapper, args_list, workers, use_processes, use_interpreters)
