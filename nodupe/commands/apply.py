# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import csv
from pathlib import Path
from ..applier import apply_moves


def cmd_apply(args, cfg):
    """Apply command."""
    # Re-implement CSV reading here since applier expects list of dicts
    rows = []
    with Path(args.plan).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    res = apply_moves(
        rows, Path(args.checkpoint),
        dry_run=(cfg["dry_run"] and not args.force)
    )
    print(f"[apply] {res}")
    return 0 if res["errors"] == 0 else 1
