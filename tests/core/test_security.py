"""Tests for security module."""

from pathlib import Path

import pytest

from nodupe.core.security import Security, SecurityError


class TestSecurity:
    """Test Security class."""

    def test_sanitize_path(self):
        """Test path sanitization."""
        # Normal path should work
        path = Security.sanitize_path("/home/user/file.txt")
        assert path is not None

    def test_sanitize_path_parent_directory(self):
        """Test sanitization rejects parent directory traversal."""
        with pytest.raises(SecurityError):
            Security.sanitize_path("../../../etc/passwd", allow_parent=False)

    def test_sanitize_path_allow_parent(self):
        """Test sanitization allows parent when enabled."""
        path = Security.sanitize_path("../file.txt", allow_parent=True)
        assert path is not None

    def test_sanitize_path_null_byte(self):
        """Test sanitization rejects null bytes."""
        with pytest.raises(SecurityError):
            Security.sanitize_path("/path/to/file\x00.txt")

    def test_validate_path(self, tmp_path):
        """Test path validation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Should pass
        assert Security.validate_path(str(test_file), must_exist=True)

    def test_validate_path_nonexistent(self, tmp_path):
        """Test validation of nonexistent path."""
        with pytest.raises(SecurityError):
            Security.validate_path(str(tmp_path / "nonexistent.txt"), must_exist=True)

    def test_validate_path_must_be_file(self, tmp_path):
        """Test validation that path must be file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        assert Security.validate_path(str(test_file), must_be_file=True)

        # Should fail for directory
        with pytest.raises(SecurityError):
            Security.validate_path(str(tmp_path), must_be_file=True)

    def test_validate_path_must_be_dir(self, tmp_path):
        """Test validation that path must be directory."""
        assert Security.validate_path(str(tmp_path), must_be_dir=True)

        # Should fail for file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        with pytest.raises(SecurityError):
            Security.validate_path(str(test_file), must_be_dir=True)

    def test_validate_path_allowed_parent(self, tmp_path):
        """Test validation with allowed parent directory."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Should pass - file is within tmp_path
        assert Security.validate_path(str(test_file), allowed_parent=tmp_path)

        # Should fail - file is outside allowed parent
        other_dir = tmp_path.parent
        with pytest.raises(SecurityError):
            Security.validate_path(str(test_file), allowed_parent=other_dir / "other")

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Normal filename
        name = Security.sanitize_filename("test.txt")
        assert name == "test.txt"

        # Invalid characters
        name = Security.sanitize_filename("test<>:file.txt")
        assert "<" not in name
        assert ">" not in name
        assert ":" not in name

    def test_sanitize_filename_reserved_names(self):
        """Test sanitization of Windows reserved names."""
        name = Security.sanitize_filename("CON.txt")
        assert name != "CON.txt"  # Should be modified

    def test_sanitize_filename_max_length(self):
        """Test filename length truncation."""
        long_name = "a" * 300 + ".txt"
        name = Security.sanitize_filename(long_name, max_length=255)
        assert len(name) <= 255

    def test_is_safe_path(self, tmp_path):
        """Test safe path checking."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Should be safe
        assert Security.is_safe_path(str(test_file), str(tmp_path))

        # Should not be safe
        other_path = tmp_path.parent / "other.txt"
        assert not Security.is_safe_path(str(other_path), str(tmp_path))

    def test_check_permissions(self, tmp_path):
        """Test permission checking."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Should have read permission
        assert Security.check_permissions(str(test_file), readable=True)

    def test_check_permissions_nonexistent(self, tmp_path):
        """Test permission check on nonexistent file."""
        with pytest.raises(SecurityError):
            Security.check_permissions(str(tmp_path / "nonexistent.txt"), readable=True)

    def test_is_symlink(self, tmp_path):
        """Test symlink detection."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Regular file is not a symlink
        assert not Security.is_symlink(str(test_file))

    def test_resolve_symlink(self, tmp_path):
        """Test symlink resolution."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        resolved = Security.resolve_symlink(str(test_file))
        assert resolved is not None

    def test_validate_extension(self):
        """Test file extension validation."""
        # Should pass
        assert Security.validate_extension("file.txt", [".txt", ".log"])
        assert Security.validate_extension("file.txt", ["txt", "log"])

        # Should fail
        with pytest.raises(SecurityError):
            Security.validate_extension("file.exe", [".txt", ".log"])

    def test_generate_safe_filename(self):
        """Test safe filename generation."""
        name = Security.generate_safe_filename("test", extension=".txt")
        assert name.endswith(".txt")
        assert name.startswith("test")

    def test_generate_safe_filename_with_timestamp(self):
        """Test safe filename generation with timestamp."""
        name = Security.generate_safe_filename("test", extension=".txt", add_timestamp=True)
        assert name.endswith(".txt")
        assert "test" in name
        # Should contain timestamp pattern (numbers)
        assert any(c.isdigit() for c in name)
