import subprocess
import tempfile
from pathlib import Path
import os

import pytest
from nodupe.convert_videos import convert_video
from tests.test_helpers import run_ffmpeg_with_progress

# Note: extract_video_conversions isn't present; we'll test convert_videos main operations directly by creating a short sample.

@pytest.mark.slow
def test_convert_videos_basic():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        img = td / "in.png"
        # create a tiny PNG
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 512)
        video = td / "in.mp4"
        # create a 1 second mp4 from image
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-c:v", "libx264", "-t", "1", "-pix_fmt", "yuv420p", str(video)]
        ok = run_ffmpeg_with_progress(cmd, expected_duration=None)
        if not ok:
            # ffmpeg not available in this environment — skip
            return

        outputs = [td / "out.mp4", td / "out.webm", td / "out.mkv", td / "out.avi"]
        # convert
        for out in outputs:
            convert_video(video, out)
            assert out.exists() and out.stat().st_size > 0


def test_convert_video_mock_success(tmp_path, monkeypatch):
    # simulate a successful ffmpeg run by creating the destination file
    inp = tmp_path / 'in.mp4'
    inp.write_text('x')
    out = tmp_path / 'converted.webm'

    def fake_run(cmd, expected_duration=None, **kwargs):
        out.write_bytes(b'converted')
        return True

    import nodupe.utils.ffmpeg_progress as ff
    monkeypatch.setattr(ff, 'run_ffmpeg_with_progress', fake_run)

    import nodupe.convert_videos as cv
    cv.convert_video(inp, out)
    assert out.exists() and out.read_bytes() == b'converted'


def test_convert_video_mock_failure(tmp_path, monkeypatch, capsys):
    inp = tmp_path / 'in.mp4'
    inp.write_text('x')
    out = tmp_path / 'converted.webm'

    import nodupe.utils.ffmpeg_progress as ff
    monkeypatch.setattr(ff, 'run_ffmpeg_with_progress', lambda *a, **k: False)

    import nodupe.convert_videos as cv
    cv.convert_video(inp, out)
    captured = capsys.readouterr()
    assert 'Error converting' in captured.out
