# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""nodupe.scanner — parallel file discovery and hashing utilities.

This module provides the high-level scanning utilities used by the
`nodupe` CLI and library. It implements a multi-threaded scanning
pipeline that discovers files on-disk, optionally skips files using a
known-files cache, and computes file hashes and basic metadata in a
bounded-thread pool. Key features:

- Robust file discovery via `iter_files` that honors ignore patterns and
    safely handles symlinks and transient filesystem errors.
- `process_file` unifies hashing + metadata extraction (mime type,
    context, permissions) for a single file.
- `threaded_hash` coordinates a threaded hashing pipeline with progress
    reporting (optional tqdm), ETA/stall messages, and a hard idle-timeout
    that cancels tasks if the pipeline appears stuck.

The documentation in `docs/DOCUMENTATION_TODO.md` lists additional
explanations and TODOs for improving the module-level docs and examples.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Iterable, List, Tuple
import time
import concurrent.futures as futures

from .utils.hashing import hash_file
from .utils.filesystem import (
    should_skip, detect_context, get_mime_safe, get_permissions
)


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


def process_file(
    p: Path, hash_algo: str, known_hash: str | None = None
) -> Tuple[str, int, int, str, str, str, str, str]:
    """Process a single file and return a metadata tuple.

    The returned tuple mirrors the values used in the rest of the
    project and tests:

    (path, size, mtime, hash, mime, context, algo, perms)

    Args:
        p: Path to the file to process.
        hash_algo: Hash algorithm name used by `hash_file`.
        known_hash: Optional pre-computed hash to avoid re-hashing
            (used by incremental scans where file size/mtime match).

    Returns:
        A tuple with the file path (str), size (int), modification
        timestamp (int), hash (str), mime (str), detected context
        (str), the algorithm used (str), and permissions string (str).
    """
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
    known_files: dict | None = None,
    heartbeat_interval: float = 10.0,
    stall_timeout: float | None = None,
    # Backwards-compatible alias (some tests/older callers):
    stalled_timeout: float | None = None,
    # Default hard timeout so callers don't hang indefinitely. Tests may
    # override this to a smaller value when exercising timeout behavior.
    max_idle_time: float | None = 300.0,
    show_eta: bool = True,
    *,
    # When collect=True, return (list_of_results, duration_s, total_count).
    # When False, return a generator to stream results (original behavior).
    collect: bool = False,
):
    """High-throughput threaded file hashing pipeline.

    threaded_hash implements a producer-consumer pattern over a
    thread pool. It discovers files (using `iter_files`), submits
    per-file hashing work to a ThreadPoolExecutor, and yields results
    as they complete. The function supports two modes:

    - Streaming (collect=False): returns a generator that yields
      (path, size, mtime, hash, mime, context, algo, perms) tuples as
      work completes.
    - Collect (collect=True): collects all results into a list and
      returns a tuple: (results_list, duration_seconds, total_count).

    Important arguments:
        roots: Iterable of root paths to scan.
        ignore: list of ignore patterns.
        workers: number of threads in the worker pool.
        hash_algo: name of hashing algorithm (passed to `hash_file`).
        follow_symlinks: whether discovery should follow symlinked dirs.
        known_files: optional mapping {path: (size, mtime, hash)} to skip
            re-hashing files that have not changed.
        heartbeat_interval: time in seconds used as a fallback wait
            interval for progress reporting when stall_timeout is not
            configured.
        stall_timeout/stalled_timeout: optional per-task stall threshold
            in seconds. If provided, the scanner will report tasks that
            exceed this age and can provide ETA calculations.
        max_idle_time: hard idle timeout in seconds. If no task
            completes for this many seconds, the pipeline will cancel
            pending work and raise TimeoutError so callers don't hang.
        show_eta: If True, print ETA/STALL messages when progress stalls.

    Returns:
        If collect is False, returns a generator of result tuples.
        If collect is True, returns (results_list, duration_seconds, total_count).
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
    start_time = time.time()
    last_progress_time = start_time
    _completed_durations: list[float] = []
    last_complete_ts = time.time()

    def _iter_impl():
        nonlocal count, last_progress_time, last_complete_ts
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
                                st.st_size == k_size
                                and int(st.st_mtime) == k_mtime
                            ):
                                known_hash = k_hash
                        except OSError:
                            pass

                    str_p = str(p)
                    submit_time = time.time()
                    fut = ex.submit(process_file, p, hash_algo, known_hash)
                    pending.add(fut)
                    # attach metadata so we can diagnose stalled tasks / ETA
                    if not hasattr(fut, '_submit_meta'):
                        setattr(fut, '_submit_meta', (str_p, submit_time))
                    # If we have too many pending tasks, wait for some to
                    # finish
                    if len(pending) >= MAX_PENDING:
                        # Wait for the first completed future. Prefer the
                        # configured stall_timeout (or the alias
                        # stalled_timeout), otherwise use the
                        # heartbeat_interval.
                        effective_stall_timeout = (
                            stall_timeout
                            if stall_timeout is not None
                            else stalled_timeout
                        )
                        wait_timeout = (
                            effective_stall_timeout
                            if effective_stall_timeout is not None
                            else heartbeat_interval
                        )
                        done, pending = futures.wait(
                            pending, timeout=wait_timeout,
                            return_when=futures.FIRST_COMPLETED
                        )
                        # If nothing completed in the wait interval we are
                        # stalled.
                        if not done:
                            now = time.time()
                            # If we have some historic per-task durations,
                            # compute an ETA from the average. Otherwise emit
                            # a short stall message so user knows we're still
                            # alive.
                            avg = (
                                sum(_completed_durations)
                                / len(_completed_durations)
                            ) if _completed_durations else None
                            if show_eta:
                                if avg:
                                    est = avg * len(pending) / max(1, workers)
                                    msg = (
                                        f"[scanner][ETA] approx "
                                        f"{round(est, 3)}s for {len(pending)} "
                                        f"pending tasks "
                                        f"(elapsed={now - start_time:.1f}s)"
                                    )
                                else:
                                    msg = (
                                        f"[scanner][STALL] no tasks completed "
                                        f"in {wait_timeout}s; {len(pending)} "
                                        f"pending "
                                        f"(elapsed={now - start_time:.1f}s)"
                                    )
                            else:
                                msg = (
                                    f"[scanner][INFO] no progress in "
                                    f"{wait_timeout}s; pending={len(pending)}"
                                )

                            if pbar is not None:
                                try:
                                    pbar.write(msg)
                                except Exception:
                                    print(msg, file=sys.stderr)
                            else:
                                print(msg, file=sys.stderr)

                            # Check for long-running tasks using submission
                            # metadata
                            oldest = None
                            for f in pending:
                                meta = getattr(f, '_submit_meta', None)
                                if not meta:
                                    continue
                                age = now - meta[1]
                                # if we have a per-task stall threshold,
                                # surface it
                                if (
                                    effective_stall_timeout is not None
                                    and age >= effective_stall_timeout
                                ):
                                    if not oldest or age > oldest[0]:
                                        oldest = (age, meta[0])
                            if oldest:
                                warn = (
                                    f"[scanner][WARN] Task stalled "
                                    f"{oldest[0]:.1f}s for: {oldest[1]}"
                                )
                                if pbar is not None:
                                    try:
                                        pbar.write(warn)
                                    except Exception:
                                        print(warn, file=sys.stderr)
                                else:
                                    print(warn, file=sys.stderr)

                            # Enforce a hard idle timeout so callers don't
                            # hang forever
                            if (
                                max_idle_time is not None
                                and (now - last_complete_ts) >= max_idle_time
                            ):
                                # Cancel pending tasks so the executor shutdown
                                # doesn't wait indefinitely for blocked
                                # workers.
                                try:
                                    ex.shutdown(
                                        wait=False, cancel_futures=True
                                    )
                                except TypeError:
                                    # Older Python versions may not support
                                    # cancel_futures
                                    try:
                                        ex.shutdown(wait=False)
                                    except Exception:
                                        pass
                                raise TimeoutError(
                                    f"scanner.threaded_hash: no tasks "
                                    f"completed for "
                                    f"{now - last_complete_ts:.3f}s "
                                    f"(max_idle_time={max_idle_time})"
                                )
                        for f in done:
                            try:
                                res = f.result()
                                # Update statistics on completion
                                now = time.time()
                                meta = getattr(f, '_submit_meta', None)
                                if meta:
                                    _completed_durations.append(
                                        max(0.0, now - meta[1])
                                    )
                                else:
                                    _completed_durations.append(
                                        max(0.0, now - last_complete_ts)
                                    )
                                last_complete_ts = now
                                if pbar is not None:
                                    pbar.update(1)
                                else:
                                    count += 1
                                    last_progress_time = time.time()
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
                        if pbar is not None:
                            pbar.update(1)
                        else:
                            count += 1
                            last_progress_time = time.time()
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
                if pbar is not None:
                    pbar.close()

    # When collect is False we want to return a generator so callers can stream
    # results. When collect is True we will collect into a list and return a
    # (results, duration, total) tuple for older callers/tests.
    gen = _iter_impl()
    if not collect:
        return gen
    # collect mode: iterate and gather results
    t0 = time.time()
    results = list(gen)
    dur = time.time() - t0
    return results, dur, len(results)
    # end threaded_hash
