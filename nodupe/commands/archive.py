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
from ..archiver import ArchiveHandler


def cmd_archive_list(args, _cfg):
    """List contents of an archive file.

    Args:
        args: Argparse Namespace with attributes:
            - file (str): Path to archive file
        _cfg: Configuration dictionary (unused)

    Returns:
        int: Exit code (0 for success, 1 for error)
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


def cmd_archive_extract(args, _cfg):
    """Extract archive contents to a destination directory.

    Args:
        args: Argparse Namespace with attributes:
            - file (str): Path to archive file
            - dest (str): Destination directory path
        _cfg: Configuration dictionary (unused)

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        h = ArchiveHandler(args.file)
        h.extract(args.dest)
        print("Extraction complete.")
        return 0
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
