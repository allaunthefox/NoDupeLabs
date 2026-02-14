#!/usr/bin/env python3
"""
Unit tests for CoreLoader class in nodupe.core.loader

Tests are aligned with the current CoreLoader API which provides:
- __init__: Initialize loader state
- initialize: Core system initialization 
- shutdown: Core system shutdown
- _apply_platform_autoconfig: Platform-specific configuration
- _detect_system_resources: System resource detection
- _configure_based_on_resources: Resource-based configuration
- _detect_thread_restrictions: Thread restriction detection
"""

import os
from typing import Dict, Any
from unittest.mock import MagicMock, patch
import pytest

from nodupe.core.loader import CoreLoader, bootstrap

# Type alias for system info dictionary
SystemInfo = Dict[str, Any]


class TestCoreLoaderInit:
    """Test CoreLoader initialization."""

    def test_init_attributes(self):
        """Test that CoreLoader initializes with correct default attributes."""
        loader = CoreLoader()
        
        assert loader.config is None
        assert loader.container is None
        assert loader.plugin_registry is None
        assert loader.plugin_loader is None
        assert loader.plugin_discovery is None
        assert loader.plugin_lifecycle is None
        assert loader.hot_reload is None
        assert loader.database is None
        assert loader.initialized is False


class TestPlatformAutoconfig:
    """Test platform-specific autoconfiguration."""

    @patch('platform.system', return_value='Windows')
    @patch('platform.machine', return_value='x86_64')
    @patch('multiprocessing.cpu_count', return_value=4)
    @patch('os.cpu_count', return_value=8)
    @patch('psutil.virtual_memory', return_value=MagicMock(total=16 * 1024**3))
    @patch('psutil.disk_partitions', return_value=[])
    def test_apply_platform_autoconfig_windows(
        self, mock_partitions: MagicMock, mock_memory: MagicMock,
        mock_cpu_count: MagicMock, mock_os_cpu_count: MagicMock,
        mock_machine: MagicMock, mock_system: MagicMock
    ):
        """Test platform-specific autoconfiguration for Windows."""
        loader = CoreLoader()
        config = loader._apply_platform_autoconfig()

        # Use os.path.join for cross-platform path comparison
        expected_path = os.path.join('output', 'index.db')
        assert config['db_path'] == expected_path
        assert config['use_symlinks'] is False
        assert 'plugins' in config

    @patch('platform.system', return_value='Linux')
    @patch('platform.machine', return_value='x86_64')
    @patch('multiprocessing.cpu_count', return_value=4)
    @patch('os.cpu_count', return_value=8)
    @patch('psutil.virtual_memory', return_value=MagicMock(total=16 * 1024**3))
    @patch('psutil.disk_partitions', return_value=[])
    def test_apply_platform_autoconfig_linux(
        self, mock_partitions: MagicMock, mock_memory: MagicMock,
        mock_cpu_count: MagicMock, mock_os_cpu_count: MagicMock,
        mock_machine: MagicMock, mock_system: MagicMock
    ):
        """Test platform-specific autoconfiguration for Linux."""
        loader = CoreLoader()
        config = loader._apply_platform_autoconfig()

        assert config['db_path'] == 'output/index.db'
        assert config['use_symlinks'] is True
        assert 'plugins' in config


