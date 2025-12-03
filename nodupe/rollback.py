# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import shutil
import json
from pathlib import Path
from typing import Dict

def rollback_from_checkpoint(checkpoint_path: Path) -> Dict:
    if not checkpoint_path.exists():
        return {"errors": 1, "msg": "Checkpoint not found"}

    try:
        manifest = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"errors": 1, "msg": "Invalid checkpoint JSON"}

    moves = manifest.get("moves", [])
    # Reverse order for rollback
    moves.reverse()
    
    results = {"restored": 0, "errors": 0}
    
    for mv in moves:
        src_orig = Path(mv["src"]) # Where it was
        dst_curr = Path(mv["dst"]) # Where it is now
        
        if not dst_curr.exists():
            print(f"[rollback][WARN] Current file missing: {dst_curr}")
            results["errors"] += 1
            continue
            
        if src_orig.exists():
            print(f"[rollback][WARN] Original location occupied: {src_orig}")
            results["errors"] += 1
            continue
            
        try:
            src_orig.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst_curr), str(src_orig))
            results["restored"] += 1
        except OSError as e:
            print(f"[rollback][ERROR] Failed to restore {dst_curr} -> {src_orig}: {e}")
            results["errors"] += 1
            
    return results
