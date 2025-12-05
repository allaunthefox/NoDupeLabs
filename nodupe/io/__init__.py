# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""I/O abstractions package.

Provides file I/O interfaces for testable operations.

Public API:
    - FileWriter: Abstract file writer
    - RealFileWriter: Filesystem implementation
    - MemoryFileWriter: In-memory implementation for testing
"""
from .writers import FileWriter, RealFileWriter, MemoryFileWriter

__all__ = [
    "FileWriter",
    "RealFileWriter",
    "MemoryFileWriter",
]
