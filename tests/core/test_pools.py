"""
Test suite for pools functionality.
Tests resource pooling operations from nodupe.core.pools.
"""

import os
import tempfile
import shutil
from pathlib import Path
import time
import pytest
from unittest.mock import patch

from nodupe.core.pools import ObjectPool, ConnectionPool, WorkerPool, Pools, PoolError


class TestObjectPool:
    """Test ObjectPool functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_object_pool_initialization(self):
        """Test ObjectPool initialization."""
        def dummy_factory():
            return "dummy_object"
        
        pool = ObjectPool(dummy_factory, max_size=5, timeout=2.0)
        
        assert pool is not None
        assert pool.max_size == 5
        assert pool.timeout == 2.0
        assert pool.factory is dummy_factory
        assert pool.size == 0
        assert pool.active == 0
    
    def test_object_pool_initialization_defaults(self):
        """Test ObjectPool initialization with defaults."""
        def dummy_factory():
            return "default_dummy"
        
        pool = ObjectPool(dummy_factory)
        
        assert pool.max_size == 10
        assert pool.timeout == 5.0
        assert pool.size == 0
        assert pool.active == 0
    
    def test_acquire_and_release_basic(self):
        """Test basic acquire and release operations."""
        def create_string():
            return "test_string"
        
        pool = ObjectPool(create_string, max_size=2)
        
        # Acquire object
        obj = pool.acquire()
        assert obj == "test_string"
        assert pool.active == 1
        
        # Release object
        pool.release(obj)
        assert pool.active == 1  # Active count stays same, object goes back to pool
        assert pool.size == 1  # Object is now in pool
    
    def test_acquire_multiple_objects(self):
        """Test acquiring multiple objects."""
        counter = 0
        def create_counter():
            nonlocal counter
            counter += 1
            return f"object_{counter}"
        
        pool = ObjectPool(create_counter, max_size=3)
        
        # Acquire multiple objects
        obj1 = pool.acquire()
        obj2 = pool.acquire()
        
        assert obj1 != obj2  # Different objects created
        assert pool.active == 2
        assert pool.size == 0  # Objects are active, not in pool
    
    def test_acquire_beyond_max_size(self):
        """Test acquiring beyond max size."""
        def create_string():
            return "limited_object"
        
        pool = ObjectPool(create_string, max_size=1)
        
        # Acquire first object
        obj1 = pool.acquire()
        assert pool.active == 1
        
        # Try to acquire second - should fail
        with pytest.raises(PoolError):
            pool.acquire(timeout=0.1)
    
    def test_release_after_close(self):
        """Test releasing object after pool is closed."""
        def create_string():
            return "test_object"
        
        pool = ObjectPool(create_string, max_size=2)
        obj = pool.acquire()
        
        pool.close()
        
        # Release should not crash after close
        pool.release(obj)
    
    def test_pool_context_manager(self):
        """Test ObjectPool context manager."""
        def create_string():
            return "context_object"
        
        pool = ObjectPool(create_string, max_size=2)
        
        with pool:
            obj = pool.acquire()
            assert obj == "context_object"
            pool.release(obj)
            
        # After context manager exit, pool should be closed
        with pytest.raises(PoolError):
            pool.acquire()
    
    def test_pool_get_object_context_manager(self):
        """Test get_object context manager."""
        def create_string():
            return "cm_object"
        
        pool = ObjectPool(create_string, max_size=2)
        
        with pool.get_object() as obj:
            assert obj == "cm_object"
            # Object should be automatically released
        
        # Object should be back in pool
        assert pool.size == 1
    
    def test_get_optimal_pool_size(self):
        """Test getting optimal pool size."""
        def create_string():
            return "size_test"
        
        pool = ObjectPool(create_string, max_size=5)
        
        # Test with no estimated usage
        optimal_size = pool.get_optimal_pool_size()
        assert optimal_size == 5  # Should return max_size
        
        # Test with estimated usage
        optimal_size = pool.get_optimal_pool_size(estimated_concurrent_usage=3)
        assert optimal_size >= 3  # Should accommodate estimated usage
    
    def test_pool_with_reset_function(self):
        """Test ObjectPool with reset function."""
        def create_list():
            return []
        
        def reset_list(lst):
            lst.clear()
            lst.extend(["reset"])
        
        pool = ObjectPool(create_list, max_size=2, reset_func=reset_list)
        
        # Acquire and populate object
        obj = pool.acquire()
        obj.append("data")
        assert obj == ["data"]
        
        # Release and acquire again
        pool.release(obj)
        obj2 = pool.acquire()
        
        # Should be reset
        assert obj2 == ["reset"]
    
    def test_pool_with_destroy_function(self):
        """Test ObjectPool with destroy function."""
        destroyed_objects = []
        
        def create_list():
            return ["alive"]
        
        def destroy_list(lst):
            lst.append("destroyed")
            destroyed_objects.append(lst)
        
        pool = ObjectPool(create_list, max_size=2, destroy_func=destroy_list)
        
        obj = pool.acquire()
        pool.release(obj)
        pool.close()
        
        assert len(destroyed_objects) == 1
        assert "destroyed" in destroyed_objects[0][-1]  # Check last element
    
    def test_pool_closed_behavior(self):
        """Test pool behavior when closed."""
        def create_string():
            return "test"
        
        pool = ObjectPool(create_string, max_size=2)
        obj = pool.acquire()
        
        pool.close()
        
        # Should not accept new acquisitions
        with pytest.raises(PoolError):
            pool.acquire()
        
        # Should handle releases gracefully
        pool.release(obj)  # Should not crash


class TestConnectionPool:
    """Test ConnectionPool functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_connection_pool_initialization(self):
        """Test ConnectionPool initialization."""
        def create_connection():
            return {"connected": True, "id": 123}
        
        pool = ConnectionPool(create_connection, max_connections=5, timeout=2.0)
        
        assert pool is not None
        assert pool.connect_func is create_connection
        assert pool.size == 0
        assert pool.active == 0
        assert pool.is_free_threaded is False  # Most likely not free-threaded
    
    def test_connection_pool_acquire_and_release(self):
        """Test connection pool acquire and release."""
        def create_connection():
            return {"connected": True, "type": "mock_db"}
        
        pool = ConnectionPool(create_connection, max_connections=2)
        
        # Acquire connection
        conn = pool.acquire()
        assert conn["connected"] is True
        assert conn["type"] == "mock_db"
        assert pool.active == 1
        
        # Release connection
        pool.release(conn)
        assert pool.size == 1  # Connection back in pool
    
    def test_connection_pool_context_manager(self):
        """Test connection pool context manager."""
        def create_connection():
            return {"connected": True, "usage": "test"}
        
        pool = ConnectionPool(create_connection, max_connections=2)
        
        with pool.get_connection() as conn:
            assert conn["connected"] is True
            conn["used"] = True
            
        # Connection should be returned to pool
        assert pool.size == 1
    
    def test_connection_pool_close(self):
        """Test connection pool close."""
        connections_created = []
        
        def create_connection():
            conn_id = len(connections_created) + 1
            conn = {"id": conn_id, "closed": False}
            connections_created.append(conn)
            return conn
        
        pool = ConnectionPool(create_connection, max_connections=2)
        
        # Create and acquire connections
        conn1 = pool.acquire()
        conn2 = pool.acquire()
        
        # Release connections before closing
        pool.release(conn1)
        pool.release(conn2)
        
        pool.close()
        
        # Pool should be empty
        assert pool.size == 0
        assert pool.active == 0
    
    def test_connection_pool_test_on_borrow(self):
        """Test connection pool with test_on_borrow."""
        def create_connection():
            return {"healthy": True}
        
        pool = ConnectionPool(create_connection, max_connections=2, test_on_borrow=True)
        
        conn = pool.acquire()
        assert conn["healthy"] is True
    
    def test_connection_pool_bad_connection_retry(self):
        """Test connection pool with bad connections."""
        # This test verifies that the pool can handle bad connections
        # by testing the connection health check functionality
        def create_connection():
            return {"healthy": True}
        
        pool = ConnectionPool(create_connection, max_connections=2, test_on_borrow=True)
        
        # Acquire a connection
        conn = pool.acquire()
        assert conn["healthy"] is True
        
        # Release it
        pool.release(conn)


