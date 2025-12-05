# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Scanning subsystem.

Provides reusable classes for file processing and progress tracking.

Public API:
    - FileProcessor: Process individual files with hashing/metadata
    - ProgressTracker: Monitor scan progress and detect stalls
    - FileRecord: Type alias for file record tuple
"""
from .file_processor import FileProcessor, FileRecord
from .progress import ProgressTracker

__all__ = [
    "FileProcessor",
    "FileRecord",
    "ProgressTracker",
]
