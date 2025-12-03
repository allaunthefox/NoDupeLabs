# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from typing import Dict


def categorize_file(mime: str, name: str) -> Dict[str, str]:
    mime = (mime or "").lower()
    name = (name or "").lower()

    if mime.startswith("image"):
        return {"category": "image", "subtype": "photo", "topic": None}
    if mime.startswith("video"):
        return {"category": "video", "subtype": "clip", "topic": None}
    if name.endswith(".txt"):
        return {"category": "text", "subtype": "textfile", "topic": None}

    # Archive detection
    if mime in (
        "application/zip",
        "application/x-7z-compressed",
        "application/vnd.rar",
        "application/x-tar",
        "application/gzip",
        "application/x-bzip2",
        "application/x-xz",
        "application/zstd",
    ) or name.endswith((
        ".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz", ".zst"
    )):
        return {"category": "archive", "subtype": "compressed", "topic": None}

    return {"category": "other", "subtype": "unknown", "topic": None}
