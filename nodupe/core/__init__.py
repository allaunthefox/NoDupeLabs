# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs Core Framework.

Provides the minimal orchestration engine for standards-compliant 
archival and backup operations.
"""

from .loader import CoreLoader, bootstrap
from .container import ServiceContainer, container
from .api.codes import ActionCode

__all__ = [
    'CoreLoader',
    'bootstrap',
    'ServiceContainer',
    'container',
    'ActionCode'
]
