# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Progress tracking utilities.

Provides the ProgressTracker class for monitoring scan progress
and detecting stalls.
"""
import sys
import time
from typing import Any, List, Optional


class SimpleProgressBar:
    """A simple progress bar using standard library only.

    Mimics a subset of tqdm interface for drop-in replacement.
    """

    def __init__(self, desc: str = "Processing", unit: str = "items"):
        self.desc = desc
        self.unit = unit
        self.count = 0
        self.start_time = time.time()
        self._last_len = 0

    def update(self, n: int = 1):
        """Update progress counter."""
        self.count += n
        self._refresh()

    def write(self, msg: str):
        """Print message above progress bar."""
        # Print the message to stdout as well as stderr so that test
        # capture plugins reliably observe it even when the progress
        # bar is controlling stderr with carriage-returns.
        try:
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()
        except Exception:
            pass

        # Clear line on stderr and print message there too
        sys.stderr.write("\r" + " " * self._last_len + "\r")
        sys.stderr.write(msg + "\n")
        self._refresh()

    def close(self):
        """Clean up progress bar."""
        sys.stderr.write("\n")

    def _refresh(self):
        """Redraw progress bar."""
        elapsed = time.time() - self.start_time
        rate = self.count / elapsed if elapsed > 0 else 0

        # Format time as MM:SS
        mins, secs = divmod(int(elapsed), 60)
        time_str = f"{mins:02d}:{secs:02d}"

        line = (
            f"{self.desc}: {self.count}{self.unit} "
            f"[{time_str}, {rate:.2f}{self.unit}/s]"
        )

        # Pad with spaces to clear previous longer lines
        if len(line) < self._last_len:
            line += " " * (self._last_len - len(line))

        self._last_len = len(line)
        sys.stderr.write("\r" + line)
        sys.stderr.flush()


class ProgressTracker:
    """Tracks progress and detects stalls during scanning.

    Monitors task completion, calculates ETAs, and detects
    when the pipeline appears stuck.

    Attributes:
        heartbeat_interval: Time between progress checks
        stall_timeout: Per-task stall threshold
        max_idle_time: Hard idle timeout
        show_eta: Whether to show ETA messages
    """

    def __init__(
        self,
        heartbeat_interval: float = 10.0,
        stall_timeout: Optional[float] = None,
        max_idle_time: Optional[float] = 300.0,
        show_eta: bool = True,
        pbar: Optional[Any] = None
    ):
        """Initialize progress tracker.

        Args:
            heartbeat_interval: Time between progress checks (seconds)
            stall_timeout: Per-task stall threshold (seconds)
            max_idle_time: Hard idle timeout (seconds)
            show_eta: Whether to show ETA messages
            pbar: Optional tqdm progress bar
        """
        self.heartbeat_interval = heartbeat_interval
        self.stall_timeout = stall_timeout
        self.max_idle_time = max_idle_time
        self.show_eta = show_eta
        self.pbar = pbar

        self.start_time = time.time()
        self.last_complete_ts = time.time()
        self.completed_durations: List[float] = []
        self.count = 0

    def get_wait_timeout(self) -> float:
        """Get effective timeout for waiting on tasks."""
        if self.stall_timeout is not None:
            return self.stall_timeout
        return self.heartbeat_interval

    def record_completion(self, submit_time: Optional[float] = None):
        """Record a task completion.

        Args:
            submit_time: When the task was submitted
        """
        now = time.time()
        if submit_time:
            self.completed_durations.append(max(0.0, now - submit_time))
        else:
            self.completed_durations.append(
                max(0.0, now - self.last_complete_ts)
            )
        self.last_complete_ts = now
        self.count += 1

        if self.pbar is not None:
            self.pbar.update(1)
        elif self.count % 100 == 0:
            print(f"[scanner] Processed {self.count}...", file=sys.stderr)

    def check_stall(self, pending_count: int, pending_tasks: set):
        """Check for stalled tasks and report progress.

        Args:
            pending_count: Number of pending tasks
            pending_tasks: Set of pending futures with _submit_meta

        Raises:
            TimeoutError: If max_idle_time exceeded
        """
        now = time.time()
        elapsed = now - self.start_time

        # Calculate ETA if we have history
        avg = None
        if self.completed_durations:
            avg = sum(self.completed_durations) / len(self.completed_durations)

        # Build message
        if self.show_eta and avg:
            workers = max(1, pending_count // 4)  # Estimate workers
            est = avg * pending_count / workers
            msg = (
                f"[scanner][ETA] approx {round(est, 3)}s for "
                f"{pending_count} pending tasks (elapsed={elapsed:.1f}s)"
            )
        elif self.show_eta:
            msg = (
                f"[scanner][STALL] no tasks completed in "
                f"{self.get_wait_timeout()}s; {pending_count} pending "
                f"(elapsed={elapsed:.1f}s)"
            )
        else:
            msg = (
                f"[scanner][INFO] no progress in "
                f"{self.get_wait_timeout()}s; pending={pending_count}"
            )

        self._print_message(msg)

        # Check for long-running tasks
        if self.stall_timeout is not None:
            oldest = self._find_oldest_stalled(pending_tasks, now)
            if oldest:
                warn = (
                    f"[scanner][WARN] Task stalled "
                    f"{oldest[0]:.1f}s for: {oldest[1]}"
                )
                self._print_message(warn)

        # Enforce hard idle timeout
        idle_time = now - self.last_complete_ts
        if self.max_idle_time is not None and idle_time >= self.max_idle_time:
            raise TimeoutError(
                f"scanner: no tasks completed for {idle_time:.3f}s "
                f"(max_idle_time={self.max_idle_time})"
            )

    def _find_oldest_stalled(
        self, pending_tasks: set, now: float
    ) -> Optional[tuple]:
        """Find the oldest stalled task."""
        oldest = None
        for task in pending_tasks:
            meta = getattr(task, '_submit_meta', None)
            if not meta:
                continue
            age = now - meta[1]
            if self.stall_timeout and age >= self.stall_timeout:
                if not oldest or age > oldest[0]:
                    oldest = (age, meta[0])
        return oldest

    def _print_message(self, msg: str):
        """Print a message to stderr or progress bar."""
        if self.pbar is not None:
            try:
                # Use the progress bar to show the message normally, but
                # also write the message to stdout so capturing systems
                # (like pytest's capsys) reliably see the message even when
                # the progress bar prints carriage-returns which can hide
                # earlier output in terminal-like streams.
                self.pbar.write(msg)
            except Exception:
                print(msg, file=sys.stderr)
            try:
                # Duplicate to stdout as well so tests that capture stdout
                # will see the stall/ETA messages. Keep this write separate
                # and best-effort — it should never break production flows.
                sys.stdout.write(msg + "\n")
                sys.stdout.flush()
            except Exception:
                # If stdout isn't available for some reason, ignore.
                pass
        else:
            print(msg, file=sys.stderr)
