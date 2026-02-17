# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File processing layer for NoDupeLabs.

This module provides file scanning and processing functionality for the NoDupeLabs project,
including file discovery, metadata extraction, and duplicate detection.

Key Features:
    - File system traversal
    - File metadata extraction
    - Cryptographic hashing
    - Progress tracking
    - Incremental scanning

Dependencies:
    - Standard library only
"""

from .file_info import FileInfo
from .incremental import Incremental
from .processor import FileProcessor, create_file_processor
from .progress import ProgressTracker
from .walker import FileWalker, create_file_walker

__all__ = [
    "FileInfo",
    "FileProcessor",
    "FileWalker",
    "Incremental",
    "ProgressTracker",
    "create_file_processor",
    "create_file_walker",
]
