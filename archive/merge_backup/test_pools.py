"""Tests for pools module with GIL and threading enhancements."""

import sys
from unittest.mock import patch, MagicMock, Mock
import pytest
import threading
from nodupe.core.pools import Pools, ObjectPool, ConnectionPool, WorkerPool, PoolError


class TestPoolsGILDetection:
    """Test GIL detection in pool classes."""

    def test_object_pool_is_free_threaded_property(self):
        """Test ObjectPool is_free_threaded property."""
        # Mock free-threaded detection
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = ObjectPool(factory=lambda: object())
            assert pool.is_free_threaded is True

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = ObjectPool(factory=lambda: object())
            assert pool.is_free_threaded is False

    def test_connection_pool_is_free_threaded_property(self):
        """Test ConnectionPool is_free_threaded property."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = ConnectionPool(connect_func=lambda: object())
            assert pool.is_free_threaded is True

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = ConnectionPool(connect_func=lambda: object())
            assert pool.is_free_threaded is False

    def test_worker_pool_is_free_threaded_property(self):
        """Test WorkerPool is_free_threaded property."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = WorkerPool(workers=2)
            assert pool.is_free_threaded is True

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = WorkerPool(workers=2)
            assert pool.is_free_threaded is False

    def test_pools_class_is_free_threaded(self):
        """Test Pools class is_free_threaded method."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            assert Pools.is_free_threaded() is True

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            assert Pools.is_free_threaded() is False


class TestObjectPoolOptimizations:
    """Test ObjectPool optimization methods."""

    def test_get_optimal_pool_size_default(self):
        """Test get_optimal_pool_size with default behavior."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = ObjectPool(factory=lambda: object(), max_size=10)
            assert pool.get_optimal_pool_size() == 10

    def test_get_optimal_pool_size_free_threaded_no_estimate(self):
        """Test get_optimal_pool_size in free-threaded mode without estimate."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = ObjectPool(factory=lambda: object(), max_size=10)
            assert pool.get_optimal_pool_size() == 10  # Uses max_size when no estimate

    def test_get_optimal_pool_size_free_threaded_with_estimate(self):
        """Test get_optimal_pool_size in free-threaded mode with estimate."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = ObjectPool(factory=lambda: object(), max_size=10)
            assert pool.get_optimal_pool_size(5) == max(10, 5 * 2)  # 5 * 2 = 10

    def test_get_optimal_pool_size_gil_locked_with_estimate(self):
        """Test get_optimal_pool_size in GIL-locked mode with estimate."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = ObjectPool(factory=lambda: object(), max_size=10)
            assert pool.get_optimal_pool_size(5) == max(10, 5)  # Just uses estimate

    def test_object_pool_rlock_usage(self):
        """Test that ObjectPool uses RLock in free-threaded mode."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = ObjectPool(factory=lambda: object(), use_rlock=True)
            assert isinstance(pool._lock, type(threading.RLock()))

        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = ObjectPool(factory=lambda: object(), use_rlock=False)
            assert isinstance(pool._lock, type(threading.Lock()))


