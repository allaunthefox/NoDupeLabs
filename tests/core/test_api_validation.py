import pytest

from nodupe.core.api.validation import (
    SchemaValidator,
    SchemaValidationError,
    validate_request,
    validate_response,
)


def test_check_type_and_validate_success():
    v = SchemaValidator()
    assert v.validate({"type": "string"}, "hello") is True
    assert v.validate({"type": "number"}, 3.14) is True
    assert v.validate({"type": "integer"}, 3) is True
    assert v.validate({"type": "boolean"}, True) is True
    assert v.validate({"type": "array"}, [1, 2]) is True
    assert v.validate({"type": "object"}, {"a": 1}) is True
    assert v.validate({"type": "null"}, None) is True


def test_validate_raises_with_error_list_and_message():
    v = SchemaValidator()
    with pytest.raises(SchemaValidationError) as exc:
        v.validate({"type": "integer"}, "not-an-int")

    assert hasattr(exc.value, "errors")
    assert exc.value.errors


def test_validate_request_and_response_decorators_are_noops():
    @validate_request({"type": "string"})
    @validate_response({"type": "string"})
    def echo(x):
        return x

    assert echo("ok") == "ok"
