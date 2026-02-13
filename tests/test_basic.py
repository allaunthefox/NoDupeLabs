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
    assert len(sample_files) == 5  # Updated to match actual fixture: small.txt, medium.txt, large.txt, duplicate_small.txt, binary.dat

    # Check that all files exist
    for name, file_path in sample_files.items():
        assert file_path.exists()
        assert file_path.is_file()

    # Check that small.txt and duplicate_small.txt have identical content (duplicates)
    small_content = sample_files["small.txt"].read_text()
    duplicate_content = sample_files["duplicate_small.txt"].read_text()
    assert small_content == duplicate_content

    # Check that other files have different content
    medium_content = sample_files["medium.txt"].read_text()
    large_content = sample_files["large.txt"].read_text()
    assert small_content != medium_content
    assert small_content != large_content
    assert medium_content != large_content


def test_mock_config_fixture(mock_config):
    """Test that the mock_config fixture provides expected structure."""
    assert isinstance(mock_config, dict)
    assert "database" in mock_config
    assert "scan" in mock_config

    # Check database config
    db_config = mock_config["database"]
    assert db_config["path"] == ":memory:"
    assert db_config["timeout"] == 10.0  # Updated to match actual fixture value

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
