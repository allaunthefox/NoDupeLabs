# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

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
    """
    A read-only FUSE filesystem that presents a deduplicated view of the scanned files.
    
    Structure:
    /by-hash/<algo>/<hash>  -> Read-only view of the file content (using the first found path)
    /stats                  -> Virtual file with DB statistics
    """

    def __init__(self, db_path: Path):
        self.db = DB(db_path)
        self.logger = logging.getLogger("nodupe.mount")

    def getattr(self, path: str, fh=None) -> Dict[str, Any]:
        if path == "/":
            return dict(st_mode=(stat.S_IFDIR | 0o755), st_nlink=2)
        
        if path == "/stats":
            return dict(st_mode=(stat.S_IFREG | 0o444), st_nlink=1, st_size=1024)

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
            rows = list(self.db.conn.execute(
                "SELECT path, size, mtime FROM files WHERE file_hash = ? AND hash_algo = ? LIMIT 1",
                (h, algo)
            ))
            if not rows:
                raise fuse.FuseOSError(errno.ENOENT)
            
            fpath, size, mtime = rows[0]
            return dict(st_mode=(stat.S_IFREG | 0o444), st_nlink=1, st_size=size, st_mtime=mtime)

        raise fuse.FuseOSError(errno.ENOENT)

    def readdir(self, path: str, fh) -> List[str]:
        if path == "/":
            return [".", "..", "by-hash", "stats"]
        
        parts = path.strip("/").split("/")

        if path == "/by-hash":
            # List used algorithms
            algos = self.db.conn.execute("SELECT DISTINCT hash_algo FROM files").fetchall()
            return [".", ".."] + [r[0] for r in algos]

        if len(parts) == 2 and parts[0] == "by-hash":
            algo = parts[1]
            # List hashes (limit to 1000 to prevent hanging on huge DBs for this demo)
            hashes = self.db.conn.execute(
                "SELECT DISTINCT file_hash FROM files WHERE hash_algo = ? LIMIT 1000",
                (algo,)
            ).fetchall()
            return [".", ".."] + [r[0] for r in hashes]

        return [".", ".."]

    def open(self, path: str, flags: int) -> int:
        # We only support read-only
        if (flags & os.O_ACCMODE) != os.O_RDONLY:
            raise fuse.FuseOSError(errno.EACCES)
        
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "by-hash":
            algo, h = parts[1], parts[2]
            rows = list(self.db.conn.execute(
                "SELECT path FROM files WHERE file_hash = ? AND hash_algo = ? LIMIT 1",
                (h, algo)
            ))
            if not rows:
                raise fuse.FuseOSError(errno.ENOENT)
            
            real_path = rows[0][0]
            return os.open(real_path, flags)
        
        if path == "/stats":
            return 0 # Virtual file

        raise fuse.FuseOSError(errno.ENOENT)

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        if path == "/stats":
            # Generate stats on the fly
            count = self.db.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            data = f"Total Files: {count}\n".encode("utf-8")
            return data[offset:offset + size]

        # For real files, fh is the file descriptor from os.open
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, size)

    def release(self, path: str, fh: int) -> int:
        if path == "/stats":
            return 0
        return os.close(fh)

def mount_fs(db_path: Path, mount_point: Path, foreground: bool = True):
    if not fuse._libfuse:
        print("[mount] Error: FUSE library (libfuse) not found. Cannot mount filesystem.", file=sys.stderr)
        print("[mount] Please install fuse (e.g. 'apt install fuse' or 'brew install macfuse').", file=sys.stderr)
        sys.exit(1)

    if not mount_point.exists():
        mount_point.mkdir(parents=True)

    print(f"[mount] Mounting deduplicated view at {mount_point}")
    print("[mount] Press Ctrl+C to unmount.")
    
    fs = NoDupeFS(db_path)
    fuse.FUSE(fs, str(mount_point), foreground=foreground, nothreads=False)
