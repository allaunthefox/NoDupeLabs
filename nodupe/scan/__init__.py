# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Scan subsystem.

Provides file scanning functionality with validation, orchestration,
and result export.

Public API:
    - ScanValidator: Validates scan preconditions
    - ScanOrchestrator: Coordinates scan workflow
"""

from .validator import ScanValidator
from .orchestrator import ScanOrchestrator

__all__ = ["ScanValidator", "ScanOrchestrator"]
