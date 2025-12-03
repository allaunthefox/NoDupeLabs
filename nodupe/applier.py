# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import shutil
import json
import time
from pathlib import Path
from typing import List, Dict

def apply_moves(rows: List[Dict], checkpoint_path: Path, dry_run: bool = True) -> Dict:
    """
    Execute moves with three-phase commit (Prepare, Execute, Commit).
    """
    results = {"success": 0, "errors": 0, "skipped": 0}
    manifest = {
        "ts": time.time(),
        "moves": []
    }

    # 1. Prepare & Validate
    valid_moves = []
    for row in rows:
        if row.get("op") != "move":
            continue
        
        src = Path(row["src_path"])
        dst = Path(row["dst_path"])
        
        if not src.exists():
            print(f"[apply][SKIP] Source missing: {src}")
            results["skipped"] += 1
            continue
            
        if dst.exists():
            print(f"[apply][SKIP] Destination exists: {dst}")
            results["skipped"] += 1
            continue
            
        valid_moves.append((src, dst, row))

    if dry_run:
        print(f"[apply] Dry run: would move {len(valid_moves)} files.")
        return results

    # 2. Execute
    for src, dst, row in valid_moves:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            
            manifest["moves"].append({
                "src": str(src),
                "dst": str(dst),
                "ts": time.time()
            })
            results["success"] += 1
        except OSError as e:
            print(f"[apply][ERROR] Failed to move {src} -> {dst}: {e}")
            results["errors"] += 1

    # 3. Checkpoint
    if checkpoint_path:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return results
