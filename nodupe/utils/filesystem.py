# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Filesystem utilities for file metadata and path handling.

This module provides helper functions for working with filesystem
metadata including MIME type detection, permission capture, context
detection, and path filtering.

Key Features:
    - Modern MIME type support (WebP, HEIC, AVIF, Matroska, etc.)
    - Context detection (archived vs. unarchived based on path)
    - Permission capture with octal representation
    - Path ignore pattern matching for scanner exclusions

MIME Type Handling:
    - Manual overrides for modern formats not in Python's mimetypes
    - Fallback to standard library mimetypes module
    - Default to application/octet-stream for unknown types

Context Detection Strategy:
    Files are marked as "archived" if any parent directory name
    matches common archive/temp indicators:
    - extracted, unzipped, unpacked, expanded
    - backup, archive, old, temp, tmp

Dependencies:
    - mimetypes: Standard library MIME type detection
    - stat: File permission mode parsing
    - pathlib: Path manipulation

Example:
    >>> from pathlib import Path
    >>> mime = get_mime_safe(Path('photo.webp'))
    >>> print(mime)
    'image/webp'
    >>> ctx = detect_context(Path('/data/extracted/photo.jpg'))
    >>> print(ctx)
    'archived'
"""

import mimetypes
import stat
from pathlib import Path
from typing import List

ARCHIVE_EXTENSIONS = {
    ".zip", ".7z", ".tar", ".gz", ".bz2", ".xz", ".rar",
    ".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tbz2",
}

# Manual overrides for modern/common types that mimetypes might miss
MIME_OVERRIDES = {
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".avif": "image/avif",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".ts": "video/mp2t",
    ".m2ts": "video/mp2t",
    ".json": "application/json",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
    ".md": "text/markdown",
    ".log": "text/plain",
}


def should_skip(p: Path, ignore: List[str]) -> bool:
    """Check if path should be skipped based on ignore patterns.

    Determines if any part of the path matches the ignore patterns.
    Used by the scanner to exclude directories like .git, __pycache__,
    node_modules, etc.

    Args:
        p: Path to check
        ignore: List of directory/file names to ignore

    Returns:
        True if path should be skipped, False otherwise

    Example:
        >>> from pathlib import Path
        >>> ignore = ['.git', '__pycache__', 'node_modules']
        >>> should_skip(Path('/project/.git/config'), ignore)
        True
        >>> should_skip(Path('/project/src/main.py'), ignore)
        False
    """
    parts = set(p.parts)
    return any(ig in parts for ig in ignore)


def detect_context(path: Path) -> str:
    """Detect if file is in archived or unarchived context.

    Analyzes the directory path to determine if the file is likely
    from an extracted archive or temporary location based on parent
    directory names.

    Args:
        path: Path to file

    Returns:
        Context string: 'archived' or 'unarchived'

    Context Indicators (case-insensitive):
        - archived: extracted, unzipped, unpacked, expanded, backup,
          archive, old, temp, tmp
        - unarchived: All other paths (default)

    Example:
        >>> from pathlib import Path
        >>> detect_context(Path('/data/extracted/photo.jpg'))
        'archived'
        >>> detect_context(Path('/backup/files/doc.pdf'))
        'archived'
        >>> detect_context(Path('/home/user/photos/pic.jpg'))
        'unarchived'
    """
    # Expanded context detection
    indicators = {
        "extracted", "unzipped", "unpacked", "expanded",
        "backup", "archive", "old", "temp", "tmp"
    }
    for parent in path.parents:
        if parent.name.lower() in indicators:
            return "archived"
    return "unarchived"


def get_mime_safe(p: Path) -> str:
    """Get MIME type for file with modern format support.

    Determines MIME type using manual overrides for modern formats
    (WebP, HEIC, AVIF, Matroska, etc.) with fallback to Python's
    mimetypes module. Returns generic octet-stream for unknown types.

    Args:
        p: Path to file

    Returns:
        MIME type string (e.g., 'image/webp', 'video/x-matroska',
        'application/octet-stream')

    Priority:
        1. MIME_OVERRIDES manual mappings (modern formats)
        2. Python mimetypes.guess_type() (standard formats)
        3. 'application/octet-stream' (unknown files)

    Example:
        >>> from pathlib import Path
        >>> get_mime_safe(Path('photo.webp'))
        'image/webp'
        >>> get_mime_safe(Path('video.mkv'))
        'video/x-matroska'
        >>> get_mime_safe(Path('unknown.xyz'))
        'application/octet-stream'
    """
    # Check overrides first
    suffix = p.suffix.lower()
    if suffix in MIME_OVERRIDES:
        return MIME_OVERRIDES[suffix]

    mime, _ = mimetypes.guess_type(str(p))
    if mime:
        return mime
    return "application/octet-stream"


def get_permissions(p: Path) -> str:
    """Get file permissions as octal string.

    Retrieves Unix-style file permissions and returns them as an
    octal string representation (e.g., '0o755', '0o644').

    Args:
        p: Path to file

    Returns:
        Octal permission string (e.g., '0o755', '0o644')
        Returns '0' if permissions cannot be read

    Raises:
        No exceptions raised. OSError handled internally.

    Example:
        >>> from pathlib import Path
        >>> # Executable file
        >>> get_permissions(Path('/usr/bin/ls'))
        '0o755'
        >>> # Regular file
        >>> get_permissions(Path('/home/user/doc.txt'))
        '0o644'
        >>> # Inaccessible file
        >>> get_permissions(Path('/root/.ssh/id_rsa'))
        '0'
    """
    try:
        # Return octal representation of mode, e.g. "0o755"
        return oct(stat.S_IMODE(p.stat().st_mode))
    except OSError:
        return "0"
