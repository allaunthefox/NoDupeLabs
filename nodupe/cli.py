# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import argparse
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import atexit

from .bootstrap import lint_tree
from .deps import init_deps
from .config import load_config
from .db import DB
from .scanner import threaded_hash, validate_hash_algo
from .exporter import write_folder_meta
from .ai.backends import choose_backend
from .planner import ensure_unique, write_plan_csv
from .applier import apply_moves
from .rollback import rollback_from_checkpoint
from .mount import mount_fs
from .similarity.cli import build_index_from_db, find_near_duplicates
from .logger import JsonlLogger
from .metrics import Metrics
from .archiver import ArchiveHandler

__version__ = "0.1.0"

def cmd_scan(args, cfg):
    """Scan command."""
    db = DB(Path(cfg["db_path"]))
    logger = JsonlLogger(Path(cfg["log_dir"]))
    metrics = Metrics(Path(cfg["metrics_path"]))

    logger.log("INFO", "scan_start", roots=list(args.root))

    try:
        hash_algo = validate_hash_algo(cfg.get("hash_algo", "sha512"))
    except ValueError as e:
        print(f"[fatal] Configuration error: {e}", file=sys.stderr)
        return 1

    records, dur, total = threaded_hash(
        args.root,
        cfg["ignore_patterns"],
        workers=cfg["parallelism"],
        hash_algo=hash_algo,
        follow_symlinks=cfg.get("follow_symlinks", False)
    )

    db.upsert_files(records)

    # Precompute embeddings for images (incremental)
    try:
        sim_dim = int(cfg.get("similarity", {}).get("dim", 16))
        model_hint = cfg.get("ai", {}).get("model_path")
        be = choose_backend(model_hint)
        updated = 0
        for rec in records:
            p = rec[0]
            mime = rec[4]
            mtime = rec[2]
            if not mime or not mime.startswith("image/"):
                continue

            existing = db.get_embedding(p)
            if existing and existing.get("mtime") == int(mtime) and existing.get("dim") == sim_dim:
                continue

            # compute embedding and store
            try:
                vec = be.compute_embedding(Path(p), dim=sim_dim)
                db.upsert_embedding(p, vec, sim_dim, int(mtime))
                updated += 1
            except Exception as e:  # pylint: disable=broad-except
                # non-fatal
                print(f"[scan][WARN] embedding failed for {p}: {e}", file=sys.stderr)

        logger.log("INFO", "embeddings_precomputed", updated=updated)
    except Exception as e:  # pylint: disable=broad-except
        print(f"[scan][WARN] Failed to precompute embeddings: {e}", file=sys.stderr)

    # Metrics
    bytes_scanned = sum(r[1] for r in records)
    metrics.data["files_scanned"] = total
    metrics.data["bytes_scanned"] = bytes_scanned
    metrics.data["durations"]["scan_s"] = round(dur, 3)

    # Meta Export
    if cfg.get("export_folder_meta", False):
        by_dir = defaultdict(list)
        for rec in records:
            path_obj = Path(rec[0])
            by_dir[path_obj.parent].append({
                "name": path_obj.name,
                "size": rec[1],
                "mtime": rec[2],
                "file_hash": rec[3],
                "mime": rec[4],
                "context_tag": rec[5],
                "hash_algo": rec[6],
                "permissions": rec[7]
            })

        meta_count = 0
        meta_errors = 0
        for dir_path, file_recs in by_dir.items():
            try:
                write_folder_meta(
                    folder_path=dir_path,
                    file_records=file_recs,
                    root_path=Path(args.root[0]),
                    pretty=cfg.get("meta_pretty", False),
                    silent=True
                )
                meta_count += 1
            except Exception as e:  # pylint: disable=broad-except
                meta_errors += 1
                logger.log("ERROR", "meta_export_failed", directory=str(dir_path), error=str(e))
        
        metrics.data["meta_exported"] = meta_count
        metrics.data["meta_errors"] = meta_errors

    metrics.save()
    print(f"[scan] files={total} bytes={bytes_scanned} dur_s={round(dur,3)} -> {cfg['db_path']}")
    return 0

def cmd_plan(args, cfg):
    """Plan command."""
    db = DB(Path(cfg["db_path"]))
    dups = db.get_duplicates()
    ts = datetime.utcnow().isoformat() + "Z"
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
    print(f"[plan] duplicate_groups={len(dups)} planned_ops={len(rows)} -> {args.out}")
    return 0

def cmd_apply(args, cfg):
    """Apply command."""
    res = apply_moves(
        # Read CSV manually or use helper if we had one for reading
        # For now, simple read
        [], # pylint: disable=fixme
        Path(args.checkpoint),
        dry_run=(cfg["dry_run"] and not args.force)
    )
    # Re-implement CSV reading here since applier expects list of dicts
    rows = []
    with Path(args.plan).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            
    res = apply_moves(rows, Path(args.checkpoint), dry_run=(cfg["dry_run"] and not args.force))
    print(f"[apply] {res}")
    return 0 if res["errors"] == 0 else 1

