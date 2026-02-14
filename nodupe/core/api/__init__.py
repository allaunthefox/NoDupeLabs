# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs API Module.

This module provides the API layer functionality for NoDupeLabs, including:
- API versioning system
- OpenAPI specification generation
- Rate limiting
- Schema validation
- API decorators
"""

from .versioning import APIVersion
from .openapi import OpenAPIGenerator
from .ratelimit import RateLimiter, rate_limited
from .validation import SchemaValidator, validate_request, validate_response
from .decorators import api_endpoint, cors

__all__ = [
    'APIVersion',
    'OpenAPIGenerator',
    'RateLimiter',
    'SchemaValidator',
    'validate_request',
    'validate_response',
    'rate_limited',
    'api_endpoint',
    'cors',
]
