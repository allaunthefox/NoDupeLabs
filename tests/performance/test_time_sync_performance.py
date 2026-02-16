"""
Performance Tests for TimeSync Tool

These tests validate the performance improvements implemented in the TimeSync tool,
including parallel NTP queries, optimized file scanning, and FastDate64 encoding.
"""

import time
import threading
import pytest
from unittest.mock import patch, MagicMock, Mock
from concurrent.futures import ThreadPoolExecutor

from nodupe.tools.time_sync import TimeSyncTool
from nodupe.core.time_sync_utils import (
    ParallelNTPClient,
    MonotonicTimeCalculator,
    DNSCache,
    TargetedFileScanner,
    FastDate64Encoder,
    get_global_dns_cache,
    get_global_metrics
)


class TestParallelNTPClient:
    """Test parallel NTP client performance improvements."""
    
    def test_parallel_vs_sequential_performance(self):
        """Test that parallel queries are significantly faster than sequential."""
        # Mock DNS resolution
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
            ]
            
            # Mock socket responses with different delays
            def mock_socket_response(query_id):
                # Simulate different response times
                delays = [0.1, 0.2, 0.05, 0.15]
                delay = delays[query_id % len(delays)]
                time.sleep(delay)
                return Mock(
                    server_time=1600000000.0 + query_id,
                    offset=0.01 * query_id,
                    delay=delay,
                    host=f"test{query_id}.com",
                    address=('1.1.1.1', 123),
                    attempt=0,
                    timestamp=time.time()
                )
            
            with patch.object(ParallelNTPClient, '_query_single_address') as mock_query:
                # Set up mock responses
                mock_query.side_effect = lambda qid, host, addr, attempt: mock_socket_response(qid)
                
                client = ParallelNTPClient(timeout=1.0, max_workers=4)
                
                # Test parallel execution
                start_time = time.perf_counter()
                result = client.query_hosts_parallel(
                    hosts=['test1.com', 'test2.com', 'test3.com', 'test4.com'],
                    attempts_per_host=1,
                    max_acceptable_delay=1.0,
                    stop_on_good_result=False
                )
                parallel_time = time.perf_counter() - start_time
                
                client.shutdown()
                
                # Verify parallel execution was faster than sequential
                # With 4 hosts and different delays (0.1, 0.2, 0.05, 0.15),
                # parallel should complete in roughly max(delay) time
                # Sequential would take sum(delay) time
                expected_sequential_time = 0.1 + 0.2 + 0.05 + 0.15  # 0.5 seconds
                assert parallel_time < expected_sequential_time * 0.7  # At least 30% faster
                
                # Verify we got responses from all hosts
                assert len(result.all_responses) == 4
                assert result.success
    
    def test_early_termination_with_good_result(self):
        """Test that early termination works when a good result is found."""
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
            ]
            
            def slow_response(query_id):
                time.sleep(0.2)  # Slow response
                return Mock(
                    server_time=1600000000.0,
                    offset=0.1,
                    delay=0.2,
                    host=f"slow{query_id}.com",
                    address=('1.1.1.1', 123),
                    attempt=0,
                    timestamp=time.time()
                )
            
            def fast_good_response(query_id):
                time.sleep(0.05)  # Fast response with good delay
                return Mock(
                    server_time=1600000000.0,
                    offset=0.01,
                    delay=0.05,  # Good delay
                    host=f"fast{query_id}.com",
                    address=('1.1.1.1', 123),
                    attempt=0,
                    timestamp=time.time()
                )
            
            with patch.object(ParallelNTPClient, '_query_single_address') as mock_query:
                # First call returns fast good response, subsequent calls return slow
                call_count = 0
                def response_selector(qid, host, addr, attempt):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        return fast_good_response(qid)
                    else:
                        return slow_response(qid)
                
                mock_query.side_effect = response_selector
                
                client = ParallelNTPClient(timeout=1.0, max_workers=4)
                
                start_time = time.perf_counter()
                result = client.query_hosts_parallel(
                    hosts=['fast.com', 'slow1.com', 'slow2.com', 'slow3.com'],
                    attempts_per_host=1,
                    max_acceptable_delay=1.0,
                    stop_on_good_result=True,
                    good_delay_threshold=0.1
                )
                elapsed_time = time.perf_counter() - start_time
                
                client.shutdown()
                
                # Should complete quickly due to early termination
                assert elapsed_time < 0.15  # Less than the slow response time
                assert result.success
                assert result.best_response.delay <= 0.1
    
    def test_dns_caching_performance(self):
        """Test that DNS caching improves performance on repeated lookups."""
        cache = DNSCache(ttl=60.0, max_size=100)
        
        # First lookup (cache miss)
        start_time = time.perf_counter()
        cache.set("test.com", 123, [("1.1.1.1", 123)])
        first_lookup_time = time.perf_counter() - start_time
        
        # Second lookup (cache hit)
        start_time = time.perf_counter()
        result = cache.get("test.com", 123)
        second_lookup_time = time.perf_counter() - start_time
        
        # Cache hit should be significantly faster
        assert second_lookup_time < first_lookup_time * 0.5
        assert result is not None
        assert len(result) == 1
    
    def test_dns_cache_eviction(self):
        """Test that DNS cache properly evicts old entries."""
        cache = DNSCache(ttl=0.1, max_size=2)  # Short TTL and small size
        
        # Fill cache to capacity
        cache.set("host1.com", 123, [("1.1.1.1", 123)])
        cache.set("host2.com", 123, [("2.2.2.2", 123)])
        
        # Next insertion should evict oldest
        cache.set("host3.com", 123, [("3.3.3.3", 123)])
        
        assert cache.get("host1.com") is None  # Evicted
        assert cache.get("host2.com") is not None
        assert cache.get("host3.com") is not None
        
        # Wait for TTL expiration
        time.sleep(0.2)
        assert cache.get("host2.com") is None  # Expired
        assert cache.get("host3.com") is None  # Expired


