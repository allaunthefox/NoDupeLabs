# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs Core Framework.

Provides the minimal orchestration engine for standards-compliant
archival and backup operations.
"""

from .api.codes import ActionCode
from .container import ServiceContainer, container
from .loader import CoreLoader, bootstrap

__all__ = [
    "ActionCode",
    "CoreLoader",
    "ServiceContainer",
    "bootstrap",
    "container",
]
