import os
import sys
import tempfile
import shutil
from pathlib import Path
# import pytest
from nodupe.scanner import iter_files, process_file, threaded_hash
from nodupe.utils.filesystem import should_skip as _should_skip
from nodupe.utils.media import extract_representative_frame
from nodupe.ai.backends.cpu import CPUBackend
from tests.test_helpers import run_ffmpeg_with_progress
import subprocess


# use run_ffmpeg_with_progress from tests.test_helpers

def create_dummy_file(path: Path, content: bytes = b"test"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

def test_should_skip():
    assert _should_skip(Path("a/b/node_modules/c"), ["node_modules"])
    assert _should_skip(Path("a/b/.git/c"), [".git"])
    assert not _should_skip(Path("a/b/src/c"), ["node_modules"])

def test_iter_files_basic():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        create_dummy_file(root / "f1.txt")
        create_dummy_file(root / "sub/f2.txt")
        create_dummy_file(root / "ignore/f3.txt")
        
        files = list(iter_files([str(root)], ignore=["ignore"]))
        names = {f.name for f in files}
        
        assert "f1.txt" in names
        assert "f2.txt" in names
        assert "f3.txt" not in names

def test_iter_files_symlinks():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        real_dir = root / "real"
        real_dir.mkdir()
        create_dummy_file(real_dir / "real.txt")
        
        link_dir = root / "link"
        try:
            os.symlink(real_dir, link_dir)
        except OSError:
            print("Symlinks not supported")
            return
            
        # Default: follow_symlinks=False
        files = list(iter_files([str(root)], ignore=[], follow_symlinks=False))
        names = {f.name for f in files}
        assert "real.txt" in names
        # Should find it once (in real_dir)
        assert len(files) == 1
        
        # follow_symlinks=True
        files = list(iter_files([str(root)], ignore=[], follow_symlinks=True))
        # Should find it twice (real and link)
        assert len(files) == 2

def test_process_file():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test.txt"
        p.write_bytes(b"hello")
        
        # sha512 of "hello"
        # cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e
        
        res = process_file(p, "sha512")
        # (path, size, mtime, hash, mime, context, algo, perms)
        assert res[0] == str(p)
        assert res[1] == 5
        assert res[3] == "9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72323c3d99ba5c11d7c7acc6e14b8c5da0c4663475c2e5c3adef46f73bcdec043"
        assert res[6] == "sha512"

def test_threaded_hash():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        create_dummy_file(root / "a.txt", b"a")
        create_dummy_file(root / "b.txt", b"b")
        
        results, dur, total = threaded_hash([str(root)], ignore=[], workers=2)
        
        assert len(results) == 2
        assert total == 2
        assert dur >= 0


import pytest


@pytest.mark.slow
def test_extract_representative_frame():
    # requires ffmpeg on PATH for this integration test
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        img = td / "in.png"
        # create a tiny PNG
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 128)

        # Build a 1 second video from the image using ffmpeg and show progress
        video = td / "out.mp4"
        # Use -progress pipe:1 so we can parse lightweight progress output
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(img), "-c:v", "libx264",
            "-t", "1", "-pix_fmt", "yuv420p", "-progress", "pipe:1", "-nostats", str(video)
        ]

        # Use the module-level run_ffmpeg_with_progress helper so tests share identical UI

        ok = run_ffmpeg_with_progress(cmd, expected_duration=1.0, max_wait=12)
        if not ok:
            # ffmpeg might not be available in CI — gracefully skip the rest of the test
            return

        frame = extract_representative_frame(video)
        assert frame is not None and frame.exists()
        # meta sidecar should exist and be valid JSON
        meta = frame.with_suffix(frame.suffix + '.json')
        assert meta.exists()
        import json
        data = json.loads(meta.read_text(encoding='utf-8'))
        assert data.get('source') and data.get('extracted_at')


@pytest.mark.slow
def test_video_embedding_cpu_backend():
    # Ensure CPUBackend can compute embeddings for a video by using extracted frame
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        img = td / "in.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 512)
        video = td / "out.webm"
        # Build a 1 second VP9 webm for embedding tests using our progress UI.
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-c:v", "libvpx-vp9", "-t", "1", str(video)]
        ok = run_ffmpeg_with_progress(cmd, expected_duration=1.0, max_wait=12)
        if not ok:
            # ffmpeg might not be available or failed — skip test
            return

        be = CPUBackend()
        vec = be.compute_embedding(video, dim=16)
        assert isinstance(vec, list)
        assert len(vec) == 16


