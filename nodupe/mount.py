# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""FUSE filesystem implementation for deduplicated content view.

This module provides a read-only virtual filesystem that exposes the
deduplicated file index. It organizes files by hash and algorithm,
allowing users to browse the content-addressable storage directly.

Key Features:
    - Read-only access to all indexed files
    - Virtual directory structure: /by-hash/<algo>/<hash>
    - Virtual statistics file: /stats
    - Efficient on-demand database queries
    - Low memory footprint (streaming reads)

Classes:
    - NoDupeFS: FUSE operations implementation

Dependencies:
    - fuse: Python FUSE bindings (fusepy)
    - ..db: Database access
    - ..vendor.fuse: Vendored FUSE interface

Example:
    >>> mount_fs(Path("nodupe.db"), Path("/mnt/nodupe"))
"""

import os
import sys
import errno
import logging
import stat
from pathlib import Path
from typing import Dict, Any, List
from .db import DB
from .vendor import fuse


class NoDupeFS(fuse.Operations):
    """Read-only FUSE filesystem presenting a deduplicated view.

    Implements standard FUSE operations (getattr, readdir, open, read)
    to expose the database contents as a virtual filesystem.

    Virtual Structure:
        /                       -> Root directory
        /stats                  -> Text file with DB statistics
        /by-hash/               -> Directory of hash algorithms
        /by-hash/<algo>/        -> Directory of file hashes
        /by-hash/<algo>/<hash>  -> File content (read-only)

    Attributes:
        db (DB): Database connection
        logger (Logger): Logger instance
    """

    def __init__(self, db_path: Path):
        self.db = DB(db_path)
        self.logger = logging.getLogger("nodupe.mount")

    def getattr(self, path: str, fh=None) -> Dict[str, Any]:
        """Get file attributes for a path."""
        if path == "/":
            return dict(st_mode=(stat.S_IFDIR | 0o755), st_nlink=2)

        if path == "/stats":
            return dict(
                st_mode=(stat.S_IFREG | 0o444), st_nlink=1, st_size=1024
            )

        parts = path.strip("/").split("/")

        # /by-hash
        if len(parts) == 1 and parts[0] == "by-hash":
            return dict(st_mode=(stat.S_IFDIR | 0o755), st_nlink=2)

        # /by-hash/<algo>
        if len(parts) == 2 and parts[0] == "by-hash":
            return dict(st_mode=(stat.S_IFDIR | 0o755), st_nlink=2)

        # /by-hash/<algo>/<hash>
        if len(parts) == 3 and parts[0] == "by-hash":
            algo, h = parts[1], parts[2]
            # Query DB for this hash
            # Query DB for this hash
            rows = list(self.db.conn.execute(
                "SELECT path, size, mtime FROM files "
                "WHERE file_hash = ? AND hash_algo = ? LIMIT 1",
                (h, algo)
            ))
            if not rows:
                raise fuse.FuseOSError(errno.ENOENT)

            _, size, mtime = rows[0]
            return dict(
                st_mode=(stat.S_IFREG | 0o444), st_nlink=1,
                st_size=size, st_mtime=mtime
            )

        raise fuse.FuseOSError(errno.ENOENT)

    def readdir(self, path: str, fh) -> List[str]:
        """List directory contents."""
        if path == "/":
            return [".", "..", "by-hash", "stats"]

        parts = path.strip("/").split("/")

        if path == "/by-hash":
            # List used algorithms
            algos = self.db.conn.execute(
                "SELECT DISTINCT hash_algo FROM files"
            ).fetchall()
            return [".", ".."] + [r[0] for r in algos]

        if len(parts) == 2 and parts[0] == "by-hash":
            algo = parts[1]
            # List hashes (limit to 1000 to prevent hanging on huge DBs)
            hashes = self.db.conn.execute(
                "SELECT DISTINCT file_hash FROM files "
                "WHERE hash_algo = ? LIMIT 1000",
                (algo,)
            ).fetchall()
            return [".", ".."] + [r[0] for r in hashes]

        return [".", ".."]

    def open(self, path: str, flags: int) -> int:
        """Open a file and return a file descriptor."""
        # We only support read-only
        if (flags & os.O_ACCMODE) != os.O_RDONLY:
            raise fuse.FuseOSError(errno.EACCES)

        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "by-hash":
            algo, h = parts[1], parts[2]
            rows = list(self.db.conn.execute(
                "SELECT path FROM files "
                "WHERE file_hash = ? AND hash_algo = ? LIMIT 1",
                (h, algo)
            ))
            if not rows:
                raise fuse.FuseOSError(errno.ENOENT)

            real_path = rows[0][0]
            return os.open(real_path, flags)

        if path == "/stats":
            return 0  # Virtual file

        raise fuse.FuseOSError(errno.ENOENT)

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        """Read data from a file."""
        if path == "/stats":
            # Generate stats on the fly
            count = self.db.conn.execute(
                "SELECT COUNT(*) FROM files"
            ).fetchone()[0]
            data = f"Total Files: {count}\n".encode("utf-8")
            return data[offset:offset + size]

        # For real files, fh is the file descriptor from os.open
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, size)

    def release(self, path: str, fh: int) -> int:
        """Release (close) a file."""
        if path == "/stats":
            return 0
        return os.close(fh)


def mount_fs(db_path: Path, mount_point: Path, foreground: bool = True):
    """Mount the deduplicated filesystem at the given mount point."""
    if not fuse._libfuse:  # pylint: disable=protected-access
        print(
            "[mount] Error: FUSE library (libfuse) not found. "
            "Cannot mount filesystem.",
            file=sys.stderr
        )
        print(
            "[mount] Please install fuse (e.g. 'apt install fuse' or "
            "'brew install macfuse').",
            file=sys.stderr
        )
        sys.exit(1)

    if not mount_point.exists():
        mount_point.mkdir(parents=True)

    print(f"[mount] Mounting deduplicated view at {mount_point}")
    print("[mount] Press Ctrl+C to unmount.")

    fs = NoDupeFS(db_path)
    fuse.FUSE(fs, str(mount_point), foreground=foreground, nothreads=False)
