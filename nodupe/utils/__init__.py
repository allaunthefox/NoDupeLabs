# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Utility functions and helpers.

This package contains shared utility modules used across the application.
It includes helpers for filesystem operations, media processing,
hashing, and external process management (FFmpeg).

Modules:
    - filesystem: Path handling, MIME detection, permissions
    - hashing: File hash computation
    - media: Video frame extraction
    - ffmpeg_progress: FFmpeg execution wrapper

Public API:
    From filesystem:
        - should_skip: Check if path should be skipped
        - detect_context: Detect file context
        - get_mime_safe: Safe MIME type detection
        - get_permissions: Get file permissions

    From hashing:
        - validate_hash_algo: Validate hash algorithm name
        - hash_file: Compute file hash

    From media:
        - extract_representative_frame: Extract video frame

    From ffmpeg_progress:
        - run_ffmpeg_with_progress: Execute FFmpeg with progress tracking
"""

from .filesystem import (
    should_skip, detect_context, get_mime_safe, get_permissions
)
from .hashing import validate_hash_algo, hash_file
from .media import extract_representative_frame
from .ffmpeg_progress import run_ffmpeg_with_progress

__all__ = [
    # Filesystem utilities
    "should_skip",
    "detect_context",
    "get_mime_safe",
    "get_permissions",
    # Hashing utilities
    "validate_hash_algo",
    "hash_file",
    # Media utilities
    "extract_representative_frame",
    # FFmpeg utilities
    "run_ffmpeg_with_progress",
]
