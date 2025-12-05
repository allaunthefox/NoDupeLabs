# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Scan argument validation.

Validates scan command arguments and configuration before execution.
Ensures all preconditions are met (paths exist, DB writable, etc.).
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple


class ScanValidator:
    """Validates scan command preconditions."""

    def validate(
        self,
        roots: List[str],
        db_path: Path,
        log_dir: Path,
        metrics_path: Path
    ) -> Tuple[bool, List[str]]:
        """Validate scan preconditions.

        Args:
            roots: Root directories to scan
            db_path: Database file path
            log_dir: Log directory path
            metrics_path: Metrics file path

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Validate roots exist
        for root in roots:
            p = Path(root)
            if not p.exists():
                errors.append(f"Root path does not exist: {root}")
            elif not os.access(p, os.R_OK):
                errors.append(f"Root path is not readable: {root}")

        # Validate DB path writable
        if db_path.exists():
            if not os.access(db_path, os.W_OK):
                errors.append(f"Database not writable: {db_path}")
        else:
            # Check parent writability
            parent = db_path.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    errors.append(f"Cannot create DB directory {parent}: {e}")
            elif not os.access(parent, os.W_OK):
                errors.append(f"DB directory not writable: {parent}")

        # Validate log dir writable
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                errors.append(f"Cannot create log directory {log_dir}: {e}")
        elif not os.access(log_dir, os.W_OK):
            errors.append(f"Log directory not writable: {log_dir}")

        # Validate metrics path writable
        metrics_parent = metrics_path.parent
        if not metrics_parent.exists():
            try:
                metrics_parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                errors.append(
                    f"Cannot create metrics directory {metrics_parent}: {e}")
        elif not os.access(metrics_parent, os.W_OK):
            errors.append(f"Metrics directory not writable: {metrics_parent}")

        return (len(errors) == 0, errors)
