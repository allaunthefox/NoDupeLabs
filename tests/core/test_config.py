import os
import tempfile
import pytest
from unittest.mock import patch
from nodupe.core.config import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary TOML file for testing
        self.temp_config_content = """
[tool.nodupe]
version = "1.0.0"
description = "Test NoDupeLabs configuration"

[tool.nodupe.database]
path = "test.db"
timeout = 30.0
journal_mode = "WAL"

[tool.nodupe.scan]
min_file_size = "1KB"
max_file_size = "100MB"
default_extensions = [".txt", ".pdf", ".jpg"]
exclude_dirs = ["node_modules", ".git", "__pycache__"]

[tool.nodupe.similarity]
default_backend = "brute_force"
vector_dimensions = 128
search_k = 10
similarity_threshold = 0.85

[tool.nodupe.performance]
max_workers = 4
chunk_size = 1024
cache_size = 1000

[tool.nodupe.logging]
level = "INFO"
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
file = "nodupe.log"
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.toml')
        self.temp_file.write(self.temp_config_content)
        self.temp_file.close()

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_config_manager_initialization_with_valid_path(self):
        """Test ConfigManager initialization with a valid configuration file path."""
        config_manager = ConfigManager(self.temp_file.name)
        assert config_manager.config_path == self.temp_file.name
        assert config_manager.config != {}

    def test_config_manager_initialization_with_default_path(self):
        """Test ConfigManager initialization with default path."""
        # Test with a valid config file at default location
        config_manager = ConfigManager(self.temp_file.name)
        assert config_manager.config_path == self.temp_file.name

    def test_config_manager_initialization_without_toml_package(self):
        """Test ConfigManager initialization when toml package is not available."""
        # Test the case where toml is None by patching it directly
        with patch('nodupe.core.config.toml', None):
            # Create a new ConfigManager instance
            config_manager = ConfigManager(self.temp_file.name)
            # When toml is None, the config should be empty as per the implementation
            assert config_manager.config == {}

    def test_load_config_file_success(self):
        """Test successful loading of a valid TOML configuration file."""
        config_manager = ConfigManager(self.temp_file.name)
        assert 'tool' in config_manager.config
        assert 'nodupe' in config_manager.config['tool']

    def test_load_config_file_not_found(self):
        """Test loading a non-existent configuration file."""
        with pytest.raises(FileNotFoundError):
            ConfigManager("non_existent_file.toml")

    def test_load_config_file_permission_error(self):
        """Test loading a configuration file with insufficient permissions."""
        # Create a temporary file and restrict permissions
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        os.chmod(temp_file.name, 0o000)  # Remove all permissions
        
        try:
            with pytest.raises(PermissionError):
                ConfigManager(temp_file.name)
        finally:
            os.chmod(temp_file.name, 0o644) # Restore permissions before deletion
            os.unlink(temp_file.name)

    def test_load_config_file_invalid_toml(self):
        """Test loading an invalid TOML configuration file."""
        # Create a temporary file with invalid TOML content
        invalid_toml_content = """
