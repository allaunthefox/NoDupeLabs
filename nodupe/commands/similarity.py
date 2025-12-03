# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import sys
from pathlib import Path
from ..similarity.cli import build_index_from_db, find_near_duplicates

def cmd_similarity_build(args, cfg):
    db_path = Path(cfg['db_path'])
    res = build_index_from_db(db_path, dim=args.dim, out_path=args.out)
    print(f"[similarity] index_count={res['index_count']}")
    return 0

def cmd_similarity_query(args, cfg):
    db_path = Path(cfg['db_path'])
    target = Path(args.file)
    res = find_near_duplicates(db_path, target, k=args.k, dim=args.dim, index_path=args.index_file)
    for path, score in res:
        print(f"{score:>12.6f} {path}")
    return 0

def cmd_similarity_update(args, cfg):
    from ..similarity.cli import update_index_from_db as _update
    db_path = Path(cfg['db_path'])
    if not args.index_file:
        print("[similarity][update] --index-file is required", file=sys.stderr)
        return 2
    res = _update(db_path, args.index_file, remove_missing=args.rebuild)
    print(f"[similarity][update] added={res.get('added')} index_count={res.get('index_count')}")
    return 0
