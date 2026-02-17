import argparse
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from nodupe.tools.commands.scan import ScanTool


def test_execute_scan_no_paths_returns_error():
    tool = ScanTool()
    args = SimpleNamespace(paths=[], container=None, min_size=0, max_size=None, extensions=None, verbose=False)
    assert tool.execute_scan(args) == 1


def test_execute_scan_missing_path_returns_error(tmp_path):
    tool = ScanTool()
    missing = tmp_path / "does_not_exist"
    args = SimpleNamespace(paths=[str(missing)], container=None, min_size=0, max_size=None, extensions=None, verbose=False)
    assert tool.execute_scan(args) == 1


def test_execute_scan_no_container_returns_error(tmp_path):
    tool = ScanTool()
    d = tmp_path / "d"
    d.mkdir()
    args = SimpleNamespace(paths=[str(d)], container=None, min_size=0, max_size=None, extensions=None, verbose=False)
    assert tool.execute_scan(args) == 1


def test_execute_scan_success_and_saves(tmp_path, capsys):
    tool = ScanTool()
    d = tmp_path / "d"
    d.mkdir()

    sample_file = {"path": str(d / "a.txt"), "size": 10, "modified_time": 1, "extension": ".txt", "hash": "h1"}

    class DummyProcessor:
        def __init__(self, walker=None):
            self._files = [sample_file]

        def process_files(self, root_path, file_filter=None, on_progress=None):
            out = [f for f in self._files if (not file_filter or file_filter(f))]
            # simulate progress callback
            if on_progress and out:
                on_progress({"files_processed": len(out), "files_per_second": 1.0})
            return out

    class DummyRepo:
        def __init__(self, db):
            pass

        def batch_add_files(self, files):
            return len(files)

    # Dummy container with a fake database service
    class C:
        def get_service(self, name):
            return object()

    args = SimpleNamespace(paths=[str(d)], container=C(), min_size=0, max_size=None, extensions=None, verbose=True)

    with patch('nodupe.tools.commands.scan.FileProcessor', DummyProcessor), patch('nodupe.tools.commands.scan.FileRepository', DummyRepo):
        rv = tool.execute_scan(args)

    assert rv == 0
    captured = capsys.readouterr()
    assert "Total files processed" in captured.out
