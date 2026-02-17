import json
import pytest

from nodupe.core.api.openapi import OpenAPIGenerator
from nodupe.core.api.validation import SchemaValidator, SchemaValidationError, validate_request, validate_response


def test_openapi_generator_basic_flow():
    gen = OpenAPIGenerator()
    gen.set_info("T", "0.1", "desc")
    gen.add_server("https://api.local", "local")
    gen.add_path("/ping", "GET", {"summary": "ping"})
    gen.add_schema("Ping", {"type": "object"})

    spec = gen.generate_spec()
    assert spec["openapi"] == "3.1.2"
    assert "/ping" in spec["paths"]

    js = gen.to_json(spec)
    assert isinstance(js, str)

    valid = gen.validate_spec(spec)
    assert valid["valid"] is True

    # invalid spec (missing openapi)
    bad = {"info": {}, "paths": {}}
    res = gen.validate_spec(bad)
    assert res["valid"] is False
    assert "Missing required field: openapi" in res["errors"][0]


def test_schema_validator_types_and_validate():
    sv = SchemaValidator()

    # primitive types
    assert sv._check_type("s", "string")
    assert sv._check_type(1, "integer")
    assert sv._check_type(1.0, "number")
    assert sv._check_type(True, "boolean")
    assert sv._check_type([], "array")
    assert sv._check_type({}, "object")
    assert sv._check_type(None, "null")

    # validate raises on mismatch
    with pytest.raises(SchemaValidationError):
        sv.validate({"type": "string"}, 1)

    # valid case
    assert sv.validate({"type": "integer"}, 5) is True


def test_decorators_preserve_behavior():
    @validate_request({"type": "string"})
    def f(a):
        return f"ok-{a}"

    @validate_response({"type": "string"})
    def g():
        return "resp"

    assert f("x") == "ok-x"
    assert g() == "resp"
