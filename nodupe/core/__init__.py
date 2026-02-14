# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs Core Module.

This module provides the core functionality with hard isolation
from optional dependencies.

Key Features:
    - Minimal core loader
    - Plugin management
    - Dependency injection
    - Graceful degradation

Dependencies:
    - Standard library only
"""

from .loader import CoreLoader, bootstrap
from .main import main
from .container import ServiceContainer, container

# Utility modules
from .mmap_handler import MMAPHandler
from .incremental import Incremental
# New API package
from .api import (
    APIVersion,
    OpenAPIGenerator,
    RateLimiter,
    SchemaValidator,
    rate_limited,
    validate_request,
    validate_response,
    api_endpoint,
    cors,
)


__all__ = [
    # Core
    'CoreLoader',
    'bootstrap',
    'main',
    'ServiceContainer',
    'container',
    # Utilities
    'MMAPHandler',
    'Incremental',
    # API
    'APIVersion',
    'OpenAPIGenerator',
    'RateLimiter',
    'SchemaValidator',
    'rate_limited',
    'validate_request',
    'validate_response',
    'api_endpoint',
    'cors',
]
