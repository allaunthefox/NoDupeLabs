# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Archive inspection and extraction commands.

This module implements the 'archive' command group, allowing users to
inspect the contents of archive files (zip, tar, rar, 7z) and extract
them safely. It serves as a unified interface for handling various
archive formats supported by the backend.

Key Features:
    - List contents of archives with size and path info
    - Extract archives to specified destination
    - Unified error handling for different archive formats

Commands:
    - list: Show archive contents
    - extract: Unpack archive to directory

Dependencies:
    - ..archiver: Core archive handling logic

Example:
    >>> # CLI usage
    >>> $ nodupe archive list backup.zip
    >>> $ nodupe archive extract backup.zip --dest /tmp/restore
"""

import sys
from pathlib import Path
from typing import Any, Dict, List
from ..archiver import ArchiveHandler


def cmd_archive_list(args: Any, _cfg: Dict[str, Any]) -> int:
    """List contents of an archive file.

    This function displays the contents of an archive file, showing each
    file's size and path within the archive. It supports multiple archive
    formats (zip, tar, rar, 7z) through the unified ArchiveHandler interface.

    Args:
        args: Argparse Namespace with attributes:
            - file (str): Path to archive file
        _cfg: Configuration dictionary (unused)

    Returns:
        int: Exit code (0 for success, 1 for error)

    Raises:
        FileNotFoundError: If archive file doesn't exist
        ValueError: If file is not a valid archive
        RuntimeError: If archive cannot be read
        OSError: If file operations fail

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(file='backup.zip')
        >>> exit_code = cmd_archive_list(args, {})
        Archive Type: zip
            1024000 file1.txt
             512000 file2.jpg
        >>> print(f"List completed with exit code: {exit_code}")
        0

    Notes:
        - Supports multiple archive formats (zip, tar, rar, 7z)
        - Displays file sizes in bytes
        - Shows relative paths within archive
        - Exit code 0 indicates successful listing
        - Exit code 1 indicates error occurred
    """
    try:
        h = ArchiveHandler(args.file)
        print(f"Archive Type: {h.type}")
        for item in h.list_contents():
            print(f"{item['size']:>12} {item['path']}")
        return 0
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_archive_extract(args: Any, _cfg: Dict[str, Any]) -> int:
    """Extract archive contents to a destination directory.

    This function extracts the contents of an archive file to the specified
    destination directory. It supports multiple archive formats (zip, tar, rar, 7z)
    and handles the extraction process with proper error handling and validation.

    Args:
        args: Argparse Namespace with attributes:
            - file (str): Path to archive file
            - dest (str): Destination directory path
        _cfg: Configuration dictionary (unused)

    Returns:
        int: Exit code (0 for success, 1 for error)

    Raises:
        FileNotFoundError: If archive file doesn't exist
        ValueError: If file is not a valid archive
        RuntimeError: If archive cannot be extracted
        OSError: If file operations fail
        PermissionError: If destination directory can't be written

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(file='backup.zip', dest='/tmp/restore')
        >>> exit_code = cmd_archive_extract(args, {})
        Extraction complete.
        >>> print(f"Extraction completed with exit code: {exit_code}")
        0

    Notes:
        - Supports multiple archive formats (zip, tar, rar, 7z)
        - Destination directory must exist and be writable
        - Preserves file structure within archive
        - Exit code 0 indicates successful extraction
        - Exit code 1 indicates error occurred
        - Handles path collisions and permission issues
    """
    try:
        h = ArchiveHandler(args.file)
        h.extract(args.dest)
        print("Extraction complete.")
        return 0
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
