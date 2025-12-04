# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Startup integrity checking and bootstrapping.

This module provides utilities for verifying the integrity of the
codebase at startup and shutdown. It performs syntax checking on
all Python files to ensure no corrupted or invalid code is present.

Key Features:
    - Recursive syntax checking of Python files
    - Fast fail on syntax errors
    - Used by CLI for self-validation

Functions:
    - lint_tree: Check syntax of all .py files in a directory

Example:
    >>> from pathlib import Path
    >>> lint_tree(Path("./nodupe"))
"""
from pathlib import Path


def lint_tree(module_dir: Path) -> None:
    """Recursively check syntax of all Python files in directory.

    Attempts to compile each .py file to detect syntax errors.
    Raises SyntaxError immediately if any file is invalid.

    Args:
        module_dir: Root directory to scan for .py files

    Raises:
        SyntaxError: If any file contains invalid syntax
        OSError: If file reading fails
    """
    py_files = list(module_dir.rglob("*.py"))
    for p in py_files:
        source = p.read_text(encoding="utf-8")
        # compile will raise SyntaxError when a file contains a syntax issue
        compile(source, str(p), 'exec')


__all__ = ["lint_tree"]
