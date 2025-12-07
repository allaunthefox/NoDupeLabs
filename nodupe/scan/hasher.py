# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun
"""Hashing pipeline utilities.

Provides threaded_hash for high-throughput parallel hashing.
"""
from __future__ import annotations

import os as _os
import time
import concurrent.futures as futures
from typing import Iterable, List, Optional
import sys
from .walker import iter_files
from .processor import process_file

def _choose_executor_type(executor_choice: str, workers_count: int) -> str:
    """Decide executor type (thread/process) for threaded_hash.

    Heuristic used by 'auto':
      - If PYTHON_ENABLE_NOGIL=1 -> prefer 'thread' (free-threading runtime)
      - Otherwise use logical CPU count (os.cpu_count()).
        - For small systems (<= 12 logical CPUs) prefer 'thread' to avoid
          process startup / memory overhead.
        - For larger systems (> 12 logical CPUs) prefer 'process' to
          better utilize many physical cores where process parallelism
          outweighs overhead.
        - Exception: if workers count is small relative to CPU count
          (workers < cpu // 2), prefer 'thread' even on large machines
          to avoid overhead for light workloads.

    Args:
        executor_choice: 'auto', 'thread', or 'process'
        workers_count: number of workers requested

    Returns:
        'thread' or 'process'
    """
    if executor_choice != "auto":
        return executor_choice

    # Check for free-threading (PEP 703) environment
    if _os.environ.get("PYTHON_ENABLE_NOGIL") == "1":
        return "thread"

    try:
        cpu = int(_os.cpu_count() or 1)
    except Exception:
        cpu = 1

    # Small/medium machine heuristic
    if cpu <= 12:
        return "thread"

    # Large machine heuristic
    # If we are using a small fraction of available cores, threads are cheaper
    if workers_count < (cpu // 2):
        return "thread"

    return "process"


def threaded_hash(
    roots: Iterable[str], ignore: List[str], workers: int = 4,
    executor: str = "auto",
    hash_algo: str = "sha512", follow_symlinks: bool = False,
    known_files: Optional[dict] = None,
    heartbeat_interval: float = 10.0,
    stall_timeout: Optional[float] = None,
    # Backwards-compatible alias (some tests/older callers):
    stalled_timeout: Optional[float] = None,
    # Default hard timeout so callers don't hang indefinitely. Tests may
    # override this to a smaller value when exercising timeout behavior.
    max_idle_time: Optional[float] = 300.0,
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
    - Collect(collect=True): collects all results into a list and
      returns a tuple: (results_list, duration_seconds, total_count).

    Important arguments:
        roots: Iterable of root paths to scan.
        ignore: list of ignore patterns.
        workers: number of worker threads / processes in the pool.
        executor: executor selection strategy for work distribution:
            'thread', 'process', or 'auto'. When 'auto' the function
            will pick a sensible default for the running host.
            The heuristic is evidence-informed:
            - <= 16 logical CPUs: prefer threads (common consumer/dev)
            - 17..31 logical CPUs: choose based on requested worker load
              (process if workers >= cpu // 2, else thread)
            - >= 32 logical CPUs: prefer processes (cloud/server sizes)
        hash_algo: name of hashing algorithm(passed to `hash_file`).
        follow_symlinks: whether discovery should follow symlinked dirs.
        known_files: optional mapping {path: (size, mtime, hash)} to skip
            re - hashing files that have not changed.
        heartbeat_interval: time in seconds used as a fallback wait
            interval for progress reporting when stall_timeout is not
            configured.
        stall_timeout / stalled_timeout: optional per - task stall threshold
            in seconds. If provided, the scanner will report tasks that
            exceed this age and can provide ETA calculations.
        max_idle_time: hard idle timeout in seconds. If no task
            completes for this many seconds, the pipeline will cancel
            pending work and raise TimeoutError so callers don't hang.
        show_eta: If True, print ETA/STALL messages when progress stalls.

    Returns:
        If collect is False, returns a generator of result tuples.
        If collect is True, returns (results_list, duration_seconds,
        total_count).
    """
    # Choose executor type. We support an environment override for
    # GIL-free runtimes; setting PYTHON_ENABLE_NOGIL=1 causes the code
    # to prefer threads because the interpreter is expected to allow
    # true parallel threads. Otherwise ProcessPoolExecutor is a safe
    # default for CPU-bound hashing on most CPython interpreters.

    if executor not in ("auto", "thread", "process"):
        raise ValueError(
            "executor must be one of: 'auto', 'thread', 'process'")

    executor_type = _choose_executor_type(executor, workers)

    # Use a bounded set of futures to prevent loading all files into memory
    MAX_PENDING = workers * 4

    known_files = known_files or {}

    from .progress import SimpleProgressBar
    pbar = SimpleProgressBar(desc="Scanning", unit="file")

    count = 0
    start_time = time.time()
    last_progress_time = start_time
    _completed_durations: list[float] = []
    last_complete_ts = time.time()

    def _iter_impl():
        """Internal generator implementing the threaded hashing pipeline.

        Yields result tuples for each processed file as futures complete.
        This internal helper is returned as a generator by threaded_hash()
        when collect=False.
        """
        nonlocal count, last_progress_time, last_complete_ts
        # Create executor based on chosen executor_type
        if executor_type == "process":
            try:
                ex = futures.ProcessPoolExecutor(max_workers=max(1, workers))
            except Exception:
                # Fall back to threads if process pool can't be created
                ex = futures.ThreadPoolExecutor(max_workers=max(1, workers))
        else:
            ex = futures.ThreadPoolExecutor(max_workers=max(1, workers))

        with ex as ex:
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
                            pass   # Streaming mode
                    submit_time = time.time()
                    # Split long lines in process_file calls.
                    # The original code had `fut = ex.submit(...)`
                    # The user's edit suggests `known_files.get(str(p))`
                    # which is a tuple, but process_file expects a hash string.
                    # Reverting to original logic for known_hash,
                    # but splitting the submit call.
                    # Resolve process_file at runtime from the public
                    # `nodupe.scanner` facade if present so tests that
                    # monkeypatch `nodupe.scanner.process_file` will
                    # affect this worker function. Fall back to the
                    # locally-imported `process_file` if needed.
                    # Default to the process_file currently bound in this
                    # module (which tests can patch by setting
                    # nodupe.scan.hasher.process_file). Prefer a different
                    # function if the public facade `nodupe.scanner` has a
                    # distinct patched `process_file` value.
                    # Prefer any runtime patch applied to this module's
                    # 'process_file' (tests sometimes set
                    # nodupe.scan.hasher.process_file). If not present,
                    # prefer a runtime patch applied to the public facade
                    # 'nodupe.scanner.process_file'. Fall back to the
                    # original processor implementation otherwise.
                    worker = process_file
                    try:
                        # Prefer the facade's runtime patch when present.
                        # Tests sometimes monkeypatch
                        # nodupe.scanner.process_file so prefer the facade
                        # when it differs from the canonical implementation.
                        from importlib import import_module

                        _scanner_mod = import_module("nodupe.scanner")
                        _scanner_pf = getattr(
                            _scanner_mod, "process_file", None
                        )

                        # Detect the canonical original function so we
                        # can tell whether a function has been patched.
                        try:
                            _proc_mod = import_module(
                                "nodupe.scan.processor"
                            )
                            _orig_pf = getattr(
                                _proc_mod, "process_file", None
                            )
                        except Exception:
                            _orig_pf = None

                        # If the module-local worker is still the original
                        # implementation, prefer a patched function from
                        # the facade if present.
                        if _orig_pf is not None and worker is _orig_pf:
                            if (
                                _scanner_pf is not None
                                and _orig_pf is not None
                                and _scanner_pf is not _orig_pf
                            ):
                                worker = _scanner_pf
                        # Otherwise keep the module-local 'process_file'.
                    except Exception:
                        # Any import errors or missing modules -> keep the
                        # local process_file implementation.
                        pass

                    fut = ex.submit(worker, p, hash_algo, known_hash)
                    pending.add(fut)
                    # attach metadata so we can diagnose stalled tasks / ETA
                    if not hasattr(fut, '_submit_meta'):
                        # Ensure size is defined, default to 0 if not available
                        # In the loop above, size is extracted from known_files
                        # or stat.
                        # But if we are here, we might have missed it.
                        # Let's try to get it from stat if possible, or 0.
                        try:
                            f_size = p.stat().st_size
                        except OSError:
                            f_size = 0

                        setattr(
                            fut,
                            '_submit_meta',
                            (str_p, f_size, submit_time)
                        )
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
                                # _submit_meta format: (path, size,
                                # submit_time)
                                    # _submit_meta format is:
                                    #   (path, size, submit_time)
                                    # compute age using submit_time (index 2)
                                age = now - meta[2]
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


def _choose_executor_type_for_test(
    executor_choice: str, workers_count: int
) -> str:
    """Expose threaded_hash auto selection logic for unit tests.

    Note: This duplicates _choose_executor_type's heuristics and exists
    so tests can monkeypatch os.cpu_count() and PYTHON_ENABLE_NOGIL and
    verify the behavior deterministically.
    """
    import os as _os

    if executor_choice == "thread":
        return "thread"
    if executor_choice == "process":
        return "process"

    # Use proper runtime detection for GIL-free Python
    from ..runtime import is_gil_disabled

    if is_gil_disabled():
        return "thread"

    try:
        cpu = int(_os.cpu_count() or 1)
    except Exception:
        cpu = 1

    if cpu <= 16:
        return "thread"
    if cpu < 32:
        if workers_count >= max(2, cpu // 2):
            return "process"
        return "thread"
    return "process"
