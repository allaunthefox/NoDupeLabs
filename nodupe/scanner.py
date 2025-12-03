# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from __future__ import annotations
import time
import hashlib
import mimetypes
import sys
from pathlib import Path
from typing import Iterable, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .deps import check_dep
except ImportError:
    def check_dep(_: str) -> bool:
        return False

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

def iter_files(roots: Iterable[str], ignore: List[str]) -> Iterable[Path]:
    for r in roots:
        rp = Path(r)
        if not rp.exists():
            continue
        for p in rp.rglob("*"):
            if p.is_file() and not _should_skip(p, ignore):
                yield p

def threaded_hash(roots: Iterable[str], ignore: List[str], workers: int = 4, hash_algo: str = "sha512"):
    """
    Scan files and compute hashes.
    Returns: (results, duration, total_files)
    """
    files = list(iter_files(roots, ignore))
    results: List[Tuple[str, int, int, str, str, str, str]] = []
    start = time.time()

    # Try to use tqdm if available
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {}
        for p in files:
            futs[ex.submit(hash_file, p, hash_algo)] = p

        if tqdm:
            pbar = tqdm(total=len(futs), desc="Hashing files", unit="file")
            for fut in as_completed(futs):
                p = futs[fut]
                try:
                    sha = fut.result()
                    st = p.stat()
                    mime = _get_mime_safe(p)
                    context = _detect_context(p)
                    results.append((str(p), st.st_size, int(st.st_mtime), sha, mime, context, hash_algo))
                except Exception as e:
                    print(f"[scanner][WARN] Failed to process {p}: {e}", file=sys.stderr)
                finally:
                    pbar.update(1)
            pbar.close()
        else:
            # Simple text progress
            done = 0
            for fut in as_completed(futs):
                p = futs[fut]
                try:
                    sha = fut.result()
                    st = p.stat()
                    mime = _get_mime_safe(p)
                    context = _detect_context(p)
                    results.append((str(p), st.st_size, int(st.st_mtime), sha, mime, context, hash_algo))
                except Exception as e:
                    print(f"[scanner][WARN] Failed to process {p}: {e}", file=sys.stderr)
                done += 1
                if done % 100 == 0:
                    print(f"[scanner] Processed {done}/{len(files)}...", file=sys.stderr)

    dur = time.time() - start
    return results, dur, len(files)
