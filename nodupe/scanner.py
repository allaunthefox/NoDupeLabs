# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Iterable, List, Tuple
import concurrent.futures as futures

from .utils.hashing import hash_file
from .utils.filesystem import (
    should_skip, detect_context, get_mime_safe, get_permissions
)


def iter_files(
    roots: Iterable[str], ignore: List[str],
    follow_symlinks: bool = False
) -> Iterable[Path]:
    for r in roots:
        rp = Path(r)
        if not rp.exists():
            print(f"[scanner][WARN] Root path not found: {r}", file=sys.stderr)
            continue

        try:
            # Use os.walk for robust handling of symlinks
            # and disappearing drives
            # onerror callback prints to stderr
            for root, dirs, files in os.walk(
                str(rp), topdown=True, followlinks=follow_symlinks,
                onerror=lambda e: print(
                    f"[scanner][WARN] Walk error: {e}", file=sys.stderr
                )
            ):
                root_path = Path(root)

                # Filter directories in-place to prevent recursion
                # into ignored/symlinked dirs
                i = 0
                while i < len(dirs):
                    d = dirs[i]
                    d_path = root_path / d
                    # Skip if ignored
                    if should_skip(d_path, ignore):
                        del dirs[i]
                        continue

                    # Skip if symlink and not following
                    # (os.walk followlinks=False handles recursion,
                    # but we filter for clarity/safety)
                    if not follow_symlinks and d_path.is_symlink():
                        del dirs[i]
                        continue
                    i += 1

                for f in files:
                    p = root_path / f

                    # Skip symlinks if configured
                    if not follow_symlinks and p.is_symlink():
                        continue

                    if should_skip(p, ignore):
                        continue

                    yield p
        except OSError as e:
            print(f"[scanner][WARN] Failed to walk {r}: {e}", file=sys.stderr)


def process_file(
    p: Path, hash_algo: str, known_hash: str | None = None
) -> Tuple[str, int, int, str, str, str, str, str]:
    """Process a single file: hash it (or use known) and extract metadata."""
    st = p.stat()

    if known_hash:
        sha = known_hash
    else:
        sha = hash_file(p, hash_algo)

    mime = get_mime_safe(p)
    context = detect_context(p)
    perms = get_permissions(p)
    return (
        str(p), st.st_size, int(st.st_mtime), sha, mime,
        context, hash_algo, perms
    )


def threaded_hash(
    roots: Iterable[str], ignore: List[str], workers: int = 4,
    hash_algo: str = "sha512", follow_symlinks: bool = False,
    known_files: dict | None = None
):
    """
    Scan files and compute hashes incrementally.
    known_files: dict {path: (size, mtime, hash)} to skip re-hashing.
    Yields: (path, size, mtime, hash, mime, context, algo, perms)
    """
    # Use a bounded set of futures to prevent loading all files into memory
    MAX_PENDING = workers * 4

    known_files = known_files or {}

    # Try to use tqdm if available
    try:
        from tqdm import tqdm  # type: ignore
        pbar = tqdm(desc="Scanning", unit="file")
    except ImportError:
        tqdm = None
        pbar = None

    count = 0

    with futures.ThreadPoolExecutor(
        max_workers=max(1, workers)
    ) as ex:
        pending = set()

        try:
            for p in iter_files(
                roots, ignore, follow_symlinks=follow_symlinks
            ):  # Check if we can skip hashing
                known_hash = None
                str_p = str(p)
                if str_p in known_files:
                    k_size, k_mtime, k_hash = known_files[str_p]
                    try:
                        st = p.stat()
                        if (
                            st.st_size == k_size and
                            int(st.st_mtime) == k_mtime
                        ):
                            known_hash = k_hash
                    except OSError:
                        pass

                fut = ex.submit(process_file, p, hash_algo, known_hash)
                pending.add(fut)
                # If we have too many pending tasks, wait for some to finish
                if len(pending) >= MAX_PENDING:
                    done, pending = futures.wait(
                        pending, return_when=futures.FIRST_COMPLETED
                    )
                    for f in done:
                        try:
                            res = f.result()
                            if pbar:
                                pbar.update(1)
                            else:
                                count += 1
                                if count % 100 == 0:
                                    print(
                                        f"[scanner] Processed {count}...",
                                        file=sys.stderr
                                    )
                            yield res
                        except (OSError, ValueError, RuntimeError) as e:
                            print(
                                f"[scanner][WARN] Processing error: {e}",
                                file=sys.stderr
                            )

            # Drain remaining
            for f in futures.as_completed(pending):
                try:
                    res = f.result()
                    if pbar:
                        pbar.update(1)
                    else:
                        count += 1
                        if count % 100 == 0:
                            print(
                                f"[scanner] Processed {count}...",
                                file=sys.stderr
                            )
                    yield res
                except (OSError, ValueError, RuntimeError) as e:
                    print(
                        f"[scanner][WARN] Processing error: {e}",
                        file=sys.stderr
                    )

        finally:
            if pbar:
                pbar.close()
