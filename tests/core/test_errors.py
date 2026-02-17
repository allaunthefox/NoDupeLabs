"""Test errors module functionality."""

import pytest

from nodupe.core.errors import (
    DatabaseError,
    NoDupeError,
    SecurityError,
    ToolError,
    ValidationError,
)


class TestErrorHierarchy:
    """Test error class hierarchy."""

    def test_nodupe_error_base(self):
        """Test NoDupeError base class."""
        assert issubclass(NoDupeError, Exception)
        assert NoDupeError.__name__ == "NoDupeError"

        # Test instantiation
        error = NoDupeError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
        assert isinstance(error, NoDupeError)

    def test_security_error(self):
        """Test SecurityError class."""
        assert issubclass(SecurityError, NoDupeError)
        assert issubclass(SecurityError, Exception)
        assert SecurityError.__name__ == "SecurityError"

        # Test instantiation
        error = SecurityError("Security violation")
        assert str(error) == "Security violation"
        assert isinstance(error, NoDupeError)
        assert isinstance(error, Exception)

    def test_validation_error(self):
        """Test ValidationError class."""
        assert issubclass(ValidationError, NoDupeError)
        assert issubclass(ValidationError, Exception)
        assert ValidationError.__name__ == "ValidationError"

        # Test instantiation
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert isinstance(error, NoDupeError)
        assert isinstance(error, Exception)

    def test_tool_error(self):
        """Test ToolError class."""
        assert issubclass(ToolError, NoDupeError)
        assert issubclass(ToolError, Exception)
        assert ToolError.__name__ == "ToolError"

        # Test instantiation
        error = ToolError("Tool failed")
        assert str(error) == "Tool failed"
        assert isinstance(error, NoDupeError)
        assert isinstance(error, Exception)

    def test_database_error(self):
        """Test DatabaseError class."""
        assert issubclass(DatabaseError, NoDupeError)
        assert issubclass(DatabaseError, Exception)
        assert DatabaseError.__name__ == "DatabaseError"

        # Test instantiation
        error = DatabaseError("Database connection failed")
        assert str(error) == "Database connection failed"
        assert isinstance(error, NoDupeError)
        assert isinstance(error, Exception)


class TestErrorUsage:
    """Test error usage scenarios."""

    def test_error_raising_and_catching(self):
        """Test raising and catching errors."""
        # Test raising and catching base error
        with pytest.raises(NoDupeError):
            raise NoDupeError("Base error")

        # Test raising and catching specific error
        with pytest.raises(SecurityError):
            raise SecurityError("Security error")

        # Test catching base class catches specific errors
        with pytest.raises(NoDupeError):
            raise ValidationError("Validation error")

    def test_error_with_context(self):
        """Test errors with additional context."""
        try:
            raise ValidationError("Invalid email format")
        except ValidationError as e:
            assert str(e) == "Invalid email format"
            assert isinstance(e, NoDupeError)

    def test_error_chaining(self):
        """Test error chaining."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ValidationError("Validation failed") from e
        except ValidationError as e:
            assert str(e) == "Validation failed"
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "Original error"


class TestErrorIntegration:
    """Test error integration scenarios."""

    def test_error_in_function(self):
        """Test using errors in functions."""

        def validate_input(value):
            if not value:
                raise ValidationError("Input cannot be empty")
            return value

        # Test successful case
        result = validate_input("valid")
        assert result == "valid"

        # Test error case
        with pytest.raises(ValidationError):
            validate_input("")

    def test_error_in_class_method(self):
        """Test using errors in class methods."""

        class UserService:
            def validate_user(self, username):
                if not username:
                    raise ValidationError("Username cannot be empty")
                if len(username) < 3:
                    raise ValidationError("Username too short")
                return username

        service = UserService()

        # Test successful case
        result = service.validate_user("validuser")
        assert result == "validuser"

        # Test error cases
        with pytest.raises(ValidationError):
            service.validate_user("")

        with pytest.raises(ValidationError):
            service.validate_user("ab")

    def test_error_in_tool_system(self):
        """Test using errors in tool system."""

        class MockTool:
            def __init__(self, name):
                if not name:
                    raise ToolError("Tool name cannot be empty")
                self.name = name

            def execute(self):
                if not hasattr(self, "initialized"):
                    raise ToolError("Tool not initialized")
                return f"Tool {self.name} executed"

        # Test successful tool
        tool = MockTool("test_tool")
        tool.initialized = True
        result = tool.execute()
        assert result == "Tool test_tool executed"

        # Test tool error
        with pytest.raises(ToolError):
            MockTool("")

        # Test tool execution error
        tool_no_init = MockTool("test_tool")
        with pytest.raises(ToolError):
            tool_no_init.execute()


class TestErrorProperties:
    """Test error properties and attributes."""

    def test_error_args(self):
        """Test error args attribute."""
        error = ValidationError("Error message", "additional_info")
        assert error.args == ("Error message", "additional_info")
        assert str(error) == "('Error message', 'additional_info')"

    def test_error_repr(self):
        """Test error repr."""
        error = SecurityError("Security breach")
        repr_str = repr(error)
        assert "SecurityError" in repr_str
        assert "Security breach" in repr_str

    def test_error_with_custom_attributes(self):
        """Test errors with custom attributes."""
        error = DatabaseError("Connection failed")
        error.connection_string = "db://localhost"
        error.retry_count = 3

        assert error.connection_string == "db://localhost"
        assert error.retry_count == 3
        assert str(error) == "Connection failed"


class TestErrorHierarchyVerification:
    """Test error hierarchy verification."""

    def test_all_errors_inherit_from_nodupe_error(self):
        """Test that all custom errors inherit from NoDupeError."""
        error_classes = [
            SecurityError,
            ValidationError,
            ToolError,
            DatabaseError,
        ]

        for error_class in error_classes:
            assert issubclass(error_class, NoDupeError)
            assert issubclass(error_class, Exception)

            # Test instantiation
            error = error_class("Test")
            assert isinstance(error, NoDupeError)
            assert isinstance(error, Exception)

    def test_error_isinstance_checks(self):
        """Test isinstance checks for error hierarchy."""
        errors = [
            NoDupeError("base"),
            SecurityError("security"),
            ValidationError("validation"),
            ToolError("tool"),
            DatabaseError("database"),
        ]

        for error in errors:
            assert isinstance(error, NoDupeError)
            assert isinstance(error, Exception)

        # Test specific isinstance checks
        assert isinstance(errors[1], SecurityError)
        assert isinstance(errors[2], ValidationError)
        assert isinstance(errors[3], ToolError)
        assert isinstance(errors[4], DatabaseError)
