# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File categorization by MIME type and extension.

This module classifies files into high-level categories (image, video,
text, archive, other) with subtypes and optional topic inference. Used
for aggregating file statistics and generating metadata manifests.

Category Taxonomy:
    - image: Photo files (MIME: image/*)
    - video: Video files (MIME: video/*)
    - text: Text files (.txt extension)
    - archive: Compressed archives (zip, tar, 7z, rar, etc.)
    - other: All other files (default fallback)

Subtypes:
    - photo: Image files
    - clip: Video files
    - textfile: Text files
    - compressed: Archive files
    - unknown: Other files

Topic Inference:
    Currently returns None for all files. Reserved for future
    content-based topic detection.

Key Features:
    - MIME type to category mapping
    - Extension-based fallback for archives
    - Consistent dict return format
    - Case-insensitive matching

Dependencies:
    - typing: Type hints only

Example:
    >>> categorize_file('image/jpeg', 'photo.jpg')
    {'category': 'image', 'subtype': 'photo', 'topic': None}
    >>> categorize_file('application/zip', 'archive.zip')
    {'category': 'archive', 'subtype': 'compressed', 'topic': None}
"""

from typing import Dict


def categorize_file(mime: str, name: str) -> Dict[str, str]:
    """Classify file by MIME type and extension.

    Categorizes files into high-level categories (image, video, text,
    archive, other) with corresponding subtypes. Uses MIME type as
    primary signal, with filename extension fallback for archives.

    Args:
        mime: MIME type string (e.g., 'image/jpeg', 'application/zip')
        name: Filename (e.g., 'photo.jpg', 'archive.zip')

    Returns:
        Dict with classification keys:
            - category: High-level category (str)
            - subtype: Specific subtype (str)
            - topic: Optional topic inference (str or None)

    Example:
        >>> categorize_file('image/png', 'screenshot.png')
        {'category': 'image', 'subtype': 'photo', 'topic': None}
        >>> categorize_file('video/mp4', 'movie.mp4')
        {'category': 'video', 'subtype': 'clip', 'topic': None}
        >>> categorize_file('application/zip', 'data.zip')
        {'category': 'archive', 'subtype': 'compressed', 'topic': None}
        >>> categorize_file('application/octet-stream', 'unknown.bin')
        {'category': 'other', 'subtype': 'unknown', 'topic': None}
    """
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
