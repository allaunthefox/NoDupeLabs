# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Metadata manifest generation for scanned directories.

This module generates `nodupe_meta_v1` compliant meta.json files for
each scanned directory. These manifests provide self-describing metadata
that remains readable even without the original software.

Key Features:
    - nodupe_meta_v1 schema compliance
    - Idempotent writes (skip if metadata unchanged)
    - Read-only filesystem detection
    - Disk full protection with atomic writes
    - Automatic categorization and keyword extraction
    - Topic inference from filenames

Manifest Contents:
    - spec: Schema version (nodupe_meta_v1)
    - generated_at: ISO 8601 timestamp
    - summary: Aggregate statistics (file count, bytes, categories, topics)
    - entries: Per-file metadata (name, size, hash, MIME, category)

Safety Features:
    - Read-only directory/file detection
    - Atomic write via temp file + replace
    - Disk full error handling (ENOSPC)
    - Validation before write
    - Idempotent updates (preserves mtime when no changes)

Dependencies:
    - json: Manifest serialization
    - collections.Counter: Category aggregation
    - datetime: Timestamp generation
    - categorizer: File classification
    - validator: Schema validation

Example:
    >>> from pathlib import Path
    >>> records = [
    ...     {'name': 'photo.jpg', 'size': 1024, 'mtime': 1234567890,
    ...      'file_hash': 'abc123', 'mime': 'image/jpeg'}
    ... ]
    >>> write_folder_meta(Path('/data'), records, Path('/data'))
    # Creates /data/meta.json if changed
"""

import os
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from .categorizer import categorize_file
from .validator import validate_meta_dict
from .io import FileWriter


def _iso_now():
    """Generate ISO 8601 timestamp with UTC timezone.

    Returns current UTC time formatted as ISO 8601 with 'Z' suffix
    (e.g., '2025-12-03T14:30:00Z'). Microseconds are truncated for
    consistency.

    Returns:
        ISO 8601 timestamp string with Z suffix

    Example:
        >>> timestamp = _iso_now()
        >>> print(timestamp)
        '2025-12-03T14:30:00Z'
    """
    return datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")


def write_folder_meta(
    folder_path: Path, file_records: List[Dict[str, Any]],
    root_path: Path, pretty: bool = False, silent: bool = True,
    writer: Optional[FileWriter] = None
):
    """Write nodupe_meta_v1 manifest to folder.

    Generates a self-describing meta.json file containing file hashes,
    categories, topics, and keywords. Implements idempotent writes
    (skips update if content unchanged) and atomic write-replace
    pattern for safety.

    Args:
        folder_path: Directory where meta.json will be written
        file_records: List of file metadata dicts with keys:
            - name: Filename
            - size: File size in bytes
            - mtime: Modification timestamp (Unix epoch)
            - file_hash: Content hash (sha512 by default)
            - hash_algo: Hash algorithm used (optional, default: sha512)
            - mime: MIME type
            - context_tag: Optional context tag
            - permissions: Optional permissions string
        root_path: Root scan directory for relative path calculation
        pretty: If True, format JSON with indentation (default: False)
        silent: If True, suppress validation error messages
            (default: True)

    Returns:
        None

    Raises:
        PermissionError: If directory or existing meta.json is read-only
        OSError: If disk full (ENOSPC) during write

    Side Effects:
        - Creates meta.json in folder_path
        - Creates meta.invalid.json if validation fails
        - Skips write if content unchanged (idempotent)

    Example:
        >>> from pathlib import Path
        >>> records = [
        ...     {'name': 'photo.jpg', 'size': 1024, 'mtime': 1234567890,
        ...      'file_hash': 'abc123', 'mime': 'image/jpeg'}
        ... ]
        >>> write_folder_meta(Path('/data'), records, Path('/data'))
        # Creates /data/meta.json if changed
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
        categorize_file(r["mime"], r["name"]).category
        for r in filtered_records
    ])
    topics: List[str] = []
    keywords: Set[str] = set()

    for r in filtered_records:
        c = categorize_file(r["mime"], r["name"])
        topic = c.topic
        if topic:
            topics.append(topic)

        # Keywords from filename
        stem = Path(r["name"]).stem.replace("_", " ").replace("-", " ")
        for tok in stem.split():
            if tok and tok.isascii() and tok[0].isalpha() and len(tok) >= 3:
                keywords.add(tok[:32])

    topics_list = list(sorted({t for t in topics if t}))[:8]
    keywords_list = list(sorted(keywords))[:16]

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
            "topics": topics_list,
            "keywords": keywords_list
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
            "category": c.category,
            "subtype": c.subtype,
            "topic": c.topic
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
