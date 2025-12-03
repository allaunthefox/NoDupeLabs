# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from __future__ import annotations
import os
import time
import hashlib
import mimetypes
import sys
import stat
from pathlib import Path
from typing import Iterable, List, Tuple
import concurrent.futures as futures


CHUNK = 1024 * 1024  # 1MB

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

SUPPORTED_HASH_ALGOS = {"sha512", "sha256", "blake2b", "sha1", "md5"}

def validate_hash_algo(algo: str) -> str:
    algo = algo.lower().strip()
    if algo not in SUPPORTED_HASH_ALGOS:
        raise ValueError(f"Unsupported hash algorithm: '{algo}'. Supported: {', '.join(sorted(SUPPORTED_HASH_ALGOS))}")
    return algo

def _should_skip(p: Path, ignore: List[str]) -> bool:
    parts = set(p.parts)
    return any(ig in parts for ig in ignore)

def hash_file(p: Path, algo: str = "sha512") -> str:
    """Compute hash of file using specified algorithm."""
    if algo == "sha512":
        h = hashlib.sha512()
    elif algo == "sha256":
        h = hashlib.sha256()
    elif algo == "blake2b":
        h = hashlib.blake2b()
    elif algo == "sha1":
        h = hashlib.sha1()
    elif algo == "md5":
        h = hashlib.md5()
    else:
        h = hashlib.sha512()

    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()

def _detect_context(path: Path) -> str:
    """Detect if file is archived or unarchived."""
    # Expanded context detection
    indicators = {
        "extracted", "unzipped", "unpacked", "expanded",
        "backup", "archive", "old", "temp", "tmp"
    }
    for parent in path.parents:
        if parent.name.lower() in indicators:
            return "archived"
    return "unarchived"

def _get_mime_safe(p: Path) -> str:
    # Check overrides first
    suffix = p.suffix.lower()
    if suffix in MIME_OVERRIDES:
        return MIME_OVERRIDES[suffix]

    mime, _ = mimetypes.guess_type(str(p))
    if mime:
        return mime
    return "application/octet-stream"

def _get_permissions(p: Path) -> str:
    try:
        # Return octal representation of mode, e.g. "0o755"
        return oct(stat.S_IMODE(p.stat().st_mode))
    except OSError:
        return "0"

def iter_files(roots: Iterable[str], ignore: List[str], follow_symlinks: bool = False) -> Iterable[Path]:
    for r in roots:
        rp = Path(r)
        if not rp.exists():
            print(f"[scanner][WARN] Root path not found: {r}", file=sys.stderr)
            continue
        
        try:
            # Use os.walk for robust handling of symlinks and disappearing drives
            for root, dirs, files in os.walk(str(rp), topdown=True, followlinks=follow_symlinks, onerror=lambda e: print(f"[scanner][WARN] Walk error: {e}", file=sys.stderr)):
                root_path = Path(root)

                # Filter directories in-place to prevent recursion into ignored/symlinked dirs
                i = 0
                while i < len(dirs):
                    d = dirs[i]
                    d_path = root_path / d
                    
                    # Skip if ignored
                    if _should_skip(d_path, ignore):
                        del dirs[i]
                        continue
                    
                    # Skip if symlink and not following (os.walk followlinks=False handles recursion, but we filter for clarity/safety)
                    if not follow_symlinks and d_path.is_symlink():
                        del dirs[i]
                        continue
                        
                    i += 1

                for f in files:
                    p = root_path / f
                    
                    # Skip symlinks if configured
                    if not follow_symlinks and p.is_symlink():
                        continue

                    if _should_skip(p, ignore):
                        continue
                        
                    yield p
        except OSError as e:
            print(f"[scanner][WARN] Failed to walk {r}: {e}", file=sys.stderr)

def process_file(p: Path, hash_algo: str) -> Tuple[str, int, int, str, str, str, str, str]:
    """Process a single file: hash it and extract all metadata."""
    sha = hash_file(p, hash_algo)
    st = p.stat()
    mime = _get_mime_safe(p)
    context = _detect_context(p)
    perms = _get_permissions(p)
    return (str(p), st.st_size, int(st.st_mtime), sha, mime, context, hash_algo, perms)

def threaded_hash(roots: Iterable[str], ignore: List[str], workers: int = 4, hash_algo: str = "sha512", follow_symlinks: bool = False):
    """
    Scan files and compute hashes.
    Returns: (results, duration, total_files)
    """
    files = list(iter_files(roots, ignore, follow_symlinks=follow_symlinks))
    results: List[Tuple[str, int, int, str, str, str, str, str]] = []
    start = time.time()

    # Try to use tqdm if available
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None

    with futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {}
        for p in files:
            futs[ex.submit(process_file, p, hash_algo)] = p

        if tqdm:
            pbar = tqdm(total=len(futs), desc="Hashing files", unit="file")
            for fut in futures.as_completed(futs):
                p = futs[fut]
                try:
                    # Result is now the full tuple
                    results.append(fut.result())
                except Exception as e:  # pylint: disable=broad-except
                    print(f"[scanner][WARN] Failed to process {p}: {e}", file=sys.stderr)
                finally:
                    pbar.update(1)
            pbar.close()
        else:
            # Simple text progress
            done = 0
            for fut in futures.as_completed(futs):
                p = futs[fut]
                try:
                    results.append(fut.result())
                except Exception as e:  # pylint: disable=broad-except
                    print(f"[scanner][WARN] Failed to process {p}: {e}", file=sys.stderr)
                done += 1
                if done % 100 == 0:
                    print(f"[scanner] Processed {done}/{len(files)}...", file=sys.stderr)

    dur = time.time() - start
    return results, dur, len(files)