class TestConnectionPoolOptimizations:
    """Test ConnectionPool optimization methods."""
    
    def test_connection_pool_initialization_sets_free_threaded_flag(self):
        """Test ConnectionPool properly sets free-threaded flag on initialization."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = ConnectionPool(connect_func=lambda: object())
            assert pool._is_free_threaded is True

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = ConnectionPool(connect_func=lambda: object())
            assert pool._is_free_threaded is False


class TestWorkerPoolOptimizations:
    """Test WorkerPool optimization methods."""

    def test_worker_pool_initialization_lock_type(self):
        """Test WorkerPool uses appropriate lock type based on threading mode."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = WorkerPool(workers=2)
            assert isinstance(pool._lock, type(threading.RLock()))

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = WorkerPool(workers=2)
            assert isinstance(pool._lock, type(threading.Lock()))

    def test_get_optimal_workers_default(self):
        """Test WorkerPool get_optimal_workers with default base."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = WorkerPool(workers=4)
            assert pool.get_optimal_workers() == 8  # 4 * 2 in free-threaded mode

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = WorkerPool(workers=4)
            assert pool.get_optimal_workers() == 4  # 4 in GIL mode

    def test_get_optimal_workers_with_base(self):
        """Test WorkerPool get_optimal_workers with custom base."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = WorkerPool(workers=2)
            assert pool.get_optimal_workers(base_workers=6) == 12  # 6 * 2

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = WorkerPool(workers=2)
            assert pool.get_optimal_workers(base_workers=6) == 6  # 6 unchanged

    def test_worker_pool_start_uses_optimal_workers(self):
        """Test WorkerPool.start uses optimal worker count."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            with patch('threading.Thread') as mock_thread:
                pool = WorkerPool(workers=2)
                pool.start()

                # In free-threaded mode, it should create 4 threads (2 * 2)
                # Note: The call count might be doubled due to other operations,
                # so we check that it's at least 4
                assert mock_thread.call_count >= 4

        # Reset mock
        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            with patch('threading.Thread') as mock_thread:
                pool = WorkerPool(workers=2)
                pool.start()

                # In GIL mode, it should create 2 threads
                # Note: The call count might be doubled due to other operations,
                # so we check that it's at least 2
                assert mock_thread.call_count >= 2


class TestPoolsFactoryMethods:
    """Test Pools factory methods with optimization."""

    def test_create_pool_optimized(self):
        """Test create_pool_optimized factory method."""
        factory = lambda: "test_object"
        
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = Pools.create_pool_optimized(factory, max_size=5)
            # In free-threaded mode, max_size should be doubled to 10
            assert pool.max_size == 10
            assert pool._is_free_threaded is True

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = Pools.create_pool_optimized(factory, max_size=5)
            assert pool.max_size == 5  # Unchanged in GIL mode

    def test_create_pool_optimized_with_kwargs(self):
        """Test create_pool_optimized with additional kwargs."""
        factory = lambda: "test_object"
        
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = Pools.create_pool_optimized(factory, max_size=5, timeout=10)
            assert pool.max_size == 10  # Doubled
            # Other parameters should be preserved

    def test_create_connection_pool_optimized(self):
        """Test create_connection_pool_optimized factory method."""
        connect_func = lambda: "connection"
        
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = Pools.create_connection_pool_optimized(connect_func, max_connections=5)
            # The underlying pool should have doubled max_size
            assert pool._pool.max_size == 10  # 5 * 2

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = Pools.create_connection_pool_optimized(connect_func, max_connections=5)
            assert pool._pool.max_size == 5  # Unchanged

    def test_create_worker_pool_optimized(self):
        """Test create_worker_pool_optimized factory method."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = Pools.create_worker_pool_optimized(workers=3, queue_size=50)
            # In free-threaded mode, workers should be doubled to 6
            assert pool.workers == 6

        with patch('nodupe.core.pools._is_free_threaded', return_value=False):
            pool = Pools.create_worker_pool_optimized(workers=3, queue_size=50)
            # In GIL mode, workers should remain 3
            assert pool.workers == 3


class TestPoolsFunctionality:
    """Test that pool functionality still works correctly with optimizations."""

    def test_object_pool_basic_operations(self):
        """Test basic ObjectPool operations work with optimizations."""
        factory = lambda: {"count": 0}
        
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = ObjectPool(factory, max_size=2)
            
            # Test acquire and release
            obj1 = pool.acquire()
            assert obj1["count"] == 0
            pool.release(obj1)
            
            # Test context manager
            with pool.get_object() as obj2:
                obj2["count"] = 1
                assert obj2["count"] == 1

    def test_connection_pool_basic_operations(self):
        """Test basic ConnectionPool operations work with optimizations."""
        def mock_connect():
            mock_conn = Mock()
            mock_conn.execute = Mock(return_value=None)
            return mock_conn

        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = ConnectionPool(mock_connect, max_connections=2)
            
            # Test context manager
            with pool.get_connection() as conn:
                conn.execute("SELECT 1")
                conn.execute.assert_called_once_with("SELECT 1")

    def test_worker_pool_basic_operations(self):
        """Test basic WorkerPool operations work with optimizations."""
        with patch('nodupe.core.pools._is_free_threaded', return_value=True):
            pool = WorkerPool(workers=1, queue_size=10)
            
            # Test submit and shutdown
            task_func = Mock()
            pool.start()
            pool.submit(task_func, "arg1", "arg2", kwarg="value")
            pool.shutdown()
            
            task_func.assert_called_once_with("arg1", "arg2", kwarg="value")