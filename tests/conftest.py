# NoDupeLabs Test Fixtures and Configuration
# Comprehensive test fixtures for database operations, file system operations, plugin system mocking, etc.

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any, Optional, Callable
import sqlite3
import pytest  # type: ignore
from unittest.mock import MagicMock, patch
import nodupe.core.container as container_module
from nodupe.core.container import ServiceContainer
import nodupe.core.config as config
from nodupe.core.database.connection import DatabaseConnection
from nodupe.core.plugin_system.registry import PluginRegistry
from nodupe.core.plugin_system.loader import PluginLoader

## Database Fixtures

@pytest.fixture(scope="function")
def temp_db_connection() -> Generator[DatabaseConnection, None, None]:
    """Create a temporary in-memory SQLite database connection for testing."""
    conn = DatabaseConnection(":memory:")
    try:
        yield conn
    finally:
        conn.close()

@pytest.fixture(scope="function")
def temp_db_file() -> Generator[str, None, None]:
    """Create a temporary database file that gets cleaned up after tests."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()

    try:
        yield temp_file.name
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

@pytest.fixture(scope="function")
def db_cursor(temp_db_connection: DatabaseConnection) -> Generator[sqlite3.Cursor, None, None]:
    """Provide a database cursor for direct SQL testing."""
    cursor = temp_db_connection.get_connection().cursor()
    try:
        yield cursor
    finally:
        cursor.close()

@pytest.fixture(scope="function")
def db_with_schema(temp_db_connection: DatabaseConnection) -> Generator[DatabaseConnection, None, None]:
    """Create a database with basic schema for testing."""
    cursor = temp_db_connection.get_connection().cursor()

    # Create basic tables
    cursor.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            size INTEGER NOT NULL,
            hash TEXT,
            modified_time INTEGER,
            is_duplicate BOOLEAN DEFAULT FALSE
        )
    """)

    cursor.execute("""
        CREATE TABLE file_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            embedding BLOB NOT NULL,
            algorithm TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE duplicates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            duplicate_file_id INTEGER NOT NULL,
            similarity_score REAL NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(id),
            FOREIGN KEY (duplicate_file_id) REFERENCES files(id)
        )
    """)

    temp_db_connection.get_connection().commit()
    yield temp_db_connection

## File System Fixtures

@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory that gets cleaned up after tests."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary file in the temp directory."""
    temp_file = temp_dir / "test_file.txt"
    temp_file.write_text("This is a test file content.")
    yield temp_file

@pytest.fixture(scope="function")
def sample_files(temp_dir: Path) -> Generator[Dict[str, Path], None, None]:
    """Create a set of sample files for duplicate detection testing."""
    files = {
        "small.txt": temp_dir / "small.txt",
        "medium.txt": temp_dir / "medium.txt",
        "large.txt": temp_dir / "large.txt",
        "duplicate_small.txt": temp_dir / "duplicate_small.txt",
        "binary.dat": temp_dir / "binary.dat"
    }

    # Create text files with different content
    files["small.txt"].write_text("Small file content")
    files["medium.txt"].write_text("Medium file content " * 100)
    files["large.txt"].write_text("Large file content " * 1000)
    files["duplicate_small.txt"].write_text("Small file content")  # Duplicate of small.txt
    files["binary.dat"].write_bytes(os.urandom(1024))

    yield files

@pytest.fixture(scope="function")
def file_system_with_duplicates(temp_dir: Path) -> Generator[Dict[str, Path], None, None]:
    """Create a file system structure with duplicates for testing."""
    # Create directory structure
    dirs = {
        "documents": temp_dir / "documents",
        "images": temp_dir / "images",
        "backups": temp_dir / "backups"
    }

    for dir_path in dirs.values():
        dir_path.mkdir()

    # Create duplicate files in different directories
    original_content = "This is original content for duplicate testing."

    files = {
        "original": dirs["documents"] / "original.txt",
        "duplicate1": dirs["images"] / "copy.txt",
        "duplicate2": dirs["backups"] / "backup.txt",
        "unique1": dirs["documents"] / "unique1.txt",
        "unique2": dirs["images"] / "unique2.txt"
    }

    # Write content
    files["original"].write_text(original_content)
    files["duplicate1"].write_text(original_content)  # Exact duplicate
    files["duplicate2"].write_text(original_content)  # Exact duplicate
    files["unique1"].write_text("Unique content 1")
    files["unique2"].write_text("Unique content 2")

    yield files

## Configuration Fixtures

@pytest.fixture(scope="function")
def mock_config() -> Generator[Dict[str, Any], None, None]:
    """Provide a mock configuration dictionary for testing."""
    yield {
        "database": {
            "path": ":memory:",
            "timeout": 10.0,
            "journal_mode": "WAL"
        },
        "scan": {
            "min_file_size": "1KB",
            "max_file_size": "10MB",
            "default_extensions": ["txt", "pdf", "jpg"],
            "exclude_dirs": [".git", ".venv"]
        },
        "performance": {
            "max_workers": 4,
            "batch_size": 100,
            "chunk_size": "1MB"
        },
        "logging": {
            "level": "DEBUG",
            "file": "test.log",
            "max_size": "5MB",
            "backup_count": 3
        }
    }

@pytest.fixture(scope="function")
def temp_config_file(temp_dir: Path, mock_config: Dict[str, Any]) -> Generator[Path, None, None]:
    """Create a temporary configuration file."""
    config_file = temp_dir / "config.toml"
    import tomlkit as toml

    with open(config_file, "w") as f:
        toml.dump(mock_config, f)

    yield config_file

@pytest.fixture(scope="function")
def loaded_config(temp_config_file: Path) -> Generator[config.ConfigManager, None, None]:
    """Load and provide a configuration object from the temp config file."""
    cfg = config.ConfigManager(str(temp_config_file))
    yield cfg

## Plugin System Fixtures

@pytest.fixture(scope="function")
def mock_plugin_registry() -> Generator[PluginRegistry, None, None]:
    """Create a mock plugin registry for testing."""
    registry = PluginRegistry()
    yield registry

@pytest.fixture(scope="function")
def mock_plugin_loader(mock_plugin_registry: PluginRegistry) -> Generator[PluginLoader, None, None]:
    """Create a mock plugin loader for testing."""
    loader = PluginLoader(mock_plugin_registry)
    yield loader

@pytest.fixture(scope="function")
def mock_plugin() -> Generator[MagicMock, None, None]:
    """Create a mock plugin object for testing."""
    mock = MagicMock()
    mock.name = "test_plugin"
    mock.version = "1.0.0"
    mock.author = "Test Author"
    mock.description = "A test plugin for NoDupeLabs"
    mock.initialize = MagicMock()
    mock.execute = MagicMock()
    mock.cleanup = MagicMock()
    yield mock

@pytest.fixture(scope="function")
def registered_mock_plugin(mock_plugin_registry: PluginRegistry, mock_plugin: MagicMock) -> Generator[MagicMock, None, None]:
    """Register a mock plugin and yield it."""
    mock_plugin_registry.register_plugin(mock_plugin)
    yield mock_plugin

## Resource Management Fixtures

@pytest.fixture(scope="function")
def memory_mapped_file(temp_file: Path) -> Generator[Any, None, None]:
    """Create a memory-mapped file for testing."""
    import mmap

    with open(temp_file, "r+b") as f:
        # Write some content first
        f.write(b"This is test content for memory mapping")
        f.flush()

        # Create memory map
        mmap_obj = mmap.mmap(f.fileno(), 0)
        try:
            yield mmap_obj
        finally:
            mmap_obj.close()

@pytest.fixture(scope="function")
def resource_pool() -> Generator[Any, None, None]:
    """Create a test resource pool."""
    from nodupe.core.pools import ResourcePool

    pool = ResourcePool(max_size=5)
    try:
        yield pool
    finally:
        pool.close()

## Container and Dependency Injection Fixtures

@pytest.fixture(scope="function")
def test_container() -> Generator[ServiceContainer, None, None]:
    """Create a test container with basic services."""
    cont = ServiceContainer()

    # Register basic services
    cont.register_service("config", mock_config())
    cont.register_service("db_connection", DatabaseConnection(":memory:"))
    cont.register_service("plugin_registry", PluginRegistry())

    yield cont

@pytest.fixture(scope="function")
def container_with_mocks(test_container: ServiceContainer) -> Generator[ServiceContainer, None, None]:
    """Create a container with mock services for testing."""
    # Add mock services
    test_container.register_service("mock_service", MagicMock())
    test_container.register_service("file_system", MagicMock())
    test_container.register_service("logger", MagicMock())

    yield test_container

## Error and Exception Fixtures

@pytest.fixture(scope="function")
def mock_error_condition() -> Generator[Callable[[Exception], None], None, None]:
    """Fixture to simulate error conditions."""
    def raise_error(error_type: Exception = Exception, message: str = "Test error") -> Callable:
        def _inner():
            raise error_type(message)
        return _inner

    yield raise_error

@pytest.fixture(scope="function")
def mock_timeout() -> Generator[Callable[[float], None], None, None]:
    """Fixture to simulate timeout conditions."""
    def timeout_after(seconds: float) -> Callable:
        import time
        def _inner():
            time.sleep(seconds + 0.1)
        return _inner

    yield timeout_after

## Performance Testing Fixtures

@pytest.fixture(scope="function")
def performance_monitor() -> Generator[Callable, None, None]:
    """Fixture for monitoring test performance."""
    import time

    def monitor(func: Callable, *args, **kwargs) -> Dict[str, float]:
        start_time = time.time()
        start_mem = get_memory_usage()

        result = func(*args, **kwargs)

        end_time = time.time()
        end_mem = get_memory_usage()

        return {
            "execution_time": end_time - start_time,
            "memory_increase": end_mem - start_mem,
            "result": result
        }

    def get_memory_usage() -> float:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB

    yield monitor

## Helper Functions

def create_test_file(path: Path, size: int = 1024, content: str = None) -> Path:
    """Helper function to create test files."""
    if content is None:
        content = "A" * size
    path.write_text(content)
    return path

def create_file_structure(base_dir: Path, structure: Dict[str, Any]) -> Dict[str, Path]:
    """Helper function to create complex file structures."""
    created_files = {}

    for name, item in structure.items():
        if isinstance(item, dict):
            # It's a directory
            dir_path = base_dir / name
            dir_path.mkdir(exist_ok=True)
            created_files.update(create_file_structure(dir_path, item))
        else:
            # It's a file
            file_path = base_dir / name
            if isinstance(item, str):
                file_path.write_text(item)
            else:
                file_path.write_bytes(item)
            created_files[name] = file_path

    return created_files

## Test Configuration Hooks

def pytest_configure(config):
    """Pytest configuration hook."""
    # Add custom markers
    config.addinivalue_line(
        "markers",
        "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers",
        "stress: mark test as stress test"
    )

def pytest_collection_modifyitems(items):
    """Modify test collection order."""
    # Run performance tests last
    performance_tests = [item for item in items if "performance" in item.keywords]
    other_tests = [item for item in items if "performance" not in item.keywords]
    items[:] = other_tests + performance_tests

def pytest_runtest_setup(item):
    """Test setup hook."""
    # Add test timing information
    if "performance" in item.keywords:
        item.user_properties.append(("test_type", "performance"))
    elif "stress" in item.keywords:
        item.user_properties.append(("test_type", "stress"))
    else:
        item.user_properties.append(("test_type", "standard"))
