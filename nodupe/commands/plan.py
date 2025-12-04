# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from pathlib import Path
from datetime import datetime, timezone
from ..db import DB
from ..planner import ensure_unique, write_plan_csv


def cmd_plan(args, cfg):
    """Plan command."""
    db = DB(Path(cfg["db_path"]))
    dups = db.get_duplicates()
    ts = datetime.now(timezone.utc).isoformat()
    rows = []
    rbk = 0

    for sha, context_tag, paths_csv in dups:
        paths = sorted(paths_csv.split("|"))
        # Keep first, move rest
        for src in paths[1:]:
            srcp = Path(src)
            dup_dir = srcp.parent / ".nodupe_duplicates"
            dst = ensure_unique(dup_dir / srcp.name)

            rows.append({
                "status": "planned",
                "op": "move",
                "src_path": src,
                "dst_path": str(dst),
                "content_id": f"nd:hash:{sha}:ctx:{context_tag}",
                "reason": "dedup",
                "rollback_key": f"rbk:{rbk:06d}",
                "ts": ts
            })
            rbk += 1

    write_plan_csv(rows, Path(args.out))
    print(
        f"[plan] duplicate_groups={len(dups)} planned_ops={len(rows)} -> "
        f"{args.out}"
    )
    return 0
