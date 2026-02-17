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

from .decorators import api_endpoint, cors
from .openapi import OpenAPIGenerator
from .ratelimit import RateLimiter, rate_limited
from .validation import SchemaValidator, validate_request, validate_response
from .versioning import APIVersion


__all__ = [
    'APIVersion',
    'OpenAPIGenerator',
    'RateLimiter',
    'SchemaValidator',
    'api_endpoint',
    'cors',
    'rate_limited',
    'validate_request',
    'validate_response',
]