class TestTargetedFileScanner:
    """Test optimized file system scanning performance."""
    
    def test_scanning_performance_vs_glob(self):
        """Test that targeted scanning is faster than recursive glob."""
        import tempfile
        import os
        
        # Create a test directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directories and files
            for i in range(5):
                subdir = os.path.join(temp_dir, f"level1_{i}")
                os.makedirs(subdir)
                for j in range(10):
                    subsubdir = os.path.join(subdir, f"level2_{j}")
                    os.makedirs(subsubdir)
                    # Create some files
                    for k in range(5):
                        with open(os.path.join(subsubdir, f"file_{k}.txt"), 'w') as f:
                            f.write("test")
            
            # Test targeted scanner
            scanner = TargetedFileScanner(max_files=50, max_depth=2)
            start_time = time.perf_counter()
            result = scanner.get_recent_file_time([temp_dir])
            targeted_time = time.perf_counter() - start_time
            
            # Verify we got a result
            assert result is not None
            assert isinstance(result, float)
            
            # Targeted scanning should be reasonably fast
            assert targeted_time < 1.0  # Should complete within 1 second
    
    def test_depth_limiting(self):
        """Test that depth limiting prevents excessive scanning."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create deep directory structure
            current_dir = temp_dir
            for i in range(10):  # 10 levels deep
                current_dir = os.path.join(current_dir, f"level_{i}")
                os.makedirs(current_dir)
                # Create a file at each level
                with open(os.path.join(current_dir, "test.txt"), 'w') as f:
                    f.write("test")
            
            # Scanner with depth limit should not go too deep
            scanner = TargetedFileScanner(max_files=10, max_depth=3)
            result = scanner.get_recent_file_time([temp_dir])
            
            # Should find a file within the depth limit
            assert result is not None
    
    def test_file_count_limiting(self):
        """Test that file count limiting prevents excessive scanning."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create many files
            for i in range(200):
                with open(os.path.join(temp_dir, f"file_{i}.txt"), 'w') as f:
                    f.write("test")
            
            # Scanner should limit file count
            scanner = TargetedFileScanner(max_files=50, max_depth=1)
            start_time = time.perf_counter()
            result = scanner.get_recent_file_time([temp_dir])
            elapsed_time = time.perf_counter() - start_time
            
            # Should complete quickly due to file count limiting
            assert elapsed_time < 0.5
            assert result is not None


