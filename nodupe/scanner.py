# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""nodupe.scanner — parallel file discovery and hashing utilities.

This module provides the high-level scanning utilities used by the
`nodupe` CLI and library. It implements a multi-threaded scanning
pipeline that discovers files on-disk, optionally skips files using a
known-files cache, and computes file hashes and basic metadata in a
bounded-thread pool.

Key Features:
    - Multi-threaded file discovery and processing
    - Incremental scanning with known-files cache
    - Parallel hashing with bounded thread pool
    - Comprehensive file metadata extraction
    - Backward compatibility facade for nodupe.scan

Dependencies:
    - Required: nodupe.scan package
    - Optional: None

Note: This module is now a facade for `nodupe.scan`.

Usage Example:
    >>> from nodupe.scanner import iter_files, process_file
    >>> for file_path in iter_files("/path/to/directory"):
    ...     record = process_file(file_path, "sha512")
    ...     print(f"Processed: {record[0]}")
"""

from __future__ import annotations

# Facade: Import from new location with graceful fallback
try:
    from .scan import (
        iter_files,
        process_file,
        threaded_hash,
        FileProcessor,
        ProgressTracker
    )
except ImportError:
    # Fallback for circular imports or if scan package is broken
    # (This should ideally not happen in production, but good for dev)
    from .scan.walker import iter_files
    from .scan.processor import process_file, FileProcessor
    from .scan.hasher import threaded_hash
    from .scan.progress import ProgressTracker

# Re-export for backward compatibility
__all__ = [
    "iter_files",
    "process_file",
    "threaded_hash",
    "FileProcessor",
    "ProgressTracker",
]

# Expose test helper if needed (though tests should update to use scan.hasher)
