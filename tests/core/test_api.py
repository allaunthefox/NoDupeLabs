# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Test API module functionality."""

import pytest

from nodupe.core.api import (
    APIVersion,
    OpenAPIGenerator,
    RateLimiter,
    SchemaValidator,
    api_endpoint,
    cors,
    rate_limited,
    validate_request,
    validate_response,
)


class TestAPIVersion:
    """Test APIVersion class."""

    def test_init_default_version(self):
        """Test API version initialization with default."""
        api = APIVersion()
        assert api.current_version == "v1"
        assert "v1" in api.supported_versions

    def test_register_version(self):
        """Test registering a new version."""
        api = APIVersion()
        api.register_version("v2")
        assert "v2" in api.supported_versions

    def test_set_current_version(self):
        """Test setting current version."""
        api = APIVersion()
        api.register_version("v2")
        api.set_current_version("v2")
        assert api.current_version == "v2"

    def test_set_current_version_invalid(self):
        """Test setting invalid version raises error."""
        api = APIVersion()
        with pytest.raises(ValueError):
            api.set_current_version("v999")

    def test_deprecate_version(self):
        """Test deprecating a version."""
        api = APIVersion()
        api.deprecate_version("v1", "v2")
        assert api.is_version_deprecated("v1")

    def test_is_version_supported(self):
        """Test checking version support."""
        api = APIVersion()
        assert api.is_version_supported("v1") is True
        assert api.is_version_supported("v999") is False

    def test_get_deprecation_message(self):
        """Test getting deprecation message."""
        api = APIVersion()
        api.deprecate_version("v1", "v2")
        msg = api.get_deprecation_message("v1")
        assert "v1" in msg
        assert "v2" in msg


class TestOpenAPIGenerator:
    """Test OpenAPIGenerator class."""

    def test_init(self):
        """Test OpenAPI generator initialization."""
        gen = OpenAPIGenerator()
        assert gen.openapi_version == "3.1.2"
        assert gen.info["title"] == "NoDupeLabs API"

    def test_set_info(self):
        """Test setting API info."""
        gen = OpenAPIGenerator()
        gen.set_info("Test API", "2.0.0", "Test description")
        assert gen.info["title"] == "Test API"
        assert gen.info["version"] == "2.0.0"
        assert gen.info["description"] == "Test description"

    def test_add_server(self):
        """Test adding server."""
        gen = OpenAPIGenerator()
        gen.add_server("https://api.example.com", "Production")
        assert len(gen.servers) == 1
        assert gen.servers[0]["url"] == "https://api.example.com"

    def test_add_path(self):
        """Test adding path."""
        gen = OpenAPIGenerator()
        gen.add_path("/users", "get", {"200": {"description": "Success"}})
        assert "/users" in gen.paths
        assert "get" in gen.paths["/users"]

    def test_add_schema(self):
        """Test adding schema."""
        gen = OpenAPIGenerator()
        gen.add_schema("User", {"type": "object", "properties": {}})
        assert "User" in gen.components["schemas"]

    def test_generate_spec(self):
        """Test generating spec."""
        gen = OpenAPIGenerator()
        spec = gen.generate_spec()
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec

    def test_to_json(self):
        """Test converting to JSON."""
        gen = OpenAPIGenerator()
        json_str = gen.to_json()
        assert "openapi" in json_str

    def test_validate_spec_valid(self):
        """Test validating valid spec."""
        gen = OpenAPIGenerator()
        result = gen.validate_spec()
        assert result["valid"] is True
        assert len(result["errors"]) == 0


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_minute=60)
        assert limiter.requests_per_minute == 60

    def test_check_rate_limit_first_request(self):
        """Test first request is allowed."""
        limiter = RateLimiter(requests_per_minute=60)
        assert limiter.check_rate_limit("client1") is True

    def test_check_rate_limit_under_limit(self):
        """Test requests under limit are allowed."""
        limiter = RateLimiter(requests_per_minute=5)
        for _ in range(5):
            assert limiter.check_rate_limit("client1") is True

    def test_check_rate_limit_over_limit(self):
        """Test requests over limit are blocked."""
        limiter = RateLimiter(requests_per_minute=2)
        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client1")
        # Third request should be blocked
        assert limiter.check_rate_limit("client1") is False

    def test_throttle_returns_wait_time(self):
        """Test throttle returns wait time."""
        limiter = RateLimiter(requests_per_minute=1)
        limiter.check_rate_limit("client1")
        wait = limiter.throttle("client1")
        assert wait >= 0


class TestRateLimitedDecorator:
    """Test rate_limited decorator."""

    def test_decorator_allows_requests(self):
        """Test decorator allows requests under limit."""

        @rate_limited(requests_per_minute=60)
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"


class TestSchemaValidator:
    """Test SchemaValidator class."""

    def test_init(self):
        """Test validator initialization."""
        validator = SchemaValidator()
        assert validator.strict_mode is False

    def test_validate_string(self):
        """Test validating string type."""
        validator = SchemaValidator()
        result = validator.validate({"type": "string"}, "hello")
        assert result is True

    def test_validate_integer(self):
        """Test validating integer type."""
        validator = SchemaValidator()
        result = validator.validate({"type": "integer"}, 42)
        assert result is True

    def test_validate_invalid_type(self):
        """Test validating invalid type raises error."""
        validator = SchemaValidator()
        with pytest.raises(Exception):
            validator.validate({"type": "string"}, 42)


class TestApiEndpointDecorator:
    """Test api_endpoint decorator."""

    def test_decorator_basic(self):
        """Test basic decorator functionality."""

        @api_endpoint()
        def test_func():
            return "test"

        result = test_func()
        assert result == "test"


class TestCorsDecorator:
    """Test cors decorator."""

    def test_decorator_adds_cors_headers(self):
        """Test decorator adds CORS headers."""

        @cors(origins=["https://example.com"])
        def test_func():
            return {"data": "test"}

        result = test_func()
        assert "_cors" in result
        assert "Access-Control-Allow-Origin" in result["_cors"]


class TestAPIIntegration:
    """Test API integration scenarios."""

    def test_complete_versioning_workflow(self):
        """Test complete API versioning workflow."""
        api = APIVersion()

        # Register versions
        api.register_version("v1")
        api.register_version("v2")

        # Set current
        api.set_current_version("v2")

        # Deprecate old
        api.deprecate_version("v1", "v2")

        # Verify
        assert api.is_version_supported("v1")
        assert api.is_version_supported("v2")
        assert api.is_version_deprecated("v1")
        assert api.get_deprecation_message("v1") != ""

    def test_complete_openapi_workflow(self):
        """Test complete OpenAPI generation workflow."""
        gen = OpenAPIGenerator()

        # Configure
        gen.set_info("Test API", "1.0.0", "Test")
        gen.add_server("https://api.test.com")
        gen.add_path("/users", "get", {"200": {"description": "List users"}})
        gen.add_schema("User", {"type": "object"})

        # Generate
        gen.generate_spec()

        # Validate
        result = gen.validate_spec()
        assert result["valid"] is True

    def test_rate_limiting_workflow(self):
        """Test complete rate limiting workflow."""
        limiter = RateLimiter(requests_per_minute=3)

        # First 3 should pass
        assert limiter.check_rate_limit("client1") is True
        assert limiter.check_rate_limit("client1") is True
        assert limiter.check_rate_limit("client1") is True

        # 4th should fail
        assert limiter.check_rate_limit("client1") is False

        # Different client should pass
        assert limiter.check_rate_limit("client2") is True
