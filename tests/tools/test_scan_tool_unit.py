import argparse
import os
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.commands.scan import ScanTool


def make_args(paths=None, container=None, **kw):
    ns = argparse.Namespace()
    ns.paths = paths
    ns.min_size = kw.get("min_size", 0)
    ns.max_size = kw.get("max_size", None)
    ns.extensions = kw.get("extensions", None)
    ns.exclude = kw.get("exclude", None)
    ns.verbose = kw.get("verbose", False)
    ns.container = container
    return ns


def test_execute_scan_no_paths_returns_error():
    t = ScanTool()
    args = make_args(paths=None)
    assert t.execute_scan(args) == 1


def test_execute_scan_missing_path_returns_error(tmp_path):
    t = ScanTool()
    missing = str(tmp_path / "does_not_exist")
    args = make_args(paths=[missing], container=MagicMock())
    assert t.execute_scan(args) == 1


def test_execute_scan_no_container_returns_error(tmp_path):
    t = ScanTool()
    p = tmp_path / "d"
    p.mkdir()
    args = make_args(paths=[str(p)], container=None)
    # Should return error because container is required
    assert t.execute_scan(args) == 1


def test_execute_scan_success_path_processes_files(tmp_path):
    # Prepare a directory with a file
    d = tmp_path / "data"
    d.mkdir()
    f = d / "a.txt"
    f.write_text("hello")

    # Mock container and services
    mock_container = MagicMock()
    mock_db = MagicMock()
    mock_container.get_service.return_value = mock_db

    # Patch FileProcessor.process_files to return a fake result list
    fake_result = [{"path": str(f), "size": 5, "extension": "txt"}]

    with patch("nodupe.tools.commands.scan.FileProcessor") as mock_processor_cls:
        mock_processor = mock_processor_cls.return_value
        mock_processor.process_files.return_value = fake_result

        # Patch FileRepository to track batch_add_files call
        with patch("nodupe.tools.commands.scan.FileRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.batch_add_files.return_value = len(fake_result)

            t = ScanTool()
            args = make_args(paths=[str(d)], container=mock_container, verbose=False)

            rc = t.execute_scan(args)

            assert rc == 0
            mock_processor.process_files.assert_called()
            mock_repo.batch_add_files.assert_called_with(fake_result)
