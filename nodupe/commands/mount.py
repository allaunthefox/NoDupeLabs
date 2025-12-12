# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""FUSE filesystem mount command.

This module implements the 'mount' command, which exposes the deduplicated
content database as a read-only FUSE filesystem. This allows users to
browse the file index as a virtual directory structure.

Key Features:
    - Mount SQLite database as virtual filesystem
    - Read-only access to indexed files
    - Custom directory structure views (by hash, by type, etc.)

Dependencies:
    - pathlib: Path handling
    - ..mount: FUSE implementation

Example:
    >>> # CLI usage
    >>> $ nodupe mount /mnt/nodupe
"""

from pathlib import Path
from typing import Any, Dict
from ..mount import mount_fs


def cmd_mount(args: Any, cfg: Dict[str, Any]) -> int:
    """Mount the database as a FUSE filesystem.

    This function exposes the deduplicated content database as a read-only
    FUSE filesystem, allowing users to browse the file index as a virtual
    directory structure. The filesystem provides access to all indexed files
    with custom organization options.

    The mount process:
    1. Loads the SQLite database
    2. Creates virtual filesystem structure
    3. Mounts at the specified mountpoint
    4. Provides read-only access to indexed files
    5. Handles filesystem operations transparently

    Args:
        args: Argparse Namespace with attributes:
            - mountpoint (str): Directory to mount the filesystem
        cfg: Configuration dictionary with keys:
            - db_path (str): SQLite database file path

    Returns:
        int: Exit code (0 for success)

    Raises:
        FileNotFoundError: If database file doesn't exist
        PermissionError: If mountpoint can't be accessed
        OSError: If FUSE mounting fails
        Exception: For unexpected errors during mount

    Example:
        >>> from argparse import Namespace
        >>> args = Namespace(mountpoint='/mnt/nodupe')
        >>> cfg = {'db_path': 'nodupe.db'}
        >>> exit_code = cmd_mount(args, cfg)
        >>> print(f"Mount completed with exit code: {exit_code}")
        0

    Notes:
        - Filesystem is read-only (no modifications allowed)
        - Requires FUSE support on the operating system
        - Mountpoint directory must exist and be accessible
        - Filesystem remains mounted until unmounted
        - Provides virtual views of file organization
    """
    mount_fs(Path(cfg["db_path"]), Path(args.mountpoint))
    return 0
