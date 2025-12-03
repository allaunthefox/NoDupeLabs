# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from pathlib import Path
import csv
from typing import Dict, Iterable

def ensure_unique(p: Path) -> Path:
    p = Path(p)
    if not p.exists():
        return p
    base = p.stem
    suffix = p.suffix
    parent = p.parent
    i = 1
    while True:
        cand = parent / f"{base}-{i}{suffix}"
        if not cand.exists():
            return cand
        i += 1

def write_plan_csv(rows: Iterable[Dict], out_path: Path) -> None:
    rows = list(rows)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return

    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
