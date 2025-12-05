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
    """A single metric value with timestamp."""

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
        log_file: Optional[Path] = None
    ):
        """Initialize telemetry.

        Args:
            name: Logger name
            level: Logging level
            log_file: Optional file for log output
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

        self._metrics: List[MetricValue] = []
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._start_times: Dict[str, float] = {}

    # Logging methods
    def debug(self, msg: str, **kwargs: Any):
        """Log debug message with optional structured data."""
        self.logger.debug(self._format_msg(msg, kwargs))

    def info(self, msg: str, **kwargs: Any):
        """Log info message with optional structured data."""
        self.logger.info(self._format_msg(msg, kwargs))

    def warning(self, msg: str, **kwargs: Any):
        """Log warning message with optional structured data."""
        self.logger.warning(self._format_msg(msg, kwargs))

    def error(self, msg: str, **kwargs: Any):
        """Log error message with optional structured data."""
        self.logger.error(self._format_msg(msg, kwargs))

    def _format_msg(self, msg: str, data: Dict[str, Any]) -> str:
        """Format message with structured data."""
        if not data:
            return msg
        pairs = " ".join(f"{k}={v}" for k, v in data.items())
        return f"{msg} | {pairs}"

    # Metric methods
    def counter(self, name: str, value: float = 1, **tags: str):
        """Increment a counter metric."""
        self._counters[name] = self._counters.get(name, 0) + value
        self._metrics.append(MetricValue(
            name, self._counters[name], tags=tags))

    def gauge(self, name: str, value: float, **tags: str):
        """Set a gauge metric."""
        self._gauges[name] = value
        self._metrics.append(MetricValue(name, value, tags=tags))

    def timer_start(self, name: str):
        """Start a timer."""
        self._start_times[name] = time.time()

    def timer_stop(self, name: str) -> float:
        """Stop a timer and record duration."""
        if name not in self._start_times:
            return 0.0
        duration = time.time() - self._start_times.pop(name)
        self.gauge(f"{name}_duration_s", duration)
        return duration

    def get_counter(self, name: str) -> float:
        """Get current counter value."""
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """Get current gauge value."""
        return self._gauges.get(name, 0.0)

    def export_metrics(self, path: Path):
        """Export metrics to JSON file."""
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
        """Reset all metrics."""
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()
        self._start_times.clear()


# Default global telemetry instance
_default_telemetry: Optional[Telemetry] = None


def get_telemetry(name: str = "nodupe") -> Telemetry:
    """Get or create a telemetry instance."""
    global _default_telemetry
    if _default_telemetry is None:
        _default_telemetry = Telemetry(name=name)
    return _default_telemetry
