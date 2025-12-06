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
from .walker import iter_files
from .processor import process_file, FileProcessor
from .hasher import threaded_hash
from .progress import ProgressTracker

__all__ = [
    "ScanValidator",
    "ScanOrchestrator",
    "iter_files",
    "process_file",
    "FileProcessor",
    "threaded_hash",
    "ProgressTracker",
]
