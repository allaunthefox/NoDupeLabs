# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from __future__ import annotations
from pathlib import Path
import subprocess
from .ffmpeg_progress import run_ffmpeg_with_progress
import tempfile
import hashlib
from typing import Optional


def _hash_path(p: Path) -> str:
    h = hashlib.sha256()
    h.update(str(p.resolve()).encode('utf-8'))
    return h.hexdigest()[:16]


def extract_representative_frame(
    video_path: Path, force: bool = False
) -> Optional[Path]:
    """Extract a single representative frame from a video file using ffmpeg.

    Returns a Path to a temporary JPEG file (persistent across runs if same
    video path), or None on failure.

    The function uses a temp directory and stable filename based on the video
    path so repeated calls reuse the same frame file.

    Note: this requires `ffmpeg` to be available on PATH. We extract at 0.5s
    (-ss 0.5) which works for short clips and avoids the first frame issues.
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