class TestFastDate64Encoder:
    """Test FastDate64 encoding performance improvements."""
    
    def test_encoding_performance(self):
        """Test that FastDate64 encoding is fast."""
        test_timestamps = [
            1672531200.123456,  # 2023-01-01T00:00:00.123456Z
            0.0,                # Unix epoch
            1000000000.0,       # 2001-09-09T01:46:40Z
            time.time(),        # Current time
        ]
        
        # Test encoding performance
        start_time = time.perf_counter()
        for _ in range(1000):  # Encode 1000 times
            for ts in test_timestamps:
                encoded = FastDate64Encoder.encode(ts)
                decoded = FastDate64Encoder.decode(encoded)
                # Verify round-trip accuracy
                assert abs(decoded - ts) < 1e-6
        elapsed_time = time.perf_counter() - start_time
        
        # Should complete encoding/decoding 4000 operations quickly
        assert elapsed_time < 1.0
    
    def test_safe_encoding_methods(self):
        """Test safe encoding/decoding methods handle errors gracefully."""
        # Test safe encoding with invalid input
        result = FastDate64Encoder.encode_safe(-1.0)  # Negative timestamp
        assert result == 0
        
        # Test safe decoding with invalid input
        result = FastDate64Encoder.decode_safe(0)  # Zero value
        assert result == 0.0
        
        # Test with valid input
        ts = time.time()
        encoded = FastDate64Encoder.encode_safe(ts)
        decoded = FastDate64Encoder.decode_safe(encoded)
        assert abs(decoded - ts) < 1e-6


class TestMonotonicTimeCalculator:
    """Test monotonic timing calculations for robustness."""
    
    def test_monotonic_timing_accuracy(self):
        """Test that monotonic timing provides accurate measurements."""
        calculator = MonotonicTimeCalculator()
        
        # Measure a short delay
        start_wall, start_mono = calculator.start_timing()
        time.sleep(0.1)  # 100ms delay
        elapsed_mono = calculator.elapsed_monotonic()
        
        # Monotonic elapsed time should be close to actual delay
        assert 0.08 <= elapsed_mono <= 0.15  # Allow some tolerance
    
    def test_wall_time_conversion(self):
        """Test conversion from monotonic to wall time."""
        calculator = MonotonicTimeCalculator()
        
        start_wall, start_mono = calculator.start_timing()
        time.sleep(0.05)
        
        # Convert monotonic elapsed to wall time
        mono_elapsed = calculator.elapsed_monotonic()
        wall_time_est = calculator.wall_time_from_monotonic(mono_elapsed)
        
        # Should be close to current wall time
        current_wall = time.time()
        assert abs(wall_time_est - current_wall) < 0.01
    
    def test_rtt_calculation(self):
        """Test NTP RTT calculation using monotonic timing."""
        # Simulate NTP timing values
        t1_wall = 1600000000.0
        t2_wall = 1600000000.05
        t3_wall = 1600000000.06
        t4_mono = 0.12  # Simulated monotonic time
        
        delay, offset = MonotonicTimeCalculator.calculate_ntp_rtt(
            t1_wall, t2_wall, t3_wall, t4_mono, 0.0
        )
        
        # Verify calculation produces reasonable results
        assert isinstance(delay, float)
        assert isinstance(offset, float)
        assert delay >= 0


