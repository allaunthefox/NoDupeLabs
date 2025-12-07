# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Unified telemetry for logging and metrics.

Provides a single interface for logging events, recording metrics,
and tracking performance statistics.
"""
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MetricValue:
    """A single metric value with timestamp.

    This dataclass captures a single recorded metric sample. It is used by
    Telemetry to maintain a short history of metric events that can be
    exported for inspection.

    Attributes:
        name: Metric name (e.g. 'files.scanned').
        value: Numeric value stored for this metric sample.
        timestamp: POSIX timestamp when the sample was recorded.
        tags: Optional key/value tags providing extra context.
    """

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


class Telemetry:
    """Unified telemetry for logging and metrics.

    Combines logging and metrics collection into a single interface.
    Supports structured logging, metric recording, and metric export.

    Example:
        >>> telem = Telemetry(name="nodupe.scanner")
        >>> telem.info("Starting scan", root="/data")
        >>> telem.counter("files_scanned", 100)
        >>> telem.gauge("memory_mb", 256.5)
        >>> telem.export_metrics(Path("metrics.json"))
    """

    def __init__(
        self,
        name: str = "nodupe",
        level: int = logging.INFO,
        log_file: Optional[Path] = None,
        log_dir: Optional[Path] = None,
        metrics_path: Optional[Path] = None
    ):
        """Initialize telemetry.

        Args:
            name: Logger name
            level: Logging level
            log_file: Optional file for standard log output
            log_dir: Optional directory for JSONL structured logs
            metrics_path: Optional path for metrics JSON export
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            formatter = logging.Formatter(
                "[%(name)s][%(levelname)s] %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Add file handler if requested
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(logging.Formatter(
                "%(asctime)s [%(name)s][%(levelname)s] %(message)s"
            ))
            self.logger.addHandler(fh)

        # Initialize legacy/structured logger if requested
        self._jsonl: Optional[Any] = None
        if log_dir:
            try:
                from .logger import JsonlLogger
                self._jsonl = JsonlLogger(log_dir)
            except ImportError:
                pass

        self.metrics_path = metrics_path
        self._metrics: List[MetricValue] = []
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._start_times: Dict[str, float] = {}

    def log(self, level: str, event: str, **kwargs: Any):
        """Unified log that writes to both standard and JSONL loggers.

        This helper writes a readable message to the configured standard
        logger and also emits a structured event to the optional JSONL
        logger (when configured).

        Args:
            level: Log level name (e.g. "INFO", "DEBUG").
            event: Short event name describing the logged event.
            **kwargs: Additional structured context to include with the
                event for later parsing/analysis.
        """
        # Log to standard logger
        lvl = getattr(logging, level.upper(), logging.INFO)
        msg = self._format_msg(f"[{event}]", kwargs)
        self.logger.log(lvl, msg)

        # Log to JSONL logger
        if self._jsonl:
            self._jsonl.log(level, event, **kwargs)

    def save(self):
        """Persist recorded metrics to the configured metrics path.

        This method is an alias for :py:meth:`export_metrics`. If
        no :attr:`metrics_path` was configured during Telemetry
        initialization, this method is a no-op.
        """
        if self.metrics_path:
            self.export_metrics(self.metrics_path)

    # Logging methods
    def debug(self, msg: str, **kwargs: Any):
        """Log a debug-level telemetry message.

        Args:
            msg: Human-readable message text.
            **kwargs: Optional structured key/value pairs attached to the
                event (useful for automated log analysis).
        """
        self.logger.debug(self._format_msg(msg, kwargs))

    def info(self, msg: str, **kwargs: Any):
        """Log an informational telemetry message.

        Args:
            msg: Human-readable message text.
            **kwargs: Optional structured context fields.
        """
        self.logger.info(self._format_msg(msg, kwargs))

    def warning(self, msg: str, **kwargs: Any):
        """Log a warning telemetry event.

        Args:
            msg: Warning message text.
            **kwargs: Optional structured context fields.
        """
        self.logger.warning(self._format_msg(msg, kwargs))

    def error(self, msg: str, **kwargs: Any):
        """Log an error-level telemetry event.

        Args:
            msg: Error message text.
            **kwargs: Optional structured context fields.
        """
        self.logger.error(self._format_msg(msg, kwargs))

    def _format_msg(self, msg: str, data: Dict[str, Any]) -> str:
        """Format message with structured data.

        Args:
            msg: Base message text.
            data: Structured data mapping to append to the message.

        Returns:
            str: Formatted message string.
        """
        if not data:
            return msg
        pairs = " ".join(f"{k}={v}" for k, v in data.items())
        return f"{msg} | {pairs}"

    # Metric methods
    def counter(self, name: str, value: float = 1, **tags: str):
        """Increment a counter metric and record a sample.

        Args:
            name: Metric name.
            value: Amount to increment by (default 1).
            **tags: Optional tags attached to this metric sample.
        """
        self._counters[name] = self._counters.get(name, 0) + value
        self._metrics.append(MetricValue(
            name, self._counters[name], tags=tags))

    def gauge(self, name: str, value: float, **tags: str):
        """Set a gauge metric and record a sample.

        Args:
            name: Gauge metric name.
            value: Numeric value for the gauge.
            **tags: Optional tags attached to this sample.
        """
        self._gauges[name] = value
        self._metrics.append(MetricValue(name, value, tags=tags))

    def timer_start(self, name: str):
        """Start a named timer used to measure durations.

        Args:
            name: Logical timer name used to correlate start/stop.
        """
        self._start_times[name] = time.time()

    def timer_stop(self, name: str) -> float:
        """Stop a previously started timer and record the elapsed time.

        Args:
            name: Timer name that was previously started.

        Returns:
            float: Duration in seconds measured for the timer, or 0.0 if
            the timer was not found.
        """
        if name not in self._start_times:
            return 0.0
        duration = time.time() - self._start_times.pop(name)
        self.gauge(f"{name}_duration_s", duration)
        return duration

    def get_counter(self, name: str) -> float:
        """Return the current value of a named counter.

        Args:
            name: Counter metric name.

        Returns:
            float: Current counter value, or 0 if not present.
        """
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """Return the current value of a named gauge.

        Args:
            name: Gauge metric name.

        Returns:
            float: Current gauge value, or 0.0 if not present.
        """
        return self._gauges.get(name, 0.0)

    def export_metrics(self, path: Path):
        """Persist current metrics and history to a JSON file.

        Args:
            path: File path to write the JSON payload to. Intermediate
                directories are created automatically.
        """
        data = {
            "counters": self._counters,
            "gauges": self._gauges,
            "history": [
                {
                    "name": m.name,
                    "value": m.value,
                    "timestamp": m.timestamp,
                    "tags": m.tags
                }
                for m in self._metrics
            ]
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def reset(self):
        """Reset all in-memory telemetry counters, gauges and samples.

        Use this primarily in tests or when a full reset of runtime
        telemetry state is required.
        """
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()
        self._start_times.clear()


# Default global telemetry instance
_default_telemetry: Optional[Telemetry] = None


def get_telemetry(name: str = "nodupe") -> Telemetry:
    """Return (and lazily create) the global Telemetry instance.

    Args:
        name: Optional name to use when creating a new Telemetry logger
            (defaults to 'nodupe').

    Returns:
        Telemetry: Global singleton telemetry instance.
    """
    global _default_telemetry
    if _default_telemetry is None:
        _default_telemetry = Telemetry(name=name)
    return _default_telemetry
