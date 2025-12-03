# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import mimetypes
import stat
from pathlib import Path
from typing import List

ARCHIVE_EXTENSIONS = {
    ".zip", ".7z", ".tar", ".gz", ".bz2", ".xz", ".rar",
    ".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tbz2",
}

# Manual overrides for modern/common types that mimetypes might miss
MIME_OVERRIDES = {
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".avif": "image/avif",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".ts": "video/mp2t",
    ".m2ts": "video/mp2t",
    ".json": "application/json",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
    ".md": "text/markdown",
    ".log": "text/plain",
}


def should_skip(p: Path, ignore: List[str]) -> bool:
    parts = set(p.parts)
    return any(ig in parts for ig in ignore)


def detect_context(path: Path) -> str:
    """Detect if file is archived or unarchived."""
    # Expanded context detection
    indicators = {
        "extracted", "unzipped", "unpacked", "expanded",
        "backup", "archive", "old", "temp", "tmp"
    }
    for parent in path.parents:
        if parent.name.lower() in indicators:
            return "archived"
    return "unarchived"


def get_mime_safe(p: Path) -> str:
    # Check overrides first
    suffix = p.suffix.lower()
    if suffix in MIME_OVERRIDES:
        return MIME_OVERRIDES[suffix]

    mime, _ = mimetypes.guess_type(str(p))
    if mime:
        return mime
    return "application/octet-stream"


def get_permissions(p: Path) -> str:
    try:
        # Return octal representation of mode, e.g. "0o755"
        return oct(stat.S_IMODE(p.stat().st_mode))
    except OSError:
        return "0"
