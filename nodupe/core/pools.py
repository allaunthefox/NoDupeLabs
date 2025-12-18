"""Pools Module.

Resource pooling utilities using standard library only.

Key Features:
    - Thread pool for concurrent tasks
    - Connection pool for database connections
    - Object pool for resource reuse
    - Pool lifecycle management
    - Thread-safe operations
    - Free-threaded Python compatible
    - Standard library only (no external dependencies)

Dependencies:
    - threading (standard library)
    - queue (standard library)
    - contextlib (standard library)
    - sys (for GIL detection)
"""

import threading
import queue
from typing import Any, Callable, Optional, Generic, TypeVar, List
from contextlib import contextmanager
import time
import sys


class PoolError(Exception):
    """Pool operation error"""


T = TypeVar('T')


def _is_free_threaded() -> bool:
    """Check if running in free-threaded mode (Python 3.13+ with --disable-gil).

    Returns:
        True if running in free-threaded mode, False otherwise
    """
    return hasattr(sys, 'flags') and getattr(sys.flags, 'gil', 1) == 0


class ObjectPool(Generic[T]):
    """Generic object pool for resource reuse.

    Maintains a pool of reusable objects with automatic lifecycle management.
    Thread-safe for concurrent access and free-threading compatible.
    """

    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 10,
        timeout: float = 5.0,
        reset_func: Optional[Callable[[T], None]] = None,
        destroy_func: Optional[Callable[[T], None]] = None,
        use_rlock: bool = True  # Use RLock instead of Lock for better free-threaded compatibility
    ):
        """Initialize object pool.

        Args:
            factory: Function to create new objects
            max_size: Maximum pool size
            timeout: Timeout for acquiring objects
            reset_func: Function to reset object before reuse
            destroy_func: Function to destroy object when removing from pool
            use_rlock: Use RLock instead of Lock for recursive locking in free-threaded mode
        """
        self.factory = factory
        self.max_size = max_size
        self.timeout = timeout
        self.reset_func = reset_func
        self.destroy_func = destroy_func

        self._pool = queue.Queue(maxsize=max_size)
        self._active_count = 0
        self._lock = threading.RLock() if use_rlock else threading.Lock()
        self._closed = False
        self._is_free_threaded = _is_free_threaded()

    @property
    def is_free_threaded(self) -> bool:
        """Check if running in free-threaded mode.

        Returns:
            True if running in free-threaded mode, False otherwise
        """
        return self._is_free_threaded

    def get_optimal_pool_size(self, estimated_concurrent_usage: Optional[int] = None) -> int:
        """Get optimal pool size based on Python version and usage patterns.

        Args:
            estimated_concurrent_usage: Expected number of concurrent users

        Returns:
            Optimal pool size
        """
        if estimated_concurrent_usage is not None:
            if self._is_free_threaded:
                # In free-threaded mode, can support more concurrent usage
                return max(self.max_size, estimated_concurrent_usage * 2)
            else:
                # With GIL, be more conservative
                return max(self.max_size, estimated_concurrent_usage)
        else:
            # Use current max_size
            return self.max_size

    def acquire(self, timeout: Optional[float] = None) -> T:
        """Acquire an object from the pool.

        Args:
            timeout: Timeout in seconds (None = use pool default)

        Returns:
            Object from pool

        Raises:
            PoolError: If pool is closed or timeout
        """
        if self._closed:
            raise PoolError("Pool is closed")

        if timeout is None:
            timeout = self.timeout

        try:
            # Try to get existing object from pool
            obj = self._pool.get(timeout=timeout)
            return obj

        except queue.Empty:
            # No objects available, try to create new one
            with self._lock:
                if self._active_count < self.max_size:
                    # Create new object
                    self._active_count += 1
                    try:
                        obj = self.factory()
                        return obj
                    except Exception as e:
                        self._active_count -= 1
                        raise PoolError(f"Failed to create object: {e}") from e

            # Pool is at capacity, wait for object
            raise PoolError(f"Pool exhausted, timeout after {timeout}s")

    def release(self, obj: T) -> None:
        """Release an object back to the pool.

        Args:
            obj: Object to release

        Raises:
            PoolError: If pool is closed
        """
        if self._closed:
            # Destroy object if pool is closed
            if self.destroy_func:
                try:
                    self.destroy_func(obj)
                except Exception:
                    pass
            return

        try:
            # Reset object if reset function provided
            if self.reset_func:
                self.reset_func(obj)

            # Return to pool
            self._pool.put_nowait(obj)

        except queue.Full:
            # Pool is full, destroy the object
            with self._lock:
                self._active_count -= 1
            if self.destroy_func:
                try:
                    self.destroy_func(obj)
                except Exception:
                    pass

    @contextmanager
    def get_object(self, timeout: Optional[float] = None):
        """Context manager for automatic acquire/release.

        Args:
            timeout: Timeout in seconds

        Yields:
            Object from pool

        Example:
            with pool.get_object() as obj:
                # Use obj
                obj.do_something()
            # Automatically released
        """
        obj = self.acquire(timeout)
        try:
            yield obj
        finally:
            self.release(obj)

    def close(self) -> None:
        """Close the pool and destroy all objects."""
        with self._lock:
            if self._closed:
                return
            self._closed = True

        # Destroy all pooled objects
        if self.destroy_func:
            while not self._pool.empty():
                try:
                    obj = self._pool.get_nowait()
                    self.destroy_func(obj)
                except (queue.Empty, Exception):
                    break

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    @property
    def size(self) -> int:
        """Get current pool size.

        Returns:
            Number of objects in pool
        """
        return self._pool.qsize()

    @property
    def active(self) -> int:
        """Get number of active objects.

        Returns:
            Number of objects currently in use
        """
        with self._lock:
            return self._active_count


