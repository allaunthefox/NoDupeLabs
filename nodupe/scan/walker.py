# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File discovery utilities.

Provides iter_files for robust directory walking.
"""
import os
import sys
from pathlib import Path
from typing import Iterable, List

from ..utils.filesystem import should_skip


def iter_files(
    roots: Iterable[str], ignore: List[str],
    follow_symlinks: bool = False
) -> Iterable[Path]:
    """Yield Path objects for files under `roots`.

    This function walks each directory in `roots` and yields files while
    respecting the `ignore` patterns (checked with `should_skip`) and the
    `follow_symlinks` flag. It is resilient to transient filesystem
    errors and reports non-fatal issues via stderr so the calling code
    can continue scanning other roots.

    Args:
        roots: Iterable of root paths to search (strings).
        ignore: List of path patterns to skip (passed to `should_skip`).
        follow_symlinks: If True, follow directory symlinks when walking.

    Yields:
        pathlib.Path objects for each discovered file.
    """
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
