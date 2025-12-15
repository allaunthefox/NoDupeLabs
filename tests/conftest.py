"""
Test configuration and fixtures for NoDupeLabs.
"""
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing duplicate detection."""
    # Create some test files
    files = []
    
    # Create identical files
    content = "This is a test file content for duplicate detection."
    for i in range(3):
        file_path = temp_dir / f"test_file_{i}.txt"
        file_path.write_text(content)
        files.append(file_path)
    
    # Create a unique file
    unique_file = temp_dir / "unique_file.txt"
    unique_file.write_text("This is a unique file content.")
    files.append(unique_file)
    
    return files


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "database": {
            "path": ":memory:",
            "timeout": 30.0,
            "journal_mode": "WAL"
        },
        "scan": {
            "min_file_size": "1KB",
            "max_file_size": "100MB",
            "default_extensions": ["jpg", "png", "pdf", "docx", "txt"],
            "exclude_dirs": [".git", ".venv", "node_modules"]
        }
    }