class ConnectionPool:
    """Database connection pool.

    Specialized pool for managing database connections.
    Free-threading compatible with appropriate locking.
    """

    def __init__(
        self,
        connect_func: Callable[[], Any],
        max_connections: int = 10,
        timeout: float = 5.0,
        test_on_borrow: bool = True
    ):
        """Initialize connection pool.

        Args:
            connect_func: Function to create new connection
            max_connections: Maximum number of connections
            timeout: Timeout for acquiring connection
            test_on_borrow: Test connection health before returning
        """
        self._is_free_threaded = _is_free_threaded()
        self.connect_func = connect_func
        self.test_on_borrow = test_on_borrow

        # Create object pool with connection-specific handlers
        self._pool = ObjectPool(
            factory=connect_func,
            max_size=max_connections,
            timeout=timeout,
            reset_func=None,  # Connections don't need reset
            destroy_func=self._close_connection
        )

    @property
    def is_free_threaded(self) -> bool:
        """Check if running in free-threaded mode.

        Returns:
            True if running in free-threaded mode, False otherwise
        """
        return self._is_free_threaded

    def _close_connection(self, conn: Any) -> None:
        """Close a database connection.

        Args:
            conn: Connection to close
        """
        try:
            if hasattr(conn, 'close'):
                conn.close()
        except Exception:
            pass

    def _test_connection(self, conn: Any) -> bool:
        """Test if connection is still valid.

        Args:
            conn: Connection to test

        Returns:
            True if connection is valid
        """
        try:
            # Try to execute a simple query
            if hasattr(conn, 'execute'):
                conn.execute('SELECT 1')
                return True
            return True
        except Exception:
            return False

    def acquire(self, timeout: Optional[float] = None) -> Any:
        """Acquire a connection from pool.

        Args:
            timeout: Timeout in seconds

        Returns:
            Database connection

        Raises:
            PoolError: If unable to acquire connection
        """
        conn = self._pool.acquire(timeout)

        # Test connection if required
        if self.test_on_borrow:
            if not self._test_connection(conn):
                # Connection is bad, destroy it and try again
                self._close_connection(conn)
                return self.acquire(timeout)

        return conn

    def release(self, conn: Any) -> None:
        """Release connection back to pool.

        Args:
            conn: Connection to release
        """
        self._pool.release(conn)

    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """Context manager for connection.

        Args:
            timeout: Timeout in seconds

        Yields:
            Database connection

        Example:
            with pool.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM users")
            # Connection automatically released
        """
        with self._pool.get_object(timeout) as conn:
            yield conn

    def close(self) -> None:
        """Close all connections in pool."""
        self._pool.close()

    @property
    def size(self) -> int:
        """Get pool size."""
        return self._pool.size

    @property
    def active(self) -> int:
        """Get active connection count."""
        return self._pool.active