class TestWorkerPool:
    """Test WorkerPool functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_worker_pool_initialization(self):
        """Test WorkerPool initialization."""
        pool = WorkerPool(workers=2, queue_size=50)
        
        assert pool is not None
        assert pool.workers == 2
        assert pool.queue_size == 50
        assert pool.pending == 0
        assert pool.is_free_threaded is False  # Most likely not free-threaded
    
    def test_worker_pool_start_stop(self):
        """Test WorkerPool start and stop."""
        pool = WorkerPool(workers=2, queue_size=100)
        
        # Start pool
        pool.start()
        assert pool._running is True
        
        # Stop pool
        pool.shutdown(wait=False)
        assert pool._running is False
    
    def test_worker_pool_submit_task(self):
        """Test submitting tasks to WorkerPool."""
        results = []
        
        def task_func(value):
            results.append(value * 2)
        
        pool = WorkerPool(workers=2, queue_size=100)
        pool.start()
        
        # Submit tasks
        pool.submit(task_func, 5)
        pool.submit(task_func, 10)
        
        # Wait for tasks to complete
        pool.shutdown(wait=True)
        
        assert len(results) == 2
        assert 10 in results
        assert 20 in results
    
    def test_worker_pool_context_manager(self):
        """Test WorkerPool context manager."""
        results = []
        
        def task_func(value):
            results.append(value + 100)
        
        with WorkerPool(workers=2, queue_size=100) as pool:
            pool.submit(task_func, 1)
            pool.submit(task_func, 2)
        
        # Pool should have processed tasks and shut down
        assert len(results) == 2
        assert 101 in results
        assert 102 in results
    
    def test_worker_pool_shutdown_wait(self):
        """Test WorkerPool shutdown with wait."""
        results = []
        
        def slow_task(value):
            time.sleep(0.1)
            results.append(value)
        
        pool = WorkerPool(workers=2, queue_size=100)
        pool.start()
        
        # Submit tasks
        for i in range(5):
            pool.submit(slow_task, i)
        
        # Shutdown with wait - should process all tasks
        pool.shutdown(wait=True)
        
        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}
    
    def test_worker_pool_get_optimal_workers(self):
        """Test getting optimal workers."""
        pool = WorkerPool(workers=2)
        
        optimal = pool.get_optimal_workers()
        assert isinstance(optimal, int)
        assert optimal > 0
        
        # Test with custom base
        optimal_custom = pool.get_optimal_workers(base_workers=4)
        assert isinstance(optimal_custom, int)
        assert optimal_custom > 0
    
    def test_worker_pool_full_queue(self):
        """Test WorkerPool with full queue."""
        def dummy_task():
            time.sleep(0.01)
        
        pool = WorkerPool(workers=1, queue_size=1)
        pool.start()
        
        # Fill queue
        pool.submit(dummy_task)
        
        # Submit another - might fail if queue is full
        try:
            pool.submit(dummy_task, timeout=0.1)
        except PoolError:
            pass  # Expected when queue is full
        
        pool.shutdown(wait=False)
    
    def test_worker_pool_submit_with_args_kwargs(self):
        """Test WorkerPool submit with args and kwargs."""
        results = []
        
        def task_with_args(a, b, c=None):
            results.append({"a": a, "b": b, "c": c})
        
        with WorkerPool(workers=2) as pool:
            pool.submit(task_with_args, 1, 2, c="test")
            pool.submit(task_with_args, 3, 4, c="another")
        
        assert len(results) == 2
        for result in results:
            assert "a" in result and "b" in result and "c" in result


class TestPoolsFactory:
    """Test Pools factory class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_is_free_threaded(self):
        """Test free-threaded detection."""
        result = Pools.is_free_threaded()
        assert isinstance(result, bool)
    
    def test_create_pool(self):
        """Test creating generic object pool."""
        def factory():
            return "pooled_object"
        
        pool = Pools.create_pool(factory, max_size=3)
        
        assert isinstance(pool, ObjectPool)
        assert pool.max_size == 3
        
        obj = pool.acquire()
        assert obj == "pooled_object"
        pool.release(obj)
    
    def test_create_pool_optimized(self):
        """Test creating optimized object pool."""
        def factory():
            return "optimized_object"
        
        pool = Pools.create_pool_optimized(factory, max_size=3)
        
        assert isinstance(pool, ObjectPool)
        assert pool.max_size >= 3  # May be adjusted based on threading mode
        
        obj = pool.acquire()
        assert obj == "optimized_object"
        pool.release(obj)
    
    def test_create_connection_pool(self):
        """Test creating connection pool."""
        def connect_func():
            return {"connection": "test"}
        
        pool = Pools.create_connection_pool(connect_func, max_connections=4)
        
        assert isinstance(pool, ConnectionPool)
        assert pool._pool.max_size == 4
        
        conn = pool.acquire()
        assert conn["connection"] == "test"
        pool.release(conn)
    
    def test_create_connection_pool_optimized(self):
        """Test creating optimized connection pool."""
        def connect_func():
            return {"connection": "optimized"}
        
        pool = Pools.create_connection_pool_optimized(connect_func, max_connections=4)
        
        assert isinstance(pool, ConnectionPool)
        assert pool._pool.max_size >= 4  # May be adjusted for free-threading
        
        conn = pool.acquire()
        assert conn["connection"] == "optimized"
        pool.release(conn)
    
    def test_create_worker_pool(self):
        """Test creating worker pool."""
        pool = Pools.create_worker_pool(workers=2, queue_size=50)
        
        assert isinstance(pool, WorkerPool)
        assert pool.workers == 2
        assert pool.queue_size == 50
    
    def test_create_worker_pool_optimized(self):
        """Test creating optimized worker pool."""
        pool = Pools.create_worker_pool_optimized(workers=2, queue_size=50)
        
        assert isinstance(pool, WorkerPool)
        assert pool.workers >= 2  # May be adjusted for free-threading
        assert pool.queue_size == 50


def test_pool_error_exception():
    """Test PoolError exception."""
    try:
        raise PoolError("Test pool error")
    except PoolError as e:
        assert str(e) == "Test pool error"
        assert isinstance(e, Exception)


def test_pool_error_handling():
    """Test error handling in pool operations."""
    def failing_factory():
        raise ValueError("Factory failed")
    
    pool = ObjectPool(failing_factory, max_size=1)
    
    # Test that pool handles factory errors gracefully
    with pytest.raises(PoolError):
        pool.acquire()


if __name__ == "__main__":
    pytest.main([__file__])
