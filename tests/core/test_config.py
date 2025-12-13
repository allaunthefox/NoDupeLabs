#!/usr/bin/env python3
"""
Unit tests for ConfigManager class in nodupe.core.config
"""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
from nodupe.core.config import ConfigManager

class TestConfigManager:
    """Test suite for ConfigManager class"""

    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('nodupe.core.config.os.path.exists', return_value=False)
    def test_init_with_default_path(self, mock_exists: MagicMock, mock_open: MagicMock):
        """Test initialization with default config path"""
        # This should raise FileNotFoundError since pyproject.toml doesn't exist in test context
        with pytest.raises(FileNotFoundError):
            ConfigManager()

    def test_init_with_custom_path(self):
        """Test initialization with custom config path"""
        # This should raise FileNotFoundError since custom.toml doesn't exist
        with pytest.raises(FileNotFoundError):
            ConfigManager("custom.toml")

    @patch('builtins.open', new_callable=mock_open, read_data='[tool.nodupe]\ndatabase = {}')
    @patch('os.path.exists', return_value=True)
    def test_load_valid_config(self, mock_exists: MagicMock, mock_file: MagicMock):
        """Test loading a valid configuration file"""
        config_manager = ConfigManager("test.toml")
        assert config_manager.config_path == "test.toml"
        assert 'tool' in config_manager.config
        assert 'nodupe' in config_manager.config['tool']

    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('os.path.exists', return_value=False)
    def test_load_missing_config_file(self, mock_exists: MagicMock, mock_file: MagicMock):
        """Test handling of missing configuration file"""
        with pytest.raises(FileNotFoundError):
            ConfigManager("missing.toml")

    @patch('builtins.open', new_callable=mock_open, read_data='invalid: toml')
    @patch('os.path.exists', return_value=True)
    def test_load_invalid_toml(self, mock_exists: MagicMock, mock_file: MagicMock):
        """Test handling of invalid TOML syntax"""
        with pytest.raises(Exception):
            ConfigManager("invalid.toml")

    @patch('nodupe.core.config.toml.load', return_value={'tool': {}})
    @patch('builtins.open', new_callable=mock_open, read_data='[tool]\nnodupe = {}')
    @patch('nodupe.core.config.os.path.exists', return_value=True)
    def test_load_missing_nodupe_section(self, mock_exists: MagicMock, mock_file: MagicMock, mock_toml_load: MagicMock):
        """Test handling of missing nodupe section"""
        with pytest.raises(ValueError):
            ConfigManager("missing_section.toml")

    def test_get_nodupe_config(self):
        """Test getting nodupe configuration section"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe]\n[tool.nodupe.database]\npath = "test.db"\n[tool.nodupe.scan]\nmin_size = 1024')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                nodupe_config = config_manager.get_nodupe_config()
                assert 'database' in nodupe_config
                assert 'scan' in nodupe_config
                assert nodupe_config['database']['path'] == 'test.db'
                assert nodupe_config['scan']['min_size'] == 1024
            finally:
                os.unlink(f.name)

    def test_get_database_config(self):
        """Test getting database configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe.database]\npath = "test.db"\ntimeout = 30')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                db_config = config_manager.get_database_config()
                assert db_config['path'] == 'test.db'
                assert db_config['timeout'] == 30
            finally:
                os.unlink(f.name)

    def test_get_scan_config(self):
        """Test getting scan configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe.scan]\nmin_file_size = "1KB"\nexclude_dirs = [".git"]')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                scan_config = config_manager.get_scan_config()
                assert scan_config['min_file_size'] == '1KB'
                assert scan_config['exclude_dirs'] == ['.git']
            finally:
                os.unlink(f.name)

    def test_get_similarity_config(self):
        """Test getting similarity configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe.similarity]\ndefault_backend = "brute_force"\nvector_dimensions = 128')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                similarity_config = config_manager.get_similarity_config()
                assert similarity_config['default_backend'] == 'brute_force'
                assert similarity_config['vector_dimensions'] == 128
            finally:
                os.unlink(f.name)

    def test_get_performance_config(self):
        """Test getting performance configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe.performance]\nmax_workers = 4\nbatch_size = 100')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                performance_config = config_manager.get_performance_config()
                assert performance_config['max_workers'] == 4
                assert performance_config['batch_size'] == 100
            finally:
                os.unlink(f.name)

    def test_get_logging_config(self):
        """Test getting logging configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe.logging]\nlevel = "INFO"\nfile = "nodupe.log"')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                logging_config = config_manager.get_logging_config()
                assert logging_config['level'] == 'INFO'
                assert logging_config['file'] == 'nodupe.log'
            finally:
                os.unlink(f.name)

    def test_get_config_value_existing(self):
        """Test getting existing configuration value"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe.database]\npath = "test.db"')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                value = config_manager.get_config_value('database', 'path')
                assert value == 'test.db'
            finally:
                os.unlink(f.name)

    def test_get_config_value_missing_section(self):
        """Test getting configuration value from missing section"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe.database]\npath = "test.db"')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                value = config_manager.get_config_value('missing_section', 'key', 'default')
                assert value == 'default'
            finally:
                os.unlink(f.name)

    def test_get_config_value_missing_key(self):
        """Test getting missing configuration key"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe.database]\npath = "test.db"')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                value = config_manager.get_config_value('database', 'missing_key', 'default')
                assert value == 'default'
            finally:
                os.unlink(f.name)

    def test_get_config_value_with_exception(self):
        """Test getting configuration value when exception occurs"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe.database]\npath = "test.db"')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                # Mock an exception in get_nodupe_config
                with patch.object(config_manager, 'get_nodupe_config', side_effect=Exception("Test error")):
                    value = config_manager.get_config_value('database', 'path', 'default')
                    assert value == 'default'
            finally:
                os.unlink(f.name)

    def test_validate_config_valid(self):
        """Test validation of valid configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('''
[tool.nodupe.database]
path = "test.db"

[tool.nodupe.scan]
min_file_size = "1KB"

[tool.nodupe.similarity]
default_backend = "brute_force"

[tool.nodupe.performance]
max_workers = 4

[tool.nodupe.logging]
level = "INFO"
            ''')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                assert config_manager.validate_config() is True
            finally:
                os.unlink(f.name)

    def test_validate_config_missing_section(self):
        """Test validation of configuration with missing required section"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('''
[tool.nodupe.database]
path = "test.db"

[tool.nodupe.scan]
min_file_size = "1KB"

[tool.nodupe.similarity]
default_backend = "brute_force"

[tool.nodupe.performance]
max_workers = 4

# Missing logging section
            ''')
            f.flush()

            try:
                config_manager = ConfigManager(f.name)
                assert config_manager.validate_config() is False
            finally:
                os.unlink(f.name)

    def test_load_config_function(self):
        """Test the load_config function"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[tool.nodupe]\ndatabase = {"path": "test.db"}')
            f.flush()

            try:
                config_manager = load_config()
                # This will use default pyproject.toml, but we can test the function works
                assert isinstance(config_manager, ConfigManager)
            finally:
                os.unlink(f.name)

def load_config() -> ConfigManager:
    """Load the NoDupeLabs configuration."""
    return ConfigManager()
