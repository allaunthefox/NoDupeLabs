#!/usr/bin/env python3
"""
Unit tests for CoreLoader class in nodupe.core.main
"""

import os
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch, mock_open
from nodupe.core.main import CoreLoader

# Type alias for system info dictionary
SystemInfo = Dict[str, Any]

# Suppress Pylance warnings for protected member access in tests
# This is legitimate as tests need to access internal implementation details
# pylint: disable=protected-access
# pyright: reportPrivateUsage=false
# pragma: pylance disable=protected-access

class TestCoreLoader:
    """Test suite for CoreLoader class"""

    def test_init(self):
        """Test initialization of CoreLoader"""
        loader = CoreLoader()
        assert loader.plugins == []
        assert loader.services == {}
        assert loader.config == {}

    @patch('builtins.open', new_callable=mock_open, read_data='test: yaml')
    @patch('os.path.exists', return_value=True)
    @patch('yaml.safe_load', return_value={'test': 'config'})
    def test_load_config_with_yaml(self, mock_yaml: MagicMock, mock_exists: MagicMock, mock_file: MagicMock):
        """Test loading configuration with YAML file"""
        loader = CoreLoader()
        config = loader.load_config("test.yml")
        # Should merge YAML config with platform autoconfig
        assert 'test' in config
        assert config['test'] == 'config'
        assert 'db_path' in config  # Should still have platform config

    @patch('yaml.safe_load', side_effect=Exception("YAML error"))
    @patch('os.path.exists', return_value=True)
    def test_load_config_yaml_error(self, mock_exists: MagicMock, mock_yaml: MagicMock):
        """Test loading configuration when YAML parsing fails"""
        loader = CoreLoader()
        config = loader.load_config("test.yml")
        # Should fall back to platform autoconfig
        assert 'db_path' in config
        assert 'log_dir' in config

    @patch('os.path.exists', return_value=False)
    def test_load_config_missing_file(self, mock_exists: MagicMock):
        """Test loading configuration when file doesn't exist"""
        loader = CoreLoader()
        config = loader.load_config("missing.yml")
        # Should fall back to platform autoconfig
        assert 'db_path' in config
        assert 'log_dir' in config

    @patch('yaml.safe_load', return_value=None)
    @patch('os.path.exists', return_value=True)
    def test_load_config_empty_yaml(self, mock_exists: MagicMock, mock_yaml: MagicMock):
        """Test loading configuration with empty YAML"""
        loader = CoreLoader()
        config = loader.load_config("empty.yml")
        # Should fall back to platform autoconfig
        assert 'db_path' in config
        assert 'log_dir' in config

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
        """Test platform-specific autoconfiguration for Windows"""
        loader = CoreLoader()
        config = loader._apply_platform_autoconfig()  # pylance: disable=protected-access

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
        """Test platform-specific autoconfiguration for Linux"""
        loader = CoreLoader()
        config = loader._apply_platform_autoconfig()  # pylance: disable=protected-access

        assert config['db_path'] == 'output/index.db'
        assert config['use_symlinks'] is True
        assert 'plugins' in config

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
        """Test system resource detection for low-end system"""
        loader = CoreLoader()
        system_info = loader._detect_system_resources()  # pylance: disable=protected-access

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
        """Test system resource detection for high-end system"""
        loader = CoreLoader()
        system_info = loader._detect_system_resources()  # pylance: disable=protected-access

        assert system_info['cpu_cores'] == 16
        assert system_info['cpu_threads'] == 32
        assert system_info['ram_gb'] == 32
        # The max_workers is capped at 16 for this configuration
        assert system_info['max_workers'] == 16
        assert system_info['batch_size'] == 1000

    @patch('platform.system', return_value='Linux')
    @patch('platform.machine', return_value='x86_64')
    @patch('multiprocessing.cpu_count', return_value=4)
    @patch('os.cpu_count', return_value=8)
    @patch('psutil.virtual_memory', return_value=MagicMock(total=16 * 1024**3))
    @patch('psutil.disk_partitions', return_value=[])
    def test_configure_based_on_resources_ssd(
        self, mock_partitions: MagicMock, mock_memory: MagicMock,
        mock_cpu_count: MagicMock, mock_os_cpu_count: MagicMock,
        mock_machine: MagicMock, mock_system: MagicMock
    ):
        """Test resource-based configuration for SSD"""
        loader = CoreLoader()
        system_info: SystemInfo = {
            'cpu_cores': 4,
            'cpu_threads': 8,
            'ram_gb': 16,
            'drive_type': 'ssd',
            'max_workers': 2,
            'batch_size': 100
        }

        loader._configure_based_on_resources(system_info)  # pylance: disable=protected-access

        assert system_info['processing_strategy'] == 'balanced'
        assert system_info['concurrency_model'] == 'threaded'
        assert system_info['disk_cache_size'] == '2GB'

    @patch('platform.system', return_value='Linux')
    @patch('platform.machine', return_value='x86_64')
    @patch('multiprocessing.cpu_count', return_value=2)
    @patch('os.cpu_count', return_value=2)
    @patch('psutil.virtual_memory', return_value=MagicMock(total=2 * 1024**3))
    @patch('psutil.disk_partitions', return_value=[])
    def test_configure_based_on_resources_low_ram(
        self, mock_partitions: MagicMock, mock_memory: MagicMock,
        mock_cpu_count: MagicMock, mock_os_cpu_count: MagicMock,
        mock_machine: MagicMock, mock_system: MagicMock
    ):
        """Test resource-based configuration for low RAM"""
        loader = CoreLoader()
        system_info: SystemInfo = {
            'cpu_cores': 2,
            'cpu_threads': 2,
            'ram_gb': 2,
            'drive_type': 'hdd',
            'max_workers': 2,
            'batch_size': 100
        }

        loader._configure_based_on_resources(system_info)  # pylance: disable=protected-access

        assert system_info['processing_strategy'] == 'conservative'
        assert system_info['concurrency_model'] == 'sequential'
        assert system_info['batch_size'] == 50
        assert system_info['memory_cache_size'] == '50MB'

    def test_detect_thread_restrictions_no_restrictions(self):
        """Test thread restriction detection when no restrictions exist"""
        loader = CoreLoader()
        system_info: SystemInfo = {'cpu_cores': 8, 'ram_gb': 16, 'max_workers': 8}

        with patch('os.environ', {}):
            loader._detect_thread_restrictions(system_info)  # pylance: disable=protected-access

        assert system_info.get('thread_restrictions_detected') is None
        assert system_info.get('max_workers') == 8  # Should remain unchanged

    @patch.dict('os.environ', {'KUBERNETES_SERVICE_HOST': 'true', 'DOCKER_CONTAINER': 'true'})
    def test_detect_thread_restrictions_container(self):
        """Test thread restriction detection in container environment"""
        loader = CoreLoader()
        system_info: SystemInfo = {
            'cpu_cores': 8, 'ram_gb': 16, 'max_workers': 8, 'batch_size': 100
        }

        loader._detect_thread_restrictions(system_info)  # pylance: disable=protected-access

        assert system_info['thread_restrictions_detected'] is True
        restriction_reasons = system_info.get('thread_restriction_reasons', [])
        assert isinstance(restriction_reasons, list)
        assert 'kubernetes' in restriction_reasons
        assert 'container' in restriction_reasons
        assert system_info['max_workers'] == 4  # Should be reduced
        assert system_info['batch_size'] == 100  # Should be reduced to 100
        assert system_info['processing_strategy'] == 'conservative'

    def test_check_python_version_compatible(self):
        """Test Python version check with compatible version"""
        loader = CoreLoader()
        mock_version_info = MagicMock()
        mock_version_info.major = 3
        mock_version_info.minor = 9
        mock_version_info.micro = 0
        with patch('sys.version_info', mock_version_info):
            assert loader._check_python_version() is True  # pylance: disable=protected-access

    def test_check_python_version_incompatible(self):
        """Test Python version check with incompatible version"""
        loader = CoreLoader()
        mock_version_info = MagicMock()
        mock_version_info.major = 3
        mock_version_info.minor = 8
        mock_version_info.micro = 0
        with patch('sys.version_info', mock_version_info):
            assert loader._check_python_version() is False  # pylance: disable=protected-access

    @patch('nodupe.core.main.PluginManager', None)
    def test_initialize_no_plugin_manager(self):
        """Test initialization when PluginManager is not available"""
        loader = CoreLoader()
        with patch.object(loader, '_check_python_version', return_value=True):  # pylance: disable=protected-access
            result = loader.initialize()
            assert result is True
            assert loader.services['plugin_manager'] is None

    @patch('nodupe.core.main.PluginManager')
    def test_initialize_with_plugin_manager(self, mock_plugin_manager: MagicMock):
        """Test initialization when PluginManager is available"""
        mock_plugin_instance = MagicMock()
        mock_plugin_manager.return_value = mock_plugin_instance

        loader = CoreLoader()
        with patch.object(loader, '_check_python_version', return_value=True):  # pylance: disable=protected-access
            result = loader.initialize()
            assert result is True
            assert loader.services['plugin_manager'] is mock_plugin_instance

    @patch('nodupe.core.main.PluginManager', None)
    @patch('nodupe.core.main.yaml', None)
    def test_run_no_args(self):
        """Test running CoreLoader with no arguments"""
        loader = CoreLoader()
        with patch.object(loader, 'initialize', return_value=True):
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_parser_instance = MagicMock()
                mock_parser.return_value = mock_parser_instance
                mock_args = MagicMock(command=None)
                mock_parser_instance.parse_args.return_value = mock_args

                result = loader.run()
                assert result == 0

    def test_cmd_version(self):
        """Test version command"""
        loader = CoreLoader()
        mock_args = MagicMock()
        result = loader._cmd_version(mock_args)  # pylance: disable=protected-access
        assert result == 0

    def test_cmd_plugin_no_plugin_manager(self):
        """Test plugin command when plugin manager is not available"""
        loader = CoreLoader()
        loader.services['plugin_manager'] = None
        mock_args = MagicMock(list=False)
        result = loader._cmd_plugin(mock_args)  # pylance: disable=protected-access
        assert result == 1

    def test_cmd_plugin_list(self):
        """Test plugin list command"""
        loader = CoreLoader()
        mock_plugin_manager = MagicMock()
        mock_plugin_manager.list_plugins.return_value = ['plugin1', 'plugin2']
        loader.services['plugin_manager'] = mock_plugin_manager

        mock_args = MagicMock(list=True)
        result = loader._cmd_plugin(mock_args)  # pylance: disable=protected-access
        assert result == 0

    def test_main_function(self):
        """Test main function"""
        with patch('nodupe.core.main.CoreLoader') as mock_loader_class:
            mock_loader_instance = MagicMock()
            mock_loader_class.return_value = mock_loader_instance
            mock_loader_instance.run.return_value = 0

            result = main()
            assert result == 0

    def test_main_function_exception(self):
        """Test main function with exception"""
        with patch('nodupe.core.main.CoreLoader', side_effect=Exception("Test error")):
            result = main()
            assert result == 1

    def test_main_function_keyboard_interrupt(self):
        """Test main function with keyboard interrupt"""
        with patch('nodupe.core.main.CoreLoader', side_effect=KeyboardInterrupt()):
            result = main()
            assert result == 130

def main(args: Optional[Any] = None) -> int:
    """Main entry point for testing."""
    from nodupe.core.main import main
    return main(args)
