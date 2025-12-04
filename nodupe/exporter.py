# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import os
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Set
from .categorizer import categorize_file
from .validator import validate_meta_dict


def _iso_now():
    return datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")


def write_folder_meta(
    folder_path: Path, file_records: List[Dict[str, Any]],
    root_path: Path, pretty: bool = False, silent: bool = True
):
    """
    Write nodupe_meta_v1 meta.json for a folder.
    Includes read-only checks, disk full checks, and skip-if-identical logic.
    """
    # Check directory permissions
    if not os.access(folder_path, os.W_OK):
        raise PermissionError(f"Directory is read-only: {folder_path}")

    meta_path = folder_path / "meta.json"
    if meta_path.exists() and not os.access(meta_path, os.W_OK):
        raise PermissionError(f"Existing meta.json is read-only: {meta_path}")

    # Filter out meta files to avoid self-reference
    filtered_records = [
        r for r in file_records
        if r["name"] not in ("meta.json", "meta.json.tmp", "meta.invalid.json")
    ]

    cats = Counter([
        categorize_file(r["mime"], r["name"])["category"]
        for r in filtered_records
    ])
    topics: List[str] = []
    keywords: Set[str] = set()

    for r in filtered_records:
        c = categorize_file(r["mime"], r["name"])
        if c.get("topic"):
            topics.append(c["topic"])

        # Keywords from filename
        stem = Path(r["name"]).stem.replace("_", " ").replace("-", " ")
        for tok in stem.split():
            if tok and tok.isascii() and tok[0].isalpha() and len(tok) >= 3:
                keywords.add(tok[:32])

    topics = sorted({t for t in topics if t})[:8]
    keywords = sorted(list(keywords))[:16]

    meta = {
        "spec": "nodupe_meta_v1",
        "generated_at": _iso_now(),
        "folder_rel": str(folder_path.relative_to(root_path))
        if folder_path != root_path else ".",
        "parent_rel": (
            str(folder_path.parent.relative_to(root_path))
            if folder_path != root_path else None
        ),
        "summary": {
            "files_total": len(filtered_records),
            "bytes_total": sum(int(r["size"]) for r in filtered_records),
            "categories": dict(cats),
            "topics": topics,
            "keywords": keywords
        },
        "entries": []
    }

    for r in filtered_records:
        c = categorize_file(r["mime"], r["name"])
        entry = {
            "name": r["name"],
            "size": int(r["size"]),
            "mtime": int(r["mtime"]),
            "file_hash": r["file_hash"],
            "hash_algo": r.get("hash_algo", "sha512"),
            "mime": r["mime"],
            "category": c["category"],
            "subtype": c["subtype"],
            "topic": c["topic"]
        }
        if "context_tag" in r:
            entry["context_tag"] = r["context_tag"]
        if "permissions" in r:
            entry["permissions"] = r["permissions"]

        meta["entries"].append(entry)

    # Deterministic sort
    meta["entries"].sort(key=lambda x: x["name"])

    ok, err = validate_meta_dict(meta)

    if ok:
        # Check if update is needed
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

                if existing.get("spec") == meta["spec"]:
                    existing_clean = existing.copy()
                    existing_clean.pop("generated_at", None)
                    meta_clean = meta.copy()
                    meta_clean.pop("generated_at", None)

                    if "entries" in existing_clean:
                        existing_clean["entries"].sort(key=lambda x: x["name"])

                    if existing_clean == meta_clean:
                        return  # Skip update
            except (json.JSONDecodeError, OSError, KeyError):
                pass

        tmp = meta_path.with_suffix(".json.tmp")
        try:
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                if pretty:
                    json.dump(
                        meta, f, ensure_ascii=False, sort_keys=True, indent=2
                    )
                else:
                    json.dump(
                        meta, f, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":")
                    )
                f.write("\n")
            tmp.replace(meta_path)
        except OSError as e:
            if e.errno == 28:  # ENOSPC
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except OSError:
                        pass
                raise OSError(f"Disk full while writing {meta_path}") from e
            raise
    else:
        bad = meta_path.with_suffix(".invalid.json")
        with open(bad, "w", encoding="utf-8", newline="\n") as f:
            json.dump(
                meta, f, ensure_ascii=False, sort_keys=True,
                separators=(",", ":")
            )
            f.write("\n")
        if not silent:
            print(f"[meta][INVALID] {folder_path}: {err}")
