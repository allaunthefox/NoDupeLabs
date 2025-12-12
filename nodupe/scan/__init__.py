# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Scan subsystem.

Provides comprehensive file scanning functionality including validation,
orchestration, parallel processing, and result export. This subsystem
forms the core of NoDupeLabs' file discovery and metadata extraction
capabilities.

Key Features:
    - Recursive directory scanning with pattern matching
    - Parallel file processing and hashing
    - Incremental scanning with change detection
    - Comprehensive validation and error handling
    - AI embeddings computation (optional)
    - Metadata export and persistence

Public API:
    - ScanValidator: Validates scan preconditions
    - ScanOrchestrator: Coordinates complete scan workflow
    - iter_files: Recursive file discovery generator
    - process_file: Individual file processing function
    - FileProcessor: File processing class
    - threaded_hash: Parallel hashing function
    - ProgressTracker: Scan progress monitoring

Dependencies:
    - Required: pathlib, threading, hashlib
    - Optional: AI backends for embeddings

Usage Example:
    >>> from nodupe.scan import ScanOrchestrator, ScanValidator
    >>> from nodupe.db import DB
    >>> from nodupe.telemetry import Telemetry
    >>> validator = ScanValidator()
    >>> is_valid, errors = validator.validate(roots=["/path/to/scan"])
    >>> if is_valid:
    ...     orchestrator = ScanOrchestrator(db, telemetry, backend, pm)
    ...     results = orchestrator.scan(roots=["/path/to/scan"])
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
