# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import sys
from pathlib import Path
from ..config import ensure_config

def cmd_init(args, _cfg):
    """Initialize configuration with a preset."""
    p = Path("nodupe.yml")
    if p.exists() and not args.force:
        print(f"[init] Config file {p} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1
    
    if args.force and p.exists():
        p.unlink()
        
    ensure_config("nodupe.yml", preset=args.preset)
    print(f"[init] Created nodupe.yml using '{args.preset}' preset.")
    return 0
