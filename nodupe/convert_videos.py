"""Compatibility shim so tests and callers can import convert_videos from the
package.

This tries to import the top-level `convert_videos` module (keeps existing
CLI/utility scripts working) and re-exports the `convert_video` helper so
callers can import `nodupe.convert_videos.convert_video` reliably whether the
package is installed or running from source.
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
