import sys
from pathlib import Path

from nodupe.utils.ffmpeg_progress import run_ffmpeg_with_progress


def test_run_ffmpeg_timeout_kills():
    # Run a short python sleep that exceeds the timeout so the helper will kill it
    cmd = [sys.executable, '-c', 'import time; time.sleep(3)']
    # expected_duration is larger than timeout -> we should hit timeout and return False
    ok = run_ffmpeg_with_progress(cmd, expected_duration=5.0, timeout=0.5, force_mode='quiet', probe_input_duration=False)
    assert ok is False


def test_run_ffmpeg_eta_and_success():
    # Short sleep that will finish quickly; ETA should be harmless and function should return True
    cmd = [sys.executable, '-c', 'import time; time.sleep(0.2)']
    ok = run_ffmpeg_with_progress(cmd, expected_duration=1.0, timeout=2.0, force_mode='quiet', probe_input_duration=False, show_eta=True)
    assert ok is True