class TestSystemResourceDetection:
    """Test system resource detection."""

    @patch('platform.system', return_value='Linux')
    @patch('platform.machine', return_value='x86_64')
    @patch('multiprocessing.cpu_count', return_value=1)
    @patch('os.cpu_count', return_value=1)
    @patch('psutil.virtual_memory', return_value=MagicMock(total=1 * 1024**3))
    @patch('psutil.disk_partitions', return_value=[])
    def test_detect_system_resources_low_end(
        self, mock_partitions: MagicMock, mock_memory: MagicMock,
        mock_cpu_count: MagicMock, mock_os_cpu_count: MagicMock,
        mock_machine: MagicMock, mock_system: MagicMock
    ):
        """Test system resource detection for low-end system."""
        loader = CoreLoader()
        system_info = loader._detect_system_resources()

        assert system_info['cpu_cores'] == 1
        assert system_info['cpu_threads'] == 1
        assert system_info['ram_gb'] == 1
        assert system_info['max_workers'] == 2
        assert system_info['batch_size'] == 50

    @patch('platform.system', return_value='Linux')
    @patch('platform.machine', return_value='x86_64')
    @patch('multiprocessing.cpu_count', return_value=16)
    @patch('os.cpu_count', return_value=32)
    @patch('psutil.virtual_memory', return_value=MagicMock(total=32 * 1024**3))
    @patch('psutil.disk_partitions', return_value=[])
    def test_detect_system_resources_high_end(
        self, mock_partitions: MagicMock, mock_memory: MagicMock,
        mock_cpu_count: MagicMock, mock_os_cpu_count: MagicMock,
        mock_machine: MagicMock, mock_system: MagicMock
    ):
        """Test system resource detection for high-end system."""
        loader = CoreLoader()
        system_info = loader._detect_system_resources()

        assert system_info['cpu_cores'] == 16
        assert system_info['cpu_threads'] == 32
        assert system_info['ram_gb'] == 32
        # The max_workers is capped at 16 for this configuration
        assert system_info['max_workers'] == 16
        assert system_info['batch_size'] == 1000


class TestResourceConfiguration:
    """Test resource-based configuration."""

    def test_configure_based_on_resources_ssd(self):
        """Test resource-based configuration for SSD."""
        loader = CoreLoader()
        system_info: SystemInfo = {
            'cpu_cores': 4,
            'cpu_threads': 8,
            'ram_gb': 16,
            'drive_type': 'ssd',
        }

        loader._configure_based_on_resources(system_info)

        assert system_info['disk_cache_size'] == '2GB'
        assert system_info['use_disk_cache'] is True
        assert system_info['max_workers'] == 4
        assert system_info['batch_size'] == 500

    def test_configure_based_on_resources_low_ram(self):
        """Test resource-based configuration for low RAM."""
        loader = CoreLoader()
        system_info: SystemInfo = {
            'cpu_cores': 2,
            'cpu_threads': 2,
            'ram_gb': 2,
            'drive_type': 'hdd',
        }

        loader._configure_based_on_resources(system_info)

        assert system_info['batch_size'] == 50
        assert system_info['memory_cache_size'] == '50MB'
        assert system_info['max_workers'] == 2

    def test_configure_based_on_resources_sdcard(self):
        """Test resource-based configuration for SD card storage."""
        loader = CoreLoader()
        system_info: SystemInfo = {
            'cpu_cores': 4,
            'cpu_threads': 4,
            'ram_gb': 4,
            'drive_type': 'sdcard',
        }

        loader._configure_based_on_resources(system_info)

        assert system_info['disk_cache_size'] == '500MB'
        assert system_info['sdcard_optimized'] is True


class TestThreadRestrictions:
    """Test thread restriction detection."""

    def test_detect_thread_restrictions_no_restrictions(self):
        """Test thread restriction detection when no restrictions exist."""
        loader = CoreLoader()
        system_info: SystemInfo = {'cpu_cores': 8, 'ram_gb': 16, 'max_workers': 8}

        with patch.dict('os.environ', {}, clear=True):
            loader._detect_thread_restrictions(system_info)

        assert system_info.get('thread_restrictions_detected') is None
        assert system_info.get('max_workers') == 8  # Should remain unchanged

    @patch.dict('os.environ', {'KUBERNETES_SERVICE_HOST': 'true'})
    def test_detect_thread_restrictions_kubernetes(self):
        """Test thread restriction detection in Kubernetes environment."""
        loader = CoreLoader()
        system_info: SystemInfo = {'cpu_cores': 8, 'ram_gb': 16, 'max_workers': 8}

        loader._detect_thread_restrictions(system_info)

        assert system_info['thread_restrictions_detected'] is True
        assert 'kubernetes' in system_info.get('thread_restriction_reasons', [])

    @patch.dict('os.environ', {'DOCKER_CONTAINER': 'true'})
    def test_detect_thread_restrictions_docker(self):
        """Test thread restriction detection in Docker container."""
        loader = CoreLoader()
        system_info: SystemInfo = {'cpu_cores': 8, 'ram_gb': 16, 'max_workers': 8}

        loader._detect_thread_restrictions(system_info)

        assert system_info['thread_restrictions_detected'] is True
        assert 'container' in system_info.get('thread_restriction_reasons', [])


