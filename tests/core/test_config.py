"""Tests for the config module."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest
import tomlkit as toml

from nodupe.core.config import ConfigManager, load_config


class TestConfigManager:
    """Test suite for ConfigManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "pyproject.toml"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        config_manager = ConfigManager()
        assert config_manager is not None
        assert hasattr(config_manager, 'config')
        assert isinstance(config_manager.config, dict)

    def test_config_manager_with_custom_path(self):
        """Test ConfigManager with custom config path."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {'path': '/test/path'},
                    'scan': {'recursive': True},
                    'similarity': {'threshold': 0.8},
                    'performance': {'workers': 4},
                    'logging': {'level': 'info'}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        assert config_manager.config_path == str(self.config_path)

    def test_config_manager_missing_toml_module(self):
        """Test ConfigManager when toml module is not available."""
        with patch('nodupe.core.config.toml', None):
            config_manager = ConfigManager()
            assert config_manager.config == {}
            assert config_manager.config_path is not None

    def test_config_manager_missing_config_file(self):
        """Test ConfigManager with missing config file."""
        nonexistent_path = Path(self.temp_dir) / "nonexistent.toml"

        with pytest.raises(FileNotFoundError, match="Configuration file .* not found"):
            ConfigManager(str(nonexistent_path))

    def test_config_manager_invalid_toml(self):
        """Test ConfigManager with invalid TOML file."""
        with open(self.config_path, 'w') as f:
            f.write('invalid toml content [')

        with pytest.raises(ValueError, match="Error parsing TOML file"):
            ConfigManager(str(self.config_path))

    def test_config_manager_missing_nodupe_section(self):
        """Test ConfigManager with missing [tool.nodupe] section."""
        config_data = {
            'tool': {
                'other_tool': {'some_config': 'value'}
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        with pytest.raises(ValueError, match="missing \\[tool.nodupe\\] section"):
            ConfigManager(str(self.config_path))

    def test_get_nodupe_config(self):
        """Test getting NoDupeLabs configuration section."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {'path': '/test/path'},
                    'scan': {'recursive': True}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        nodupe_config = config_manager.get_nodupe_config()

        assert isinstance(nodupe_config, dict)
        assert 'database' in nodupe_config
        assert 'scan' in nodupe_config

    def test_get_database_config(self):
        """Test getting database configuration."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {
                        'path': '/test/database.db',
                        'timeout': 30.0,
                        'journal_mode': 'WAL'
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        db_config = config_manager.get_database_config()

        assert db_config['path'] == '/test/database.db'
        assert db_config['timeout'] == 30.0
        assert db_config['journal_mode'] == 'WAL'

    def test_get_scan_config(self):
        """Test getting scan configuration."""
        config_data = {
            'tool': {
                'nodupe': {
                    'scan': {
                        'min_file_size': '1KB',
                        'max_file_size': '100MB',
                        'default_extensions': ['jpg', 'png', 'pdf', 'docx', 'txt'],
                        'exclude_dirs': ['temp', 'cache']
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        scan_config = config_manager.get_scan_config()

        assert scan_config['min_file_size'] == '1KB'
        assert scan_config['max_file_size'] == '100MB'
        assert scan_config['default_extensions'] == ['jpg', 'png', 'pdf', 'docx', 'txt']
        assert scan_config['exclude_dirs'] == ['temp', 'cache']

    def test_get_similarity_config(self):
        """Test getting similarity configuration."""
        config_data = {
            'tool': {
                'nodupe': {
                    'similarity': {
                        'default_backend': 'brute_force',
                        'vector_dimensions': 128,
                        'search_k': 10,
                        'similarity_threshold': 0.85
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        similarity_config = config_manager.get_similarity_config()

        assert similarity_config['default_backend'] == 'brute_force'
        assert similarity_config['vector_dimensions'] == 128
        assert similarity_config['search_k'] == 10
        assert similarity_config['similarity_threshold'] == 0.85

    def test_get_performance_config(self):
        """Test getting performance configuration."""
        config_data = {
            'tool': {
                'nodupe': {
                    'performance': {
                        'workers': 4,
                        'batch_size': 100,
                        'memory_limit': '1GB'
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        performance_config = config_manager.get_performance_config()

        assert performance_config['workers'] == 4
        assert performance_config['batch_size'] == 100
        assert performance_config['memory_limit'] == '1GB'

    def test_get_logging_config(self):
        """Test getting logging configuration."""
        config_data = {
            'tool': {
                'nodupe': {
                    'logging': {
                        'level': 'info',
                        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        'file': 'nodupe.log'
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        logging_config = config_manager.get_logging_config()

        assert logging_config['level'] == 'info'
        assert logging_config['format'] == '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        assert logging_config['file'] == 'nodupe.log'

    def test_get_config_value(self):
        """Test getting specific configuration values."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {'path': '/test/path'},
                    'scan': {'recursive': True}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        # Test existing value
        path = config_manager.get_config_value('database', 'path')
        assert path == '/test/path'

        # Test non-existing value with default
        timeout = config_manager.get_config_value('database', 'timeout', 30.0)
        assert timeout == 30.0

        # Test non-existing section
        nonexistent = config_manager.get_config_value('nonexistent', 'key', 'default')
        assert nonexistent == 'default'

    def test_validate_config_success(self):
        """Test successful config validation."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {'path': '/test/path'},
                    'scan': {'recursive': True},
                    'similarity': {'threshold': 0.8},
                    'performance': {'workers': 4},
                    'logging': {'level': 'info'}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        assert config_manager.validate_config() is True

    def test_validate_config_missing_section(self):
        """Test config validation with missing required section."""
        config_data = {
            'tool': {
                'nodupe': {
                    # Missing 'scan' section
                    'database': {'path': '/test/path'},
                    'similarity': {'threshold': 0.8},
                    'performance': {'workers': 4},
                    'logging': {'level': 'info'}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        assert config_manager.validate_config() is False

    def test_validate_config_missing_multiple_sections(self):
        """Test config validation with multiple missing sections."""
        config_data = {
            'tool': {
                'nodupe': {
                    # Missing multiple sections
                    'database': {'path': '/test/path'}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))
        assert config_manager.validate_config() is False

    def test_config_manager_default_behavior(self):
        """Test ConfigManager default behavior when no config file exists."""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()

            # Should have empty config
            assert config_manager.config == {}

            # Methods should return empty dicts or defaults
            assert config_manager.get_nodupe_config() == {}
            assert config_manager.get_database_config() == {}
            assert config_manager.get_scan_config() == {}
            assert config_manager.get_similarity_config() == {}
            assert config_manager.get_performance_config() == {}
            assert config_manager.get_logging_config() == {}

    def test_config_manager_with_minimal_config(self):
        """Test ConfigManager with minimal valid config."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {'path': 'test.db'},
                    'scan': {'recursive': False},
                    'similarity': {'threshold': 0.5},
                    'performance': {'workers': 1},
                    'logging': {'level': 'debug'}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        assert config_manager.validate_config() is True
        assert config_manager.get_database_config()['path'] == 'test.db'
        assert config_manager.get_scan_config()['recursive'] is False
        assert config_manager.get_similarity_config()['threshold'] == 0.5
        assert config_manager.get_performance_config()['workers'] == 1
        assert config_manager.get_logging_config()['level'] == 'debug'

    def test_config_manager_nested_values(self):
        """Test ConfigManager with nested configuration values."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {
                        'path': '/test/path',
                        'connection': {
                            'timeout': 30,
                            'retries': 3,
                            'pool': {
                                'min_size': 1,
                                'max_size': 10
                            }
                        }
                    },
                    'scan': {
                        'recursive': True,
                        'filters': {
                            'size': {
                                'min': 1024,
                                'max': 1048576
                            },
                            'types': {
                                'include': ['*.txt', '*.pdf'],
                                'exclude': ['*.tmp']
                            }
                        }
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        db_config = config_manager.get_database_config()
        assert db_config['path'] == '/test/path'
        assert db_config['connection']['timeout'] == 30
        assert db_config['connection']['retries'] == 3
        assert db_config['connection']['pool']['min_size'] == 1
        assert db_config['connection']['pool']['max_size'] == 10

        scan_config = config_manager.get_scan_config()
        assert scan_config['recursive'] is True
        assert scan_config['filters']['size']['min'] == 1024
        assert scan_config['filters']['size']['max'] == 1048576
        assert scan_config['filters']['types']['include'] == ['*.txt', '*.pdf']
        assert scan_config['filters']['types']['exclude'] == ['*.tmp']

    def test_config_manager_array_values(self):
        """Test ConfigManager with array configuration values."""
        config_data = {
            'tool': {
                'nodupe': {
                    'scan': {
                        'default_extensions': ['.txt', '.pdf', '.doc'],
                        'exclude_dirs': ['temp', 'cache', 'logs'],
                        'include_patterns': ['*.important', '*.critical']
                    },
                    'performance': {
                        'workers': 4,
                        'batch_sizes': [10, 50, 100, 500]
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        scan_config = config_manager.get_scan_config()
        assert scan_config['default_extensions'] == ['.txt', '.pdf', '.doc']
        assert scan_config['exclude_dirs'] == ['temp', 'cache', 'logs']
        assert scan_config['include_patterns'] == ['*.important', '*.critical']

        performance_config = config_manager.get_performance_config()
        assert performance_config['workers'] == 4
        assert performance_config['batch_sizes'] == [10, 50, 100, 500]

    def test_config_manager_boolean_values(self):
        """Test ConfigManager with boolean configuration values."""
        config_data = {
            'tool': {
                'nodupe': {
                    'scan': {
                        'recursive': True,
                        'follow_symlinks': False,
                        'include_hidden': True
                    },
                    'database': {
                        'backup_enabled': True,
                        'auto_vacuum': False,
                        'foreign_keys': True
                    },
                    'performance': {
                        'parallel': True,
                        'cache_enabled': False
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        scan_config = config_manager.get_scan_config()
        assert scan_config['recursive'] is True
        assert scan_config['follow_symlinks'] is False
        assert scan_config['include_hidden'] is True

        db_config = config_manager.get_database_config()
        assert db_config['backup_enabled'] is True
        assert db_config['auto_vacuum'] is False
        assert db_config['foreign_keys'] is True

        performance_config = config_manager.get_performance_config()
        assert performance_config['parallel'] is True
        assert performance_config['cache_enabled'] is False

    def test_config_manager_numeric_values(self):
        """Test ConfigManager with numeric configuration values."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {
                        'timeout': 30.5,
                        'max_connections': 100,
                        'page_size': 4096
                    },
                    'scan': {
                        'min_file_size': 1024,
                        'max_file_size': 1048576,
                        'depth_limit': 10
                    },
                    'performance': {
                        'workers': 8,
                        'batch_size': 1000,
                        'memory_limit_mb': 512
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        db_config = config_manager.get_database_config()
        assert db_config['timeout'] == 30.5
        assert db_config['max_connections'] == 100
        assert db_config['page_size'] == 4096

        scan_config = config_manager.get_scan_config()
        assert scan_config['min_file_size'] == 1024
        assert scan_config['max_file_size'] == 1048576
        assert scan_config['depth_limit'] == 10

        performance_config = config_manager.get_performance_config()
        assert performance_config['workers'] == 8
        assert performance_config['batch_size'] == 1000
        assert performance_config['memory_limit_mb'] == 512

    def test_config_manager_string_values(self):
        """Test ConfigManager with string configuration values."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {
                        'path': '/var/lib/nodupe/database.db',
                        'journal_mode': 'WAL',
                        'synchronous': 'NORMAL'
                    },
                    'scan': {
                        'default_extensions': '.txt,.pdf,.doc',
                        'exclude_dirs': 'temp,cache,logs',
                        'encoding': 'utf-8'
                    },
                    'logging': {
                        'level': 'INFO',
                        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        'file': '/var/log/nodupe.log'
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        db_config = config_manager.get_database_config()
        assert db_config['path'] == '/var/lib/nodupe/database.db'
        assert db_config['journal_mode'] == 'WAL'
        assert db_config['synchronous'] == 'NORMAL'

        scan_config = config_manager.get_scan_config()
        assert scan_config['default_extensions'] == '.txt,.pdf,.doc'
        assert scan_config['exclude_dirs'] == 'temp,cache,logs'
        assert scan_config['encoding'] == 'utf-8'

        logging_config = config_manager.get_logging_config()
        assert logging_config['level'] == 'INFO'
        assert logging_config['format'] == '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        assert logging_config['file'] == '/var/log/nodupe.log'

    def test_config_manager_concurrent_access(self):
        """Test ConfigManager with concurrent access."""
        import threading
        import time

        config_data = {
            'tool': {
                'nodupe': {
                    'database': {'path': '/test/path'},
                    'scan': {'recursive': True},
                    'similarity': {'threshold': 0.8},
                    'performance': {'workers': 4},
                    'logging': {'level': 'info'}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        results = []
        errors = []

        def access_config():
            try:
                config_manager = ConfigManager(str(self.config_path))
                db_config = config_manager.get_database_config()
                scan_config = config_manager.get_scan_config()
                results.append((db_config['path'], scan_config['recursive']))
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=access_config)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have no errors and all results should be identical
        assert len(errors) == 0
        assert len(results) == 10
        assert all(r == ('/test/path', True) for r in results)

    def test_config_manager_large_config(self):
        """Test ConfigManager with large configuration file."""
        # Create large config
        config_data = {
            'tool': {
                'nodupe': {
                    'scan': {
                        'default_extensions': [f'.ext{i}' for i in range(1000)],
                        'exclude_dirs': [f'dir{i}' for i in range(100)],
                        'include_patterns': [f'pattern_{i}' for i in range(500)]
                    },
                    'database': {
                        'paths': [f'/path_{i}' for i in range(100)],
                        'connection_strings': {f'conn_{i}': f'sqlite:///{i}.db' for i in range(50)}
                    },
                    'performance': {
                        'worker_settings': {f'worker_{i}': i for i in range(100)},
                        'batch_sizes': [i * 10 for i in range(100)]
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        scan_config = config_manager.get_scan_config()
        assert len(scan_config['default_extensions']) == 1000
        assert len(scan_config['exclude_dirs']) == 100
        assert len(scan_config['include_patterns']) == 500

        db_config = config_manager.get_database_config()
        assert len(db_config['paths']) == 100
        assert len(db_config['connection_strings']) == 50

        performance_config = config_manager.get_performance_config()
        assert len(performance_config['worker_settings']) == 100
        assert len(performance_config['batch_sizes']) == 100

    def test_config_manager_special_characters(self):
        """Test ConfigManager with special characters in config."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {
                        'path': '/путь/к/базе/тест.db',
                        'name': 'тест_база'
                    },
                    'scan': {
                        'description': 'Тест сканирования',
                        'patterns': ['файлы.tmp', '文件.tmp', 'fichiers.tmp']
                    },
                    'logging': {
                        'format': 'Тест формата: %(message)s',
                        'file': '/логи/nodupe.log'
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        db_config = config_manager.get_database_config()
        assert db_config['path'] == '/путь/к/базе/тест.db'
        assert db_config['name'] == 'тест_база'

        scan_config = config_manager.get_scan_config()
        assert scan_config['description'] == 'Тест сканирования'
        assert scan_config['patterns'] == ['файлы.tmp', '文件.tmp', 'fichiers.tmp']

        logging_config = config_manager.get_logging_config()
        assert logging_config['format'] == 'Тест формата: %(message)s'
        assert logging_config['file'] == '/логи/nodupe.log'

    def test_config_manager_error_handling(self):
        """Test ConfigManager error handling."""
        # Test with corrupted TOML
        with open(self.config_path, 'w') as f:
            f.write('invalid toml [ content')

        with pytest.raises(ValueError, match="Error parsing TOML file"):
            ConfigManager(str(self.config_path))

    def test_config_manager_memory_usage(self):
        """Test ConfigManager memory usage doesn't grow unbounded."""
        import gc

        # Force garbage collection before test
        gc.collect()

        initial_objects = len(gc.get_objects())

        # Create many config managers
        for _ in range(100):
            ConfigManager()

        # Force garbage collection after test
        gc.collect()

        final_objects = len(gc.get_objects())

        # Should not have significant memory leak
        assert final_objects - initial_objects < 5000

    def test_config_manager_serialization(self):
        """Test ConfigManager serialization and deserialization."""
        import pickle

        config_data = {
            'tool': {
                'nodupe': {
                    'database': {'path': '/test/path'},
                    'scan': {'recursive': True},
                    'similarity': {'threshold': 0.8},
                    'performance': {'workers': 4},
                    'logging': {'level': 'info'}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = ConfigManager(str(self.config_path))

        # Serialize and deserialize
        pickled_data = pickle.dumps(config_manager)
        unpickled_manager = pickle.loads(pickled_data)

        # Should have same configuration
        assert unpickled_manager.get_database_config()['path'] == '/test/path'
        assert unpickled_manager.get_scan_config()['recursive'] is True
        assert unpickled_manager.get_similarity_config()['threshold'] == 0.8
        assert unpickled_manager.get_performance_config()['workers'] == 4
        assert unpickled_manager.get_logging_config()['level'] == 'info'


class TestLoadConfig:
    """Test suite for load_config function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "pyproject.toml"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_config_default(self):
        """Test load_config with default parameters."""
        config_manager = load_config()
        assert isinstance(config_manager, ConfigManager)

    def test_load_config_with_custom_path(self):
        """Test load_config with custom config path."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {'path': '/test/path'},
                    'scan': {'recursive': True},
                    'similarity': {'threshold': 0.8},
                    'performance': {'workers': 4},
                    'logging': {'level': 'info'}
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        config_manager = load_config(str(self.config_path))

        assert isinstance(config_manager, ConfigManager)
        assert config_manager.get_database_config()['path'] == '/test/path'

    def test_load_config_missing_file(self):
        """Test load_config with missing config file."""
        # Mock os.path.exists to simulate missing file
        with patch('os.path.exists', return_value=False):
            config_manager = load_config()
            assert isinstance(config_manager, ConfigManager)
            assert config_manager.config == {}

    def test_load_config_integration(self):
        """Test load_config integration with actual usage."""
        config_data = {
            'tool': {
                'nodupe': {
                    'database': {
                        'path': 'nodupe.db',
                        'timeout': 30.0,
                        'journal_mode': 'WAL'
                    },
                    'scan': {
                        'min_file_size': '1KB',
                        'max_file_size': '100MB',
                        'default_extensions': ['jpg', 'png', 'pdf', 'docx', 'txt'],
                        'exclude_dirs': ['temp', 'cache']
                    },
                    'similarity': {
                        'default_backend': 'brute_force',
                        'vector_dimensions': 128,
                        'search_k': 10,
                        'similarity_threshold': 0.85
                    },
                    'performance': {
                        'workers': 4,
                        'batch_size': 100,
                        'memory_limit': '1GB'
                    },
                    'logging': {
                        'level': 'info',
                        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        'file': 'nodupe.log'
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

        # Load config using ConfigManager with explicit path
        config_manager = ConfigManager(str(self.config_path))

        # Verify all sections are accessible
        assert config_manager.validate_config() is True

        db_config = config_manager.get_database_config()
        assert db_config['path'] == 'nodupe.db'
        assert db_config['timeout'] == 30.0
        assert db_config['journal_mode'] == 'WAL'

        scan_config = config_manager.get_scan_config()
        assert scan_config['min_file_size'] == '1KB'
        assert scan_config['max_file_size'] == '100MB'
        assert scan_config['default_extensions'] == ['jpg', 'png', 'pdf', 'docx', 'txt']
        assert scan_config['exclude_dirs'] == ['temp', 'cache']

        similarity_config = config_manager.get_similarity_config()
        assert similarity_config['default_backend'] == 'brute_force'
        assert similarity_config['vector_dimensions'] == 128
        assert similarity_config['search_k'] == 10
        assert similarity_config['similarity_threshold'] == 0.85

        performance_config = config_manager.get_performance_config()
        assert performance_config['workers'] == 4
        assert performance_config['batch_size'] == 100
        assert performance_config['memory_limit'] == '1GB'

        logging_config = config_manager.get_logging_config()
        assert logging_config['level'] == 'info'
        assert logging_config['format'] == '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        assert logging_config['file'] == 'nodupe.log'
