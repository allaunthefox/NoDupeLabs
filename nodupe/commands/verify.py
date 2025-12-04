# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import json
from pathlib import Path

def cmd_verify(args, _cfg):
    """Verify command - check checkpoint integrity."""
    cp = Path(args.checkpoint)
    if not cp.exists():
        print(f"[verify] checkpoint not found: {cp}")
        return 1

    manifest = json.loads(cp.read_text(encoding="utf-8"))
    moves = manifest.get("moves", [])
    missing = []
    
    print(f"[verify] Checking {len(moves)} moves in checkpoint...")
    
    for mv in moves:
        dst = Path(mv["dst"])
        if not dst.exists():
            missing.append(str(dst))
            print(f"[verify][FAIL] Missing destination file: {dst}")
            
    if missing:
        print(f"[verify] FAILED. {len(missing)} files missing.")
        return 1
        
    print("[verify] OK. All destination files exist.")
    return 0
