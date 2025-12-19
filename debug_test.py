#!/usr/bin/env python3
"""Debug script for the failing test."""

import os
import sys
import time
from unittest.mock import patch, Mock

# Set environment variables to ensure plugin is enabled
os.environ['NODUPE_TIMESYNC_ENABLED'] = '1'
os.environ['NODUPE_TIMESYNC_NO_NETWORK'] = '0'

# Now import after setting environment variables
from nodupe.plugins.time_sync import TimeSyncPlugin

def test_mock():
    """Test the mock setup."""
    plugin = TimeSyncPlugin(
        servers=['test1.com', 'test2.com', 'test3.com'],
        timeout=1.0,
        attempts=1
    )
    
    print(f"Plugin enabled: {plugin.is_enabled()}")
    print(f"Network allowed: {plugin.is_network_allowed()}")
    
    # Mock the ParallelNTPClient used inside force_sync
    with patch('nodupe.plugins.time_sync.time_sync.ParallelNTPClient') as mock_client_class:
        print(f"Mock client class: {mock_client_class}")
        
        # Create a proper mock response
        mock_response = Mock()
        mock_response.success = True
        mock_response.best_response = Mock()
        mock_response.best_response.server_time = 1600000000.0
        mock_response.best_response.offset = 0.01
        mock_response.best_response.delay = 0.05
        mock_response.best_response.host = "test1.com"
        mock_response.all_responses = []
        mock_response.errors = []
        
        # Configure the mock client
        mock_client = Mock()
        mock_client.query_hosts_parallel.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        print(f"Mock client: {mock_client}")
        print(f"Mock client.query_hosts_parallel: {mock_client.query_hosts_parallel}")
        
        # Test sync performance
        start_time = time.perf_counter()
        try:
            result = plugin.force_sync()
            elapsed_time = time.perf_counter() - start_time
            print(f"Success! Result: {result}, elapsed time: {elapsed_time:.3f}s")
            return True
        except Exception as e:
            elapsed_time = time.perf_counter() - start_time
            print(f"Failed with error: {e}, elapsed time: {elapsed_time:.3f}s")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_mock()
    sys.exit(0 if success else 1)
