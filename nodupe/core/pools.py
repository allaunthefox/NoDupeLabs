"""Pools Module.

Resource pooling utilities using standard library only.

Key Features:
    - Thread pool for concurrent tasks
    - Connection pool for database connections
    - Object pool for resource reuse
    - Pool lifecycle management
    - Thread-safe operations
    - Standard library only (no external dependencies)

Dependencies:
    - threading (standard library)
    - queue (standard library)
    - contextlib (standard library)
"""

import threading
import queue
from typing import Any, Callable, Optional, Generic, TypeVar, List
from contextlib import contextmanager
import time


class PoolError(Exception):
    """Pool operation error"""


T = TypeVar('T')


class ObjectPool(Generic[T]):
    """Generic object pool for resource reuse.

    Maintains a pool of reusable objects with automatic lifecycle management.
    Thread-safe for concurrent access.
    """

    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 10,
        timeout: float = 5.0,
        reset_func: Optional[Callable[[T], None]] = None,
        destroy_func: Optional[Callable[[T], None]] = None
    ):
        """Initialize object pool.

        Args:
            factory: Function to create new objects
            max_size: Maximum pool size
            timeout: Timeout for acquiring objects
            reset_func: Function to reset object before reuse
            destroy_func: Function to destroy object when removing from pool
        """
        self.factory = factory
        self.max_size = max_size
        self.timeout = timeout
        self.reset_func = reset_func
        self.destroy_func = destroy_func

        self._pool = queue.Queue(maxsize=max_size)
        self._active_count = 0
        self._lock = threading.Lock()
        self._closed = False

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
    """

    def __init__(self, workers: int = 4, queue_size: int = 100):
        """Initialize worker pool.

        Args:
            workers: Number of worker threads
            queue_size: Maximum queue size (0 = unlimited)
        """
        self.workers = workers
        self.queue_size = queue_size

        if queue_size > 0:
            self._queue = queue.Queue(maxsize=queue_size)
        else:
            self._queue = queue.Queue()

        self._threads: List[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start worker threads."""
        with self._lock:
            if self._running:
                return

            self._running = True

            # Create and start worker threads
            for i in range(self.workers):
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
                # Get task from queue (with timeout to check _running)
                task = self._queue.get(timeout=0.1)

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
            # Wait for queue to empty
            start_time = time.time()
            while not self._queue.empty():
                if timeout and (time.time() - start_time) > timeout:
                    break
                time.sleep(0.1)

        # Send poison pills to workers
        for _ in range(len(self._threads)):
            try:
                self._queue.put(None, block=False)
            except queue.Full:
                pass

        # Wait for threads to finish
        for thread in self._threads:
            if timeout:
                remaining = timeout - (time.time() - start_time)
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
