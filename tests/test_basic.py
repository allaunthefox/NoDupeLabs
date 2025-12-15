"""
Basic tests for NoDupeLabs functionality.
"""
import pytest
from pathlib import Path


def test_temp_dir_fixture(temp_dir):
    """Test that the temp_dir fixture works correctly."""
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    # Test that we can create files in the temp directory
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()
    assert test_file.read_text() == "test content"


def test_sample_files_fixture(sample_files):
    """Test that the sample_files fixture creates files correctly."""
    assert len(sample_files) == 4  # 3 duplicate files + 1 unique file
    
    # Check that all files exist
    for file_path in sample_files:
        assert file_path.exists()
        assert file_path.is_file()
    
    # Check that the first 3 files have identical content (duplicates)
    content_0 = sample_files[0].read_text()
    content_1 = sample_files[1].read_text()
    content_2 = sample_files[2].read_text()
    
    assert content_0 == content_1 == content_2
    assert "duplicate detection" in content_0
    
    # Check that the last file is unique
    unique_content = sample_files[3].read_text()
    assert "unique file" in unique_content
    assert unique_content != content_0


def test_mock_config_fixture(mock_config):
    """Test that the mock_config fixture provides expected structure."""
    assert isinstance(mock_config, dict)
    assert "database" in mock_config
    assert "scan" in mock_config
    
    # Check database config
    db_config = mock_config["database"]
    assert db_config["path"] == ":memory:"
    assert db_config["timeout"] == 30.0
    
    # Check scan config
    scan_config = mock_config["scan"]
    assert "min_file_size" in scan_config
    assert "max_file_size" in scan_config
    assert isinstance(scan_config["default_extensions"], list)


def test_nodupe_import():
    """Test that we can import the main nodupe module."""
    try:
        import nodupe
        assert nodupe is not None
    except ImportError:
        pytest.skip("nodupe module not available for import testing")


if __name__ == "__main__":
    pytest.main([__file__])