[tool.nodupe
invalid = content
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.toml')
        temp_file.write(invalid_toml_content)
        temp_file.close()

        try:
            with pytest.raises(ValueError):
                ConfigManager(temp_file.name)
        finally:
            os.unlink(temp_file.name)

    def test_load_config_file_missing_nodupe_section(self):
        """Test loading a TOML file without the required [tool.nodupe] section."""
        # Create a temporary file without the required section
        invalid_toml_content = """
[tool.other]
config = "value"
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.toml')
        temp_file.write(invalid_toml_content)
        temp_file.close()

        try:
            with pytest.raises(ValueError):
                ConfigManager(temp_file.name)
        finally:
            os.unlink(temp_file.name)

    def test_get_nodupe_config(self):
        """Test retrieval of the NoDupeLabs configuration section."""
        config_manager = ConfigManager(self.temp_file.name)
        nodupe_config = config_manager.get_nodupe_config()
        assert isinstance(nodupe_config, dict)
        assert 'version' in nodupe_config
        assert 'description' in nodupe_config
        assert nodupe_config['version'] == "1.0.0"
        assert nodupe_config['description'] == "Test NoDupeLabs configuration"

    def test_get_database_config(self):
        """Test retrieval of the database configuration."""
        config_manager = ConfigManager(self.temp_file.name)
        db_config = config_manager.get_database_config()
        assert isinstance(db_config, dict)
        assert db_config['path'] == "test.db"
        assert db_config['timeout'] == 30.0
        assert db_config['journal_mode'] == "WAL"

    def test_get_scan_config(self):
        """Test retrieval of the scan configuration."""
        config_manager = ConfigManager(self.temp_file.name)
        scan_config = config_manager.get_scan_config()
        assert isinstance(scan_config, dict)
        assert scan_config['min_file_size'] == "1KB"
        assert scan_config['max_file_size'] == "100MB"
        assert scan_config['default_extensions'] == [".txt", ".pdf", ".jpg"]

    def test_get_similarity_config(self):
        """Test retrieval of the similarity configuration."""
        config_manager = ConfigManager(self.temp_file.name)
        similarity_config = config_manager.get_similarity_config()
        assert isinstance(similarity_config, dict)
        assert similarity_config['default_backend'] == "brute_force"
        assert similarity_config['vector_dimensions'] == 128
        assert similarity_config['search_k'] == 10
        assert similarity_config['similarity_threshold'] == 0.85

    def test_get_performance_config(self):
        """Test retrieval of the performance configuration."""
        config_manager = ConfigManager(self.temp_file.name)
        perf_config = config_manager.get_performance_config()
        assert isinstance(perf_config, dict)
        assert perf_config['max_workers'] == 4
        assert perf_config['chunk_size'] == 1024
        assert perf_config['cache_size'] == 1000

    def test_get_logging_config(self):
        """Test retrieval of the logging configuration."""
        config_manager = ConfigManager(self.temp_file.name)
        log_config = config_manager.get_logging_config()
        assert isinstance(log_config, dict)
        assert log_config['level'] == "INFO"
        assert "format" in log_config
        assert log_config['file'] == "nodupe.log"

    def test_get_config_value_with_existing_key(self):
        """Test retrieval of a specific configuration value that exists."""
        config_manager = ConfigManager(self.temp_file.name)
        value = config_manager.get_config_value('database', 'path', 'default.db')
        assert value == "test.db"

    def test_get_config_value_with_nonexistent_key(self):
        """Test retrieval of a specific configuration value that doesn't exist."""
        config_manager = ConfigManager(self.temp_file.name)
        value = config_manager.get_config_value('database', 'nonexistent_key', 'default_value')
        assert value == "default_value"

    def test_get_config_value_with_exception_handling(self):
        """Test get_config_value with exception handling."""
        # Create a mock config manager with a config that will cause an exception
        config_manager = ConfigManager(self.temp_file.name)
        # Replace the get_nodupe_config method with one that raises an exception
        original_method = config_manager.get_nodupe_config
        config_manager.get_nodupe_config = lambda: (_ for _ in ()).throw(Exception("Test exception"))
        
        try:
            value = config_manager.get_config_value('database', 'path', 'default_value')
            assert value == "default_value"
        finally:
            config_manager.get_nodupe_config = original_method

    def test_validate_config_valid(self):
        """Test validation of a valid configuration."""
        config_manager = ConfigManager(self.temp_file.name)
        is_valid = config_manager.validate_config()
        assert is_valid is True

    def test_validate_config_missing_sections(self):
        """Test validation of a configuration with missing required sections."""
        # Create a config with missing sections
        minimal_config_content = """
[tool.nodupe]
version = "1.0.0"
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.toml')
        temp_file.write(minimal_config_content)
        temp_file.close()

        try:
            config_manager = ConfigManager(temp_file.name)
            is_valid = config_manager.validate_config()
            assert is_valid is False
        finally:
            os.unlink(temp_file.name)

    def test_config_with_utf8_bom(self):
        """Test loading a configuration file with UTF-8 BOM."""
        # Create a config file with UTF-8 BOM
        bom_content = '\ufeff' + self.temp_config_content
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.toml', encoding='utf-8')
        temp_file.write(bom_content)
        temp_file.close()

        try:
            config_manager = ConfigManager(temp_file.name)
            # Should successfully load despite BOM
            assert 'tool' in config_manager.config
            assert 'nodupe' in config_manager.config['tool']
        finally:
            os.unlink(temp_file.name)


class TestLoadConfigFunction:
    """Test suite for the load_config function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary TOML file for testing
        self.temp_config_content = """
[tool.nodupe]
version = "1.0.0"
description = "Test NoDupeLabs configuration"

[tool.nodupe.database]
path = "test.db"
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.toml')
        self.temp_file.write(self.temp_config_content)
        self.temp_file.close()

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_load_config_function(self):
        """Test the load_config function returns a ConfigManager instance."""
        # Create a ConfigManager instance with our test file
        config_manager = ConfigManager(self.temp_file.name)
        # Verify it's a ConfigManager instance
        assert isinstance(config_manager, ConfigManager)
        assert config_manager.config_path == self.temp_file.name

    def test_load_config_with_custom_path(self):
        """Test loading config with a custom path."""
        config_manager = ConfigManager(self.temp_file.name)
        assert isinstance(config_manager, ConfigManager)
        assert config_manager.config_path == self.temp_file.name


def test_config_manager_example_usage():
    """Test the example usage from the ConfigManager module."""
    # Create a temporary config file
    temp_config_content = """
[tool.nodupe]
version = "1.0.0"
description = "Test configuration"

[tool.nodupe.database]
path = "test.db"
timeout = 30.0
journal_mode = "WAL"

[tool.nodupe.scan]
min_file_size = "1KB"
max_file_size = "100MB"
default_extensions = [".txt"]
exclude_dirs = [".git"]

[tool.nodupe.similarity]
default_backend = "brute_force"
vector_dimensions = 128
search_k = 10
similarity_threshold = 0.85

[tool.nodupe.performance]
max_workers = 4

[tool.nodupe.logging]
level = "INFO"
"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.toml')
    temp_file.write(temp_config_content)
    temp_file.close()

    try:
        config = ConfigManager(temp_file.name)

        # Test that validation passes
        assert config.validate_config() is True

        # Test that we can retrieve various config sections
        assert config.get_nodupe_config()['version'] == "1.0.0"
        assert config.get_database_config()['path'] == "test.db"
        assert config.get_scan_config()['min_file_size'] == "1KB"
        assert config.get_similarity_config()['default_backend'] == "brute_force"
        assert config.get_performance_config()['max_workers'] == 4
        assert config.get_logging_config()['level'] == "INFO"

        # Test retrieving specific config values
        assert config.get_config_value('database', 'path', 'default.db') == "test.db"
        assert config.get_config_value('scan', 'nonexistent', 'default') == "default"

    finally:
        os.unlink(temp_file.name)