def cmd_rollback(args, _cfg):
    res = rollback_from_checkpoint(Path(args.checkpoint))
    print(f"[rollback] {res}")
    return 0 if res["errors"] == 0 else 1

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

def cmd_mount(args, cfg):
    """Mount command."""
    mount_fs(Path(cfg["db_path"]), Path(args.mountpoint))
    return 0

def cmd_archive_list(args, _cfg):
    try:
        h = ArchiveHandler(args.file)
        print(f"Archive Type: {h.type}")
        for item in h.list_contents():
            print(f"{item['size']:>12} {item['path']}")
        return 0
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

def cmd_archive_extract(args, _cfg):
    try:
        h = ArchiveHandler(args.file)
        h.extract(args.dest)
        print("Extraction complete.")
        return 0
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

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
    from .similarity.cli import update_index_from_db as _update
    db_path = Path(cfg['db_path'])
    if not args.index_file:
        print("[similarity][update] --index-file is required", file=sys.stderr)
        return 2
    res = _update(db_path, args.index_file, remove_missing=args.rebuild)
    print(f"[similarity][update] added={res.get('added')} index_count={res.get('index_count')}")
    return 0


def main(argv=None):
    # Initialize dependency auto-installer
    init_deps(auto_install=True, silent=False)

    # Startup linting
    module_dir = Path(__file__).parent
    try:
        lint_tree(module_dir)
    except SyntaxError as e:
        print(f"[fatal] Startup linting failed: {e}", file=sys.stderr)
        return 10

    # Register shutdown linting
    def shutdown_lint():
        try:
            lint_tree(module_dir)
        except Exception as e:  # pylint: disable=broad-except
            print(f"[warn] Shutdown linting failed: {e}", file=sys.stderr)

    atexit.register(shutdown_lint)

    # Load configuration
    cfg = load_config()

    parser = argparse.ArgumentParser(prog="nodupe")
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Scan
    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--root", action="append", required=True)
    p_scan.set_defaults(_run=cmd_scan)

    # Plan
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--out", required=True)
    p_plan.set_defaults(_run=cmd_plan)

    # Apply
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--plan", required=True)
    p_apply.add_argument("--checkpoint", required=True)
    p_apply.add_argument("--force", action="store_true")
    p_apply.set_defaults(_run=cmd_apply)

    # Rollback
    p_rb = sub.add_parser("rollback")
    p_rb.add_argument("--checkpoint", required=True)
    p_rb.set_defaults(_run=cmd_rollback)

    # Verify
    p_vf = sub.add_parser("verify")
    p_vf.add_argument("--checkpoint", required=True)
    p_vf.set_defaults(_run=cmd_verify)

    # Mount
    p_mnt = sub.add_parser("mount")
    p_mnt.add_argument("mountpoint", help="Directory to mount the filesystem")
    p_mnt.set_defaults(_run=cmd_mount)

    # Archive
    p_arch = sub.add_parser("archive")
    p_arch_sub = p_arch.add_subparsers(dest="archive_cmd", required=True)
    
    p_l = p_arch_sub.add_parser("list")
    p_l.add_argument("file")
    p_l.set_defaults(_run=cmd_archive_list)
    
    p_e = p_arch_sub.add_parser("extract")
    p_e.add_argument("file")
    p_e.add_argument("--dest", required=True)
    p_e.set_defaults(_run=cmd_archive_extract)

    # Similarity
    p_sim = sub.add_parser("similarity")
    p_sim_sub = p_sim.add_subparsers(dest="sim_cmd", required=True)

    p_sim_build = p_sim_sub.add_parser("build")
    p_sim_build.add_argument("--dim", type=int, default=16)
    p_sim_build.add_argument("--out", help="Optional output index file (.index or .npz)")
    p_sim_build.set_defaults(_run=cmd_similarity_build)

    p_sim_query = p_sim_sub.add_parser("query")
    p_sim_query.add_argument("file")
    p_sim_query.add_argument("--dim", type=int, default=16)
    p_sim_query.add_argument("-k", type=int, default=5)
    p_sim_query.add_argument("--index-file", help="Optional index file to load for faster queries")
    p_sim_query.set_defaults(_run=cmd_similarity_query)

    p_sim_update = p_sim_sub.add_parser("update")
    p_sim_update.add_argument("--index-file", required=True, help="Index file to update (.index/.npz)")
    p_sim_update.add_argument("--rebuild", action="store_true", help="Rebuild index from DB (remove missing / stale entries)")
    p_sim_update.set_defaults(_run=cmd_similarity_update)

    args = parser.parse_args(argv)
    
    try:
        rc = args._run(args, cfg)  # pylint: disable=protected-access
    except KeyboardInterrupt:
        print("\n[fatal] Interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:  # pylint: disable=broad-except
        print(f"[fatal] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 10

    return rc

if __name__ == "__main__":
    sys.exit(main())