def _make_fake_proc(steps=3, rc=0, sleep=0.0):
    """Return a fake Popen-like object for tests.

    - steps: number of poll() calls that return None before returning rc
    - rc: final returncode
    """
    class FakeProc:
        def __init__(self):
            self._calls = 0
            self.returncode = None

        def poll(self):
            # On each call, increment; return None until we've seen `steps` calls.
            if self._calls < steps:
                self._calls += 1
                return None
            self.returncode = rc
            return rc

        def communicate(self, timeout=None):
            return ('', '')

        def kill(self):
            self.returncode = 1

    return FakeProc()


def test_run_ffmpeg_probe_and_interactive_behavior(tmp_path, monkeypatch, capsys):
    # Create a fake media file and ensure ffprobe is called to probe duration
    f = tmp_path / 'dummy.mp4'
    f.write_text('dummy')

    # Patch subprocess.run to simulate ffprobe returning a duration
    calls = {}

    def fake_run(cmd, capture_output=False, text=False, check=False):
        # Ensure ffprobe call is used
        calls['cmd'] = cmd
        class Result:
            stdout = '2.5\n'
        return Result()

    monkeypatch.setattr(subprocess, 'run', fake_run)

    # Patch Popen so the command appears to run and finish
    fake = _make_fake_proc(steps=2, rc=0)
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: fake)

    # Force interactive mode so we exercise the live updates path
    ok = run_ffmpeg_with_progress(['ffmpeg', '-i', str(f)], expected_duration=None, force_mode='interactive', probe_input_duration=True)
    assert ok is True
    # Confirm ffprobe was invoked
    assert 'ffprobe' in ' '.join(calls['cmd'])


def test_run_ffmpeg_env_quiet_and_noninteractive(monkeypatch, tmp_path, capsys):
    # Create dummy file
    f = tmp_path / 'dummy2.mp4'
    f.write_text('x')

    # Simulate ffprobe failure (no problem — it will fall back)
    def fake_run(cmd, capture_output=False, text=False, check=False):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, 'run', fake_run)

    # Simulate a process
    fake = _make_fake_proc(steps=1, rc=0)
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: fake)

    # Force quiet via environment
    monkeypatch.setenv('NO_DUPE_PROGRESS', 'quiet')

    ok = run_ffmpeg_with_progress(['ffmpeg', '-i', str(f)], expected_duration=None, probe_input_duration=True)
    assert ok is True
    captured = capsys.readouterr()
    # Should have a single final progress line and not many updates
    assert captured.out.count('[TEST PROGRESS]') <= 2


def test_run_ffmpeg_failure_returns_false(monkeypatch):
    # Simulate ffmpeg missing by having Popen raise FileNotFoundError
    def fake_popen(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, 'Popen', fake_popen)
    ok = run_ffmpeg_with_progress(['ffmpeg', '-i', 'no-file'], expected_duration=0.1)
    assert ok is False


def test_extract_representative_frame_mock_failure(monkeypatch, tmp_path):
    from nodupe.utils import media as media_mod

    video = tmp_path / 'in.mp4'
    video.write_text('x')

    # Simulate ffmpeg missing/failure
    monkeypatch.setattr(media_mod, 'run_ffmpeg_with_progress', lambda *a, **k: False)

    res = media_mod.extract_representative_frame(video, force=True)
    assert res is None


def test_extract_representative_frame_mock_success(monkeypatch, tmp_path):
    from nodupe.utils import media as media_mod

    video = tmp_path / 'in.mp4'
    video.write_text('x')

    # compute expected out file path
    out_dir = media_mod.Path(media_mod.tempfile.gettempdir()) / 'nodupe_video_frames'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{media_mod._hash_path(video)}_{video.stem}.jpg"

    def fake_run(cmd, expected_duration=None, **kwargs):
        out_file.write_bytes(b'jpegdata')
        return True

    monkeypatch.setattr(media_mod, 'run_ffmpeg_with_progress', fake_run)

    res = media_mod.extract_representative_frame(video, force=True)
    assert res == out_file
