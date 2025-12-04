# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Media processing utilities for video frame extraction.

This module provides utilities for extracting representative frames
from video files using FFmpeg. Extracted frames are cached in a
temporary directory and reused across runs.

Key Features:
    - Video frame extraction at 0.5s offset
    - Persistent frame cache based on video path hash
    - FFmpeg progress reporting integration
    - Metadata sidecar generation (JSON)
    - Graceful degradation when FFmpeg unavailable

Frame Extraction Strategy:
    - Extract single frame at 0.5s offset (avoids black first frames)
    - Cache frames in system temp directory (nodupe_video_frames/)
    - Filename based on video path hash + original stem
    - Quality setting: -q:v 2 (high JPEG quality)
    - Reuse cached frames unless force=True

Supported Formats:
    - All video formats supported by FFmpeg
    - Common: MP4, MKV, AVI, MOV, WebM, FLV, etc.

Dependencies:
    - ffmpeg: External binary (must be on PATH)
    - ffmpeg_progress: Progress reporting helper
    - tempfile: Temporary directory management
    - hashlib: Path hashing for cache keys

Example:
    >>> from pathlib import Path
    >>> frame = extract_representative_frame(Path('/data/video.mp4'))
    >>> if frame:
    ...     print(f"Frame extracted to: {frame}")
    Frame extracted to: /tmp/nodupe_video_frames/abc123_video.jpg
"""

from __future__ import annotations
from pathlib import Path
import subprocess
from .ffmpeg_progress import run_ffmpeg_with_progress
import tempfile
import hashlib
from typing import Optional


def _hash_path(p: Path) -> str:
    """Generate short hash of path for cache filename.

    Args:
        p: Path to hash

    Returns:
        First 16 characters of SHA-256 hash of resolved path

    Example:
        >>> from pathlib import Path
        >>> _hash_path(Path('/data/video.mp4'))
        'a1b2c3d4e5f67890'
    """
    h = hashlib.sha256()
    h.update(str(p.resolve()).encode('utf-8'))
    return h.hexdigest()[:16]


def extract_representative_frame(
    video_path: Path, force: bool = False
) -> Optional[Path]:
    """Extract representative frame from video using FFmpeg.

    Extracts a single high-quality JPEG frame at 0.5s offset from the
    video. Frames are cached in system temp directory and reused across
    runs unless force=True.

    Args:
        video_path: Path to video file
        force: If True, re-extract even if cached frame exists
            (default: False)

    Returns:
        Path to extracted JPEG frame, or None if extraction failed

    Cache Location:
        Frames stored in: {system_temp}/nodupe_video_frames/
        Filename format: {path_hash}_{video_stem}.jpg
        Also creates .jpg.json metadata sidecar with extraction details

    FFmpeg Command:
        - Seek to 0.5s offset (-ss 0.5) to avoid black first frames
        - Extract single frame (-frames:v 1)
        - High JPEG quality (-q:v 2)
        - Suppress warnings (-v error)

    Raises:
        No exceptions raised. Returns None on failure.

    Failure Conditions:
        - video_path doesn't exist
        - ffmpeg not found on PATH
        - ffmpeg fails (corrupted video, unsupported format, etc.)

    Example:
        >>> from pathlib import Path
        >>> frame = extract_representative_frame(Path('/data/clip.mp4'))
        >>> if frame:
        ...     print(f"Frame: {frame}")
        ...     # Frame persists in temp, reused on next call
        ...     frame2 = extract_representative_frame(Path('/data/clip.mp4'))
        ...     assert frame == frame2
        Frame: /tmp/nodupe_video_frames/abc123def456_clip.jpg
    """
    if not video_path.exists():
        return None

    out_dir = Path(tempfile.gettempdir()) / "nodupe_video_frames"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"{_hash_path(video_path)}_{video_path.stem}.jpg"
    if out_file.exists() and not force:
        return out_file

    # Build ffmpeg command: seek to 0.5s, extract one frame
    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-ss",
        "0.5",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(out_file),
    ]

    try:
        ok = run_ffmpeg_with_progress(cmd, expected_duration=1.0)
        if not ok:
            return None
        if out_file.exists():
            # Write a small metadata sidecar in JSON so the output is
            # inspectable
            meta_file = out_file.with_suffix(out_file.suffix + '.json')
            try:
                import json
                info = {
                    'source': str(video_path.resolve()),
                    'extracted_at': __import__('datetime').datetime.now(
                        __import__('datetime').timezone.utc
                    ).isoformat(),
                    'frame_offset_s': 0.5,
                    'format': 'jpeg',
                }
                with open(meta_file, 'w', encoding='utf-8') as fh:
                    json.dump(info, fh, ensure_ascii=False, indent=2)
            except Exception:
                # best-effort only
                pass

            return out_file
        else:
            return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        # ffmpeg missing or failed
        return None