class TestCoreLoaderLifecycle:
    """Test CoreLoader initialize and shutdown."""

    def test_initialize_sets_initialized_flag(self):
        """Test that initialize sets the initialized flag on success."""
        loader = CoreLoader()
        
        with patch('nodupe.core.loader.load_config') as mock_config, \
             patch('nodupe.core.loader.global_container') as mock_container, \
             patch('nodupe.core.loader.PluginRegistry') as mock_registry, \
             patch('nodupe.core.loader.create_plugin_loader') as mock_loader, \
             patch('nodupe.core.loader.create_plugin_discovery') as mock_discovery, \
             patch('nodupe.core.loader.create_lifecycle_manager') as mock_lifecycle, \
             patch('nodupe.core.loader.PluginHotReload') as mock_hot_reload, \
             patch('nodupe.core.loader.get_connection') as mock_db:
            
            # Set up mocks
            mock_config.return_value = MagicMock(config={})
            mock_registry_instance = MagicMock()
            mock_registry.return_value = mock_registry_instance
            mock_hot_reload_instance = MagicMock()
            mock_hot_reload.return_value = mock_hot_reload_instance
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            mock_lifecycle_instance = MagicMock()
            mock_lifecycle.return_value = mock_lifecycle_instance
            
            loader.initialize()
            
            assert loader.initialized is True

    def test_initialize_idempotent(self):
        """Test that initialize is idempotent (calling twice doesn't reinitialize)."""
        loader = CoreLoader()
        loader.initialized = True  # Pretend already initialized
        
        # Should return early without doing anything
        loader.initialize()
        
        # Should still be in the same state
        assert loader.initialized is True
        assert loader.config is None  # Wasn't actually initialized

    def test_shutdown_not_initialized(self):
        """Test that shutdown does nothing if not initialized."""
        loader = CoreLoader()
        assert loader.initialized is False
        
        # Should return early without error
        loader.shutdown()
        
        assert loader.initialized is False


class TestBootstrap:
    """Test the bootstrap function."""

    def test_bootstrap_returns_loader(self):
        """Test that bootstrap returns a CoreLoader instance."""
        with patch('nodupe.core.loader.load_config') as mock_config, \
             patch('nodupe.core.loader.global_container') as mock_container, \
             patch('nodupe.core.loader.PluginRegistry') as mock_registry, \
             patch('nodupe.core.loader.create_plugin_loader') as mock_loader, \
             patch('nodupe.core.loader.create_plugin_discovery') as mock_discovery, \
             patch('nodupe.core.loader.create_lifecycle_manager') as mock_lifecycle, \
             patch('nodupe.core.loader.PluginHotReload') as mock_hot_reload, \
             patch('nodupe.core.loader.get_connection') as mock_db:
            
            mock_config.return_value = MagicMock(config={})
            mock_registry_instance = MagicMock()
            mock_registry.return_value = mock_registry_instance
            mock_hot_reload.return_value = MagicMock()
            mock_db.return_value = MagicMock()
            mock_lifecycle.return_value = MagicMock()
            
            result = bootstrap()
            
            assert isinstance(result, CoreLoader)
            assert result.initialized is True
