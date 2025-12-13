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

from .walker import FileWalker
from .processor import FileProcessor
from .hasher import FileHasher
from .progress import ProgressTracker

__all__ = [
    'FileWalker',
    'FileProcessor',
    'FileHasher',
    'ProgressTracker'
]
