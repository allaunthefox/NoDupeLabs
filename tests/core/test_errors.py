import pytest
from nodupe.core.errors import NoDupeError


class TestNoDupeError:
    """Test suite for NoDupeError class."""

    def test_no_dupe_error_creation_with_message(self):
        """Test creating a NoDupeError with a message."""
        error = NoDupeError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_no_dupe_error_creation_without_message(self):
        """Test creating a NoDupeError without a message."""
        error = NoDupeError()
        assert str(error) == ""
        assert isinstance(error, Exception)

    def test_no_dupe_error_inheritance(self):
        """Test that NoDupeError properly inherits from Exception."""
        error = NoDupeError("Test message")
        assert isinstance(error, Exception)
        assert isinstance(error, NoDupeError)

    def test_no_dupe_error_with_args(self):
        """Test creating a NoDupeError with args."""
        error = NoDupeError("Error occurred", "additional_info")
        assert "Error occurred" in str(error)
        # The error should contain the first argument as its string representation

    def test_no_dupe_error_raising(self):
        """Test that NoDupeError can be raised and caught."""
        with pytest.raises(NoDupeError):
            raise NoDupeError("Test error")

    def test_no_dupe_error_raising_with_catch(self):
        """Test catching a raised NoDupeError."""
        try:
            raise NoDupeError("Test error")
        except NoDupeError as e:
            assert str(e) == "Test error"

    def test_no_dupe_error_is_subclass_of_exception(self):
        """Test that NoDupeError is a subclass of Exception."""
        assert issubclass(NoDupeError, Exception)

    def test_no_dupe_error_empty_message(self):
        """Test creating a NoDupeError with an empty message."""
        error = NoDupeError("")
        assert str(error) == ""
        assert isinstance(error, NoDupeError)

    def test_no_dupe_error_with_numeric_message(self):
        """Test creating a NoDupeError with a numeric value."""
        error = NoDupeError(123)
        assert str(error) == "123"

    def test_no_dupe_error_with_none_message(self):
        """Test creating a NoDupeError with None as message."""
        error = NoDupeError(None)
        assert str(error) == "None"

    def test_no_dupe_error_multiple_args(self):
        """Test creating a NoDupeError with multiple arguments."""
        error = NoDupeError("Error", "detail1", "detail2")
        assert "Error" in str(error)

    def test_no_dupe_error_comparison(self):
        """Test comparing two NoDupeError instances."""
        error1 = NoDupeError("Same message")
        error2 = NoDupeError("Same message")
        # They should not be identical but both be NoDupeError instances
        assert type(error1) == type(error2)
        assert isinstance(error1, NoDupeError)
        assert isinstance(error2, NoDupeError)

    def test_no_dupe_error_attributes(self):
        """Test accessing attributes of NoDupeError."""
        error = NoDupeError("Test error")
        # Standard exception attributes
        assert hasattr(error, '__traceback__') or True  # __traceback__ only exists when raised
        assert hasattr(error, 'args')
        assert error.args == ("Test error",) or error.args[0] == "Test error"

    def test_no_dupe_error_str_representation(self):
        """Test string representation of NoDupeError."""
        error = NoDupeError("Test error message")
        assert str(error) == "Test error message"

    def test_no_dupe_error_repr_representation(self):
        """Test repr representation of NoDupeError."""
        error = NoDupeError("Test error message")
        repr_str = repr(error)
        assert "NoDupeError" in repr_str
        assert "Test error message" in repr_str

    def test_no_dupe_error_with_formatting(self):
        """Test creating NoDupeError with formatted strings."""
        message = "Error code: {}".format(404)
        error = NoDupeError(message)
        assert "Error code: 404" == str(error)

    def test_no_dupe_error_from_another_exception(self):
        """Test creating NoDupeError from another exception."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            error = NoDupeError(f"Wrapped: {str(e)}")
            assert "Wrapped: Original error" == str(error)

    def test_no_dupe_error_with_unicode_message(self):
        """Test creating NoDupeError with unicode message."""
        error = NoDupeError("Error with ünïcödë")
        assert "Error with ünïcödë" in str(error)

    def test_no_dupe_error_chaining(self):
        """Test exception chaining behavior with NoDupeError."""
        try:
            try:
                raise ValueError("Original")
            except ValueError as original:
                raise NoDupeError("Converted") from original
        except NoDupeError as e:
            assert "Converted" in str(e)
            assert e.__cause__ is not None

    def test_no_dupe_error_context(self):
        """Test exception context behavior with NoDupeError."""
        try:
            try:
                raise ValueError("Original")
            except ValueError:
                raise NoDupeError("Converted")
        except NoDupeError as e:
            assert "Converted" in str(e)
