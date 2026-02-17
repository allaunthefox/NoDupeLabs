"""Tests for validators module."""

from pathlib import Path

import pytest

from nodupe.tools.security_audit.validator_logic import (
    ValidationError,
    Validators,
)


class TestValidators:
    """Test Validators class."""

    def test_validate_type(self):
        """Test type validation."""
        # Should pass
        assert Validators.validate_type("test", str)
        assert Validators.validate_type(42, int)
        assert Validators.validate_type(3.14, float)
        assert Validators.validate_type([], list)

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_type("test", int)

    def test_validate_type_allow_none(self):
        """Test type validation with None allowed."""
        assert Validators.validate_type(None, str, allow_none=True)

        with pytest.raises(ValidationError):
            Validators.validate_type(None, str, allow_none=False)

    def test_validate_range(self):
        """Test range validation."""
        # Should pass
        assert Validators.validate_range(5, min_val=0, max_val=10)
        assert Validators.validate_range(0, min_val=0, max_val=10)
        assert Validators.validate_range(10, min_val=0, max_val=10)

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_range(-1, min_val=0, max_val=10)

        with pytest.raises(ValidationError):
            Validators.validate_range(11, min_val=0, max_val=10)

    def test_validate_range_exclusive(self):
        """Test exclusive range validation."""
        # Exclusive range
        assert Validators.validate_range(
            5, min_val=0, max_val=10, inclusive=False
        )

        with pytest.raises(ValidationError):
            Validators.validate_range(0, min_val=0, max_val=10, inclusive=False)

        with pytest.raises(ValidationError):
            Validators.validate_range(
                10, min_val=0, max_val=10, inclusive=False
            )

    def test_validate_string_length(self):
        """Test string length validation."""
        # Should pass
        assert Validators.validate_string_length(
            "test", min_length=1, max_length=10
        )
        assert Validators.validate_string_length(
            "test", min_length=4, max_length=4
        )

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_string_length("test", min_length=5)

        with pytest.raises(ValidationError):
            Validators.validate_string_length("test", max_length=3)

    def test_validate_pattern(self):
        """Test pattern validation."""
        # Should pass
        assert Validators.validate_pattern("test123", r"^[a-z]+[0-9]+$")
        assert Validators.validate_pattern("abc", r"^[a-z]+$")

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_pattern("test123", r"^[a-z]+$")

    def test_validate_email(self):
        """Test email validation."""
        # Should pass
        assert Validators.validate_email("user@example.com")
        assert Validators.validate_email("test.user@domain.co.uk")

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_email("invalid-email")

        with pytest.raises(ValidationError):
            Validators.validate_email("@example.com")

    def test_validate_path(self, tmp_path):
        """Test path validation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Should pass
        assert Validators.validate_path(test_file, must_exist=True)
        assert Validators.validate_path(test_file, must_be_file=True)
        assert Validators.validate_path(tmp_path, must_be_dir=True)

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_path(
                tmp_path / "nonexistent.txt", must_exist=True
            )

    def test_validate_enum(self):
        """Test enum validation."""
        # Should pass
        assert Validators.validate_enum("apple", ["apple", "banana", "orange"])
        assert Validators.validate_enum(1, [1, 2, 3])

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_enum("grape", ["apple", "banana", "orange"])

    def test_validate_dict_keys(self):
        """Test dictionary key validation."""
        data = {"name": "test", "age": 25}

        # Should pass
        assert Validators.validate_dict_keys(data, required_keys=["name"])
        assert Validators.validate_dict_keys(
            data, required_keys=["name", "age"]
        )
        assert Validators.validate_dict_keys(
            data, allowed_keys=["name", "age", "email"]
        )

        # Should fail - missing required keys
        with pytest.raises(ValidationError):
            Validators.validate_dict_keys(data, required_keys=["name", "email"])

        # Should fail - extra keys not allowed
        with pytest.raises(ValidationError):
            Validators.validate_dict_keys(data, allowed_keys=["name"])

    def test_validate_list_items(self):
        """Test list item validation."""
        # Should pass
        assert Validators.validate_list_items([1, 2, 3], int)
        assert Validators.validate_list_items(
            ["a", "b"], str, min_items=2, max_items=2
        )

        # Should fail - wrong type
        with pytest.raises(ValidationError):
            Validators.validate_list_items([1, "2", 3], int)

        # Should fail - too few items
        with pytest.raises(ValidationError):
            Validators.validate_list_items([1], int, min_items=2)

        # Should fail - too many items
        with pytest.raises(ValidationError):
            Validators.validate_list_items([1, 2, 3], int, max_items=2)

    def test_validate_boolean(self):
        """Test boolean validation."""
        # Should pass
        assert Validators.validate_boolean(True)
        assert Validators.validate_boolean(False)

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_boolean(1)

        with pytest.raises(ValidationError):
            Validators.validate_boolean("true")

    def test_validate_positive(self):
        """Test positive number validation."""
        # Should pass
        assert Validators.validate_positive(1)
        assert Validators.validate_positive(0.1)

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_positive(0)

        with pytest.raises(ValidationError):
            Validators.validate_positive(-1)

    def test_validate_non_negative(self):
        """Test non-negative number validation."""
        # Should pass
        assert Validators.validate_non_negative(0)
        assert Validators.validate_non_negative(1)

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_non_negative(-1)

    def test_validate_non_empty(self):
        """Test non-empty validation."""
        # Should pass
        assert Validators.validate_non_empty("test")
        assert Validators.validate_non_empty([1, 2, 3])
        assert Validators.validate_non_empty({"key": "value"})

        # Should fail
        with pytest.raises(ValidationError):
            Validators.validate_non_empty("")

        with pytest.raises(ValidationError):
            Validators.validate_non_empty([])

        with pytest.raises(ValidationError):
            Validators.validate_non_empty({})
