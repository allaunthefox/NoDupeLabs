"""Validators Module.

Input validation utilities using standard library only.

Key Features:
    - Type validation
    - Range validation
    - String validation (length, pattern)
    - Path validation
    - Collection validation
    - Standard library only (no external dependencies)

Dependencies:
    - typing (standard library)
    - re (standard library)
"""

import re
from pathlib import Path
from typing import Any, Optional, Union


class ValidationError(Exception):
    """Validation error"""


class Validators:
    """Handle input validation.

    Provides comprehensive validation utilities for type checking,
    range validation, string validation, and more.
    """

    @staticmethod
    def validate_type(
        value: Any, expected_type: type, allow_none: bool = False
    ) -> bool:
        """Validate type.

        Args:
            value: Value to validate
            expected_type: Expected type
            allow_none: If True, None is allowed

        Returns:
            True if type is valid

        Raises:
            ValidationError: If type is invalid
        """
        if value is None and allow_none:
            return True

        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Expected type {expected_type.__name__}, got {type(value).__name__}"
            )

        return True

    @staticmethod
    def validate_range(
        value: Union[int, float],
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        inclusive: bool = True,
    ) -> bool:
        """Validate range.

        Args:
            value: Value to validate
            min_val: Minimum value (None = no minimum)
            max_val: Maximum value (None = no maximum)
            inclusive: If True, range is inclusive

        Returns:
            True if value is in range

        Raises:
            ValidationError: If value is out of range
        """
        # Validate type
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"Expected numeric type, got {type(value).__name__}"
            )

        # Check minimum
        if min_val is not None:
            if inclusive:
                if value < min_val:
                    raise ValidationError(f"Value {value} < minimum {min_val}")
            elif value <= min_val:
                raise ValidationError(f"Value {value} <= minimum {min_val}")

        # Check maximum
        if max_val is not None:
            if inclusive:
                if value > max_val:
                    raise ValidationError(f"Value {value} > maximum {max_val}")
            elif value >= max_val:
                raise ValidationError(f"Value {value} >= maximum {max_val}")

        return True

    @staticmethod
    def validate_string_length(
        value: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> bool:
        """Validate string length.

        Args:
            value: String to validate
            min_length: Minimum length (None = no minimum)
            max_length: Maximum length (None = no maximum)

        Returns:
            True if string length is valid

        Raises:
            ValidationError: If string length is invalid
        """
        # Validate type
        if not isinstance(value, str):
            raise ValidationError(
                f"Expected string, got {type(value).__name__}"
            )

        length = len(value)

        # Check minimum length
        if min_length is not None and length < min_length:
            raise ValidationError(
                f"String length {length} < minimum {min_length}"
            )

        # Check maximum length
        if max_length is not None and length > max_length:
            raise ValidationError(
                f"String length {length} > maximum {max_length}"
            )

        return True

    @staticmethod
    def validate_pattern(value: str, pattern: str) -> bool:
        """Validate string against regex pattern.

        Args:
            value: String to validate
            pattern: Regex pattern

        Returns:
            True if string matches pattern

        Raises:
            ValidationError: If string doesn't match pattern
        """
        # Validate type
        if not isinstance(value, str):
            raise ValidationError(
                f"Expected string, got {type(value).__name__}"
            )

        # Compile and match pattern
        try:
            regex = re.compile(pattern)
            if not regex.match(value):
                raise ValidationError(
                    f"String '{value}' doesn't match pattern '{pattern}'"
                )
        except re.error as e:
            raise ValidationError(
                f"Invalid regex pattern '{pattern}': {e}"
            ) from e

        return True

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address.

        Args:
            email: Email address to validate

        Returns:
            True if email is valid

        Raises:
            ValidationError: If email is invalid
        """
        # Simple email validation regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return Validators.validate_pattern(email, email_pattern)

    @staticmethod
    def validate_path(
        file_path: Union[str, Path],
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
    ) -> bool:
        """Validate file path.

        Args:
            file_path: Path to validate
            must_exist: If True, path must exist
            must_be_file: If True, path must be a file
            must_be_dir: If True, path must be a directory

        Returns:
            True if path is valid

        Raises:
            ValidationError: If path is invalid
        """
        # Convert to Path
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not isinstance(file_path, Path):
            raise ValidationError(
                f"Expected Path or str, got {type(file_path).__name__}"
            )

        # Check existence
        if must_exist and not file_path.exists():
            raise ValidationError(f"Path does not exist: {file_path}")

        # Check if file
        if must_be_file:
            if not file_path.exists():
                raise ValidationError(f"File does not exist: {file_path}")
            if not file_path.is_file():
                raise ValidationError(f"Path is not a file: {file_path}")

        # Check if directory
        if must_be_dir:
            if not file_path.exists():
                raise ValidationError(f"Directory does not exist: {file_path}")
            if not file_path.is_dir():
                raise ValidationError(f"Path is not a directory: {file_path}")

        return True

    @staticmethod
    def validate_enum(value: Any, allowed_values: list[Any]) -> bool:
        """Validate value is in allowed list.

        Args:
            value: Value to validate
            allowed_values: List of allowed values

        Returns:
            True if value is allowed

        Raises:
            ValidationError: If value is not allowed
        """
        if value not in allowed_values:
            raise ValidationError(
                f"Value '{value}' not in allowed values: {allowed_values}"
            )

        return True

    @staticmethod
    def validate_dict_keys(
        data: dict,
        required_keys: Optional[list[str]] = None,
        allowed_keys: Optional[list[str]] = None,
    ) -> bool:
        """Validate dictionary keys.

        Args:
            data: Dictionary to validate
            required_keys: List of required keys
            allowed_keys: List of allowed keys (None = any keys allowed)

        Returns:
            True if dictionary keys are valid

        Raises:
            ValidationError: If dictionary keys are invalid
        """
        # Validate type
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict, got {type(data).__name__}")

        # Check required keys
        if required_keys is not None:
            missing_keys = set(required_keys) - set(data.keys())
            if missing_keys:
                raise ValidationError(f"Missing required keys: {missing_keys}")

        # Check allowed keys
        if allowed_keys is not None:
            extra_keys = set(data.keys()) - set(allowed_keys)
            if extra_keys:
                raise ValidationError(f"Unexpected keys: {extra_keys}")

        return True

    @staticmethod
    def validate_list_items(
        items: list,
        item_type: type,
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> bool:
        """Validate list items.

        Args:
            items: List to validate
            item_type: Expected type of items
            min_items: Minimum number of items
            max_items: Maximum number of items

        Returns:
            True if list items are valid

        Raises:
            ValidationError: If list items are invalid
        """
        # Validate type
        if not isinstance(items, list):
            raise ValidationError(f"Expected list, got {type(items).__name__}")

        # Check item count
        item_count = len(items)

        if min_items is not None and item_count < min_items:
            raise ValidationError(
                f"List has {item_count} items, minimum is {min_items}"
            )

        if max_items is not None and item_count > max_items:
            raise ValidationError(
                f"List has {item_count} items, maximum is {max_items}"
            )

        # Check item types
        for i, item in enumerate(items):
            if not isinstance(item, item_type):
                raise ValidationError(
                    f"Item {i} has type {type(item).__name__}, "
                    f"expected {item_type.__name__}"
                )

        return True

    @staticmethod
    def validate_boolean(value: Any) -> bool:
        """Validate boolean value.

        Args:
            value: Value to validate

        Returns:
            True if value is boolean

        Raises:
            ValidationError: If value is not boolean
        """
        if not isinstance(value, bool):
            raise ValidationError(f"Expected bool, got {type(value).__name__}")

        return True

    @staticmethod
    def validate_positive(value: Union[int, float]) -> bool:
        """Validate value is positive.

        Args:
            value: Value to validate

        Returns:
            True if value is positive

        Raises:
            ValidationError: If value is not positive
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"Expected numeric type, got {type(value).__name__}"
            )

        if value <= 0:
            raise ValidationError(f"Value {value} is not positive")

        return True

    @staticmethod
    def validate_non_negative(value: Union[int, float]) -> bool:
        """Validate value is non-negative.

        Args:
            value: Value to validate

        Returns:
            True if value is non-negative

        Raises:
            ValidationError: If value is negative
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"Expected numeric type, got {type(value).__name__}"
            )

        if value < 0:
            raise ValidationError(f"Value {value} is negative")

        return True

    @staticmethod
    def validate_non_empty(value: Union[str, list, dict, set, tuple]) -> bool:
        """Validate value is not empty.

        Args:
            value: Value to validate

        Returns:
            True if value is not empty

        Raises:
            ValidationError: If value is empty
        """
        if not value:
            raise ValidationError("Value is empty")

        return True
