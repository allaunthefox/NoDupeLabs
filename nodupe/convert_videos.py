# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Video conversion compatibility shim.

This module provides a compatibility layer for video conversion, allowing
imports from `nodupe.convert_videos` to work regardless of whether the
code is running from source or as an installed package. It re-exports
functionality from the top-level script or provides a fallback implementation.

Functions:
    - convert_video: Convert video format using FFmpeg

Dependencies:
    - nodupe.utils.ffmpeg_progress: FFmpeg execution
"""
from importlib import import_module
from typing import Any

try:
    # prefer the top-level script if present
    _cv = import_module("convert_videos")
except Exception:  # pragma: no cover - best-effort shim
    _cv = None


def convert_video(input_path: Any, output_path: Any) -> None:
    # Prefer the library helper so tests can patch the ffmpeg helper;
    # if a top-level script is present we'll still use the shared helper
    # implementation below instead of delegating to the script's binding
    # (which may have captured its own helper at import time).

    # Fallback minimal implementation if the top-level script isn't importable.
    # This keeps tests robust but real code should prefer the main script.
    from nodupe.utils.ffmpeg_progress import run_ffmpeg_with_progress

    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(input_path), str(output_path)
    ]
    ok = run_ffmpeg_with_progress(cmd, expected_duration=None)
    if not ok:
        print(f"Error converting {input_path}: ffmpeg failed or not present")
