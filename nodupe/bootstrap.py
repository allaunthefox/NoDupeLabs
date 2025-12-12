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

    This function performs comprehensive syntax checking by attempting
    to compile each Python file in the specified directory tree. It
    serves as a startup validation to ensure no corrupted or invalid
    Python code is present in the codebase.

    Args:
        module_dir: Root directory to scan for .py files

    Raises:
        SyntaxError: If any file contains invalid syntax
        OSError: If file reading fails
        UnicodeDecodeError: If file encoding is invalid

    Example:
        >>> from pathlib import Path
        >>> from nodupe.bootstrap import lint_tree
        >>> lint_tree(Path("./nodupe"))
        # Raises SyntaxError if any invalid Python files are found
    """
    py_files = list(module_dir.rglob("*.py"))
    for p in py_files:
        source = p.read_text(encoding="utf-8")
        # compile will raise SyntaxError when a file contains a syntax issue
        compile(source, str(p), 'exec')


__all__ = ["lint_tree"]