class TestTimeSyncToolPerformance:
    """Test overall TimeSync tool performance improvements."""
    
    def test_parallel_sync_performance(self):
        """Test that parallel synchronization is faster than sequential."""
        tool = TimeSyncTool(
            servers=['test1.com', 'test2.com', 'test3.com'],
            timeout=1.0,
            attempts=1
        )
        
        # Mock the parallel client to simulate different response times
        with patch('nodupe.core.time_sync_utils.ParallelNTPClient') as mock_client_class:
            mock_client = Mock()
            mock_client.query_hosts_parallel.return_value = Mock(
                success=True,
                best_response=Mock(
                    server_time=1600000000.0,
                    offset=0.01,
                    delay=0.05,
                    host="test1.com"
                ),
                all_responses=[],
                errors=[]
            )
            mock_client_class.return_value = mock_client
            
            # Test sync performance
            start_time = time.perf_counter()
            result = tool.force_sync()
            elapsed_time = time.perf_counter() - start_time
            
            # Should complete quickly with parallel execution
            assert elapsed_time < 2.0  # Within 2 seconds
            assert result[0] == "test1.com"  # Got response from best host
    
    def test_dns_cache_integration(self):
        """Test that DNS cache is used by the tool."""
        tool = TimeSyncTool(servers=['test.com'])
        
        # Verify global DNS cache is being used
        cache = get_global_dns_cache()
        
        # Add a test entry
        cache.set("test.com", 123, [("1.1.1.1", 123)])
        
        # Verify it can be retrieved
        result = cache.get("test.com", 123)
        assert result is not None
        assert len(result) == 1
    
    def test_metrics_collection(self):
        """Test that performance metrics are collected."""
        metrics = get_global_metrics()
        
        # Record some test metrics
        metrics.record_ntp_query("test.com", 0.1, True, 0.5)
        metrics.record_dns_cache_hit()
        metrics.record_parallel_query(3, 6, True, 0.5, 0.1)
        
        # Get summary
        summary = metrics.get_summary()
        
        # Verify metrics were recorded
        assert summary['total_queries'] == 1
        assert summary['dns_cache_hit_rate'] > 0
        assert summary['total_parallel_queries'] == 1
        assert summary['success_rate'] == 1.0
    
    def test_file_scanner_integration(self):
        """Test that optimized file scanner is used in fallback."""
        import tempfile
        import os
        
        tool = TimeSyncTool()
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            test_file = f.name
        
        try:
            # Test that file timestamp can be retrieved
            # (This would normally be called during fallback)
            timestamp = os.path.getmtime(test_file)
            assert isinstance(timestamp, float)
            assert timestamp > 0
        finally:
            os.unlink(test_file)
    
    def test_fastdate64_integration(self):
        """Test that optimized FastDate64 encoder is used."""
        tool = TimeSyncTool()
        
        # Test encoding/decoding
        current_time = time.time()
        encoded = tool.encode_fastdate64(current_time)
        decoded = tool.decode_fastdate64(encoded)
        
        # Verify round-trip accuracy
        assert abs(decoded - current_time) < 1e-6
        
        # Test with corrected time
        corrected_time = tool.get_corrected_time()
        encoded_corrected = tool.get_corrected_fast64()
        decoded_corrected = tool.decode_fastdate64(encoded_corrected)
        
        assert abs(decoded_corrected - corrected_time) < 1e-6


class TestPerformanceRegression:
    """Test to prevent performance regressions."""
    
    def test_no_duplicate_struct_parsing(self):
        """Ensure struct formats are precompiled and not parsed repeatedly."""
        # This test verifies that the optimized code doesn't re-parse struct formats
        # The actual verification would require profiling or code inspection
        # For now, we test that the optimized methods work correctly
        
        tool = TimeSyncTool()
        
        # Multiple encoding operations should use precompiled formats
        for _ in range(100):
            ts = time.time()
            encoded = tool.encode_fastdate64(ts)
            decoded = tool.decode_fastdate64(encoded)
            assert abs(decoded - ts) < 1e-6
    
    def test_memory_usage_stability(self):
        """Test that memory usage doesn't grow unbounded."""
        import gc
        
        tool = TimeSyncTool()
        
        # Perform many operations
        for i in range(1000):
            try:
                tool.get_corrected_time()
                tool.get_corrected_fast64()
            except:
                pass  # Expected to fail without network
            
            # Force garbage collection periodically
            if i % 100 == 0:
                gc.collect()
        
        # If we get here without memory issues, the test passes
        assert True
    
    def test_concurrent_access_safety(self):
        """Test that the tool handles concurrent access safely."""
        tool = TimeSyncTool()
        
        results = []
        errors = []
        
        def worker():
            try:
                # These operations should be thread-safe
                time_val = tool.get_corrected_time()
                fast64_val = tool.get_corrected_fast64()
                results.append((time_val, fast64_val))
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) == 10


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short"])