class WorkerPool:
    """Worker pool for task execution.

    Maintains a pool of worker threads for executing tasks.
    Free-threading compatible with appropriate locking.
    """

    def __init__(self, workers: int = 4, queue_size: int = 100):
        """Initialize worker pool.

        Args:
            workers: Number of worker threads
            queue_size: Maximum queue size (0 = unlimited)
        """
        self._is_free_threaded = _is_free_threaded()
        self.workers = workers
        self.queue_size = queue_size

        if queue_size > 0:
            self._queue = queue.Queue(maxsize=queue_size)
        else:
            self._queue = queue.Queue()

        self._threads: List[threading.Thread] = []
        self._running = False
        self._lock = threading.RLock() if self._is_free_threaded else threading.Lock()

    @property
    def is_free_threaded(self) -> bool:
        """Check if running in free-threaded mode.

        Returns:
            True if running in free-threaded mode, False otherwise
        """
        return self._is_free_threaded

    def get_optimal_workers(self, base_workers: Optional[int] = None) -> int:
        """Get optimal number of workers based on Python version.

        Args:
            base_workers: Base number of workers (None = use self.workers)

        Returns:
            Optimal number of workers
        """
        if base_workers is None:
            base_workers = self.workers

        if self._is_free_threaded:
            # In free-threaded mode, can use more workers efficiently
            return base_workers * 2
        else:
            # With GIL, be more conservative
            return base_workers

    def start(self) -> None:
        """Start worker threads."""
        with self._lock:
            if self._running:
                return

            self._running = True

            # Get optimal number of workers based on Python version
            optimal_workers = self.get_optimal_workers()

            # Create and start worker threads
            for i in range(optimal_workers):
                thread = threading.Thread(
                    target=self._worker,
                    name=f"Worker-{i}",
                    daemon=True
                )
                thread.start()
                self._threads.append(thread)

    def _worker(self) -> None:
        """Worker thread main loop."""
        while self._running:
            try:
                # Get task from queue (blocking to avoid polling)
                task = self._queue.get()

                if task is None:  # Poison pill
                    break

                # Execute task
                func, args, kwargs = task
                try:
                    func(*args, **kwargs)
                except Exception:
                    # Ignore task errors (could log here)
                    pass
                finally:
                    self._queue.task_done()

            except queue.Empty:
                # This shouldn't happen with blocking get, but handle gracefully
                continue

    def submit(
        self,
        func: Callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> None:
        """Submit a task to the pool.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            timeout: Timeout for queue insertion
            **kwargs: Keyword arguments for func

        Raises:
            PoolError: If pool is not running or queue is full
        """
        if not self._running:
            raise PoolError("Worker pool is not running")

        try:
            task = (func, args, kwargs)
            self._queue.put(task, timeout=timeout)
        except queue.Full:
            raise PoolError("Worker queue is full")

    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """Shutdown worker pool.

        Args:
            wait: Wait for tasks to complete
            timeout: Maximum time to wait in seconds
        """
        with self._lock:
            if not self._running:
                return

            self._running = False

        if wait:
            # Wait for all tasks to complete using queue.join()
            start_time = time.monotonic()
            try:
                self._queue.join()
            except Exception:
                # If join() fails, fall back to polling
                while not self._queue.empty():
                    if timeout and (time.monotonic() - start_time) > timeout:
                        break
                    time.sleep(0.1)

        # Send poison pills to workers - ensure we send exactly one per worker
        for _ in range(len(self._threads)):
            try:
                # Use blocking put with timeout to avoid deadlock
                self._queue.put(None, block=True, timeout=1.0)
            except queue.Full:
                # Queue is full, but this shouldn't happen if we used queue.join()
                pass
            except Exception:
                # If put fails, continue anyway
                pass

        # Wait for threads to finish
        for thread in self._threads:
            if timeout:
                remaining = timeout - (time.monotonic() - start_time)
                thread.join(timeout=max(0, remaining))
            else:
                thread.join()

        self._threads.clear()

    @property
    def pending(self) -> int:
        """Get number of pending tasks.

        Returns:
            Number of tasks in queue
        """
        return self._queue.qsize()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown(wait=True)
        return False


class Pools:
    """Factory class for creating various types of pools."""

    @staticmethod
    def is_free_threaded() -> bool:
        """Check if running in free-threaded mode.

        Returns:
            True if running in free-threaded mode, False otherwise
        """
        return _is_free_threaded()

    @staticmethod
    def create_pool(
        factory: Callable[[], T],
        max_size: int = 10,
        **kwargs
    ) -> ObjectPool[T]:
        """Create a generic object pool.

        Args:
            factory: Function to create objects
            max_size: Maximum pool size
            **kwargs: Additional pool arguments

        Returns:
            ObjectPool instance
        """
        return ObjectPool(factory=factory, max_size=max_size, **kwargs)

    @staticmethod
    def create_pool_optimized(
        factory: Callable[[], T],
        max_size: int = 10,
        **kwargs
    ) -> ObjectPool[T]:
        """Create a generic object pool optimized for current Python version.

        Args:
            factory: Function to create objects
            max_size: Base maximum pool size (will be adjusted for free-threading)
            **kwargs: Additional pool arguments

        Returns:
            ObjectPool instance optimized for current environment
        """
        is_free_threaded = _is_free_threaded()

        # Adjust max_size based on threading mode if not explicitly set
        if 'max_size' not in kwargs and is_free_threaded:
            max_size = max_size * 2  # More capacity in free-threaded mode

        return ObjectPool(factory=factory, max_size=max_size, use_rlock=True, **kwargs)

    @staticmethod
    def create_connection_pool(
        connect_func: Callable[[], Any],
        max_connections: int = 10,
        **kwargs
    ) -> ConnectionPool:
        """Create a connection pool.

        Args:
            connect_func: Function to create connections
            max_connections: Maximum number of connections
            **kwargs: Additional pool arguments

        Returns:
            ConnectionPool instance
        """
        return ConnectionPool(
            connect_func=connect_func,
            max_connections=max_connections,
            **kwargs
        )

    @staticmethod
    def create_connection_pool_optimized(
        connect_func: Callable[[], Any],
        max_connections: int = 10,
        **kwargs
    ) -> ConnectionPool:
        """Create a connection pool optimized for current Python version.

        Args:
            connect_func: Function to create connections
            max_connections: Base maximum connections (will be adjusted for free-threading)
            **kwargs: Additional pool arguments

        Returns:
            ConnectionPool instance optimized for current environment
        """
        if _is_free_threaded():
            # In free-threaded mode, can handle more concurrent connections
            max_connections = max_connections * 2
        return ConnectionPool(
            connect_func=connect_func,
            max_connections=max_connections,
            **kwargs
        )

    @staticmethod
    def create_worker_pool(
        workers: int = 4,
        queue_size: int = 100
    ) -> WorkerPool:
        """Create a worker pool.

        Args:
            workers: Number of worker threads
            queue_size: Maximum queue size

        Returns:
            WorkerPool instance
        """
        return WorkerPool(workers=workers, queue_size=queue_size)

    @staticmethod
    def create_worker_pool_optimized(
        workers: int = 4,
        queue_size: int = 100
    ) -> WorkerPool:
        """Create a worker pool optimized for current Python version.

        Args:
            workers: Base number of worker threads (will be adjusted for free-threading)
            queue_size: Maximum queue size

        Returns:
            WorkerPool instance optimized for current environment
        """
        if _is_free_threaded():
            # In free-threaded mode, can use more workers efficiently
            workers = workers * 2
        return WorkerPool(workers=workers, queue_size=queue_size)
