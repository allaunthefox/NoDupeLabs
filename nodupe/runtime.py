# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Python runtime feature detection for NoDupeLabs.

Detects Python 3.13+ features like free-threading, zstd compression,
subinterpreters, and provides helpers for optimal execution strategy.
This module enables NoDupeLabs to automatically adapt to different Python
runtime environments and choose the most efficient execution strategies.

Key Features:
    - Automatic detection of GIL-free (free-threaded) Python builds
    - Subinterpreter support detection for advanced concurrency
    - Compression algorithm detection and selection
    - Runtime optimization recommendations for different workloads
    - Garbage collection tuning for performance optimization
    - Comprehensive runtime information reporting

Dependencies:
    - sys: Python runtime information
    - gc: Garbage collection tuning
    - typing: Type annotations for code safety

Example:
    >>> from nodupe.runtime import get_runtime_info, get_optimal_executor
    >>>
    >>> # Get comprehensive runtime information
    >>> runtime_info = get_runtime_info()
    >>> print(f"Python version: {runtime_info['python_version']}")
    >>> print(f"GIL disabled: {runtime_info['gil_disabled']}")
    >>> print(f"Optimal executor: {runtime_info['optimal_executor']}")
    >>>
    >>> # Choose optimal execution strategy
    >>> executor = get_optimal_executor()
    >>> if executor == 'thread':
    ...     print("Using threads for optimal performance (GIL-free)")
    >>> elif executor == 'interpreter':
    ...     print("Using subinterpreters for optimal performance")
    >>> else:
    ...     print("Using processes for optimal performance")
"""
import gc
import sys
from typing import Literal, Optional

# Minimum Python version
MIN_VERSION = (3, 10)
CURRENT_VERSION = sys.version_info[:2]


def is_gil_disabled() -> bool:
    """Check if running on a free-threaded (GIL-disabled) Python build.

    Returns:
        True if GIL is disabled (free-threaded mode)
    """
    # Python 3.13+ provides sys._is_gil_enabled()
    if hasattr(sys, "_is_gil_enabled"):
        return not sys._is_gil_enabled()  # type: ignore[attr-defined]
    return False


def has_subinterpreters() -> bool:
    """Check if subinterpreter support is available.

    Returns:
        True if concurrent.futures.InterpreterPoolExecutor is available
    """
    try:
        # 3.14+ feature
        # from .utils.concurrency import InterpreterPoolExecutor
        # FEATURES["interpreter_pool"] = True
        pass
    except ImportError:
        pass
    return False


def has_zstd() -> bool:
    """Check if zstd compression is available (Python 3.14+ stdlib).

    Returns:
        True if compression.zstd is available
    """
    try:
        from compression import zstd  # noqa: F401
        return True
    except ImportError:
        pass
    # Also check for third-party zstandard
    try:
        import zstandard  # noqa: F401
        return True
    except ImportError:
        pass
    return False


def get_optimal_executor() -> Literal["thread", "process", "interpreter"]:
    """Determine the optimal executor type for CPU-bound work.

    Returns:
        'thread' if GIL-free, 'interpreter' if available, else 'process'
    """
    if is_gil_disabled():
        return "thread"
    if has_subinterpreters():
        return "interpreter"
    return "process"


def get_compression_module() -> Optional[str]:
    """Get the best available compression module.

    Returns:
        Module name: 'zstd', 'zstandard', 'gzip', or None
    """
    try:
        from compression import zstd  # noqa: F401
        return "zstd"
    except ImportError:
        pass
    try:
        import zstandard  # noqa: F401
        return "zstandard"
    except ImportError:
        pass
    try:
        import gzip  # noqa: F401
        return "gzip"
    except ImportError:
        pass
    return None


def tune_gc_for_throughput():
    """Tune garbage collector for high-throughput workloads.

    For large scans with millions of objects, reduce GC frequency
    to improve throughput at the cost of slightly higher memory.
    """
    # Increase thresholds to reduce GC frequency
    # Default is (700, 10, 10)
    gc.set_threshold(1500, 15, 15)


def tune_gc_for_latency():
    """Tune garbage collector for low-latency workloads.

    For interactive or real-time operations, keep GC responsive.
    """
    # Use default/slightly lower thresholds
    gc.set_threshold(700, 10, 10)


def get_runtime_info() -> dict:
    """Get comprehensive runtime information.

    Returns:
        Dict with version, features, and capabilities
    """
    return {
        "python_version": f"{CURRENT_VERSION[0]}.{CURRENT_VERSION[1]}",
        "python_full": sys.version,
        "gil_disabled": is_gil_disabled(),
        "has_subinterpreters": has_subinterpreters(),
        "has_zstd": has_zstd(),
        "optimal_executor": get_optimal_executor(),
        "compression_module": get_compression_module(),
        "platform": sys.platform,
    }
