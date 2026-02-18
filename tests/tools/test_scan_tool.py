import argparse
from types import SimpleNamespace
from unittest.mock import Mock, patch

from nodupe.tools.commands.scan import ScanTool


def test_execute_scan_no_paths_returns_error():
    tool = ScanTool()
    args = SimpleNamespace(paths=[], container=Mock(), min_size=0, max_size=None, extensions=None, exclude=None, verbose=False)

    rc = tool.execute_scan(args)
    assert rc == 1


def test_execute_scan_path_not_exists_returns_error():
    tool = ScanTool()
    args = SimpleNamespace(paths=["/nonexistent/path"], container=Mock(), min_size=0, max_size=None, extensions=None, exclude=None, verbose=False)

    rc = tool.execute_scan(args)
    assert rc == 1


def test_execute_scan_success_calls_batch_add_files(tmp_path):
    tool = ScanTool()

    fake_container = Mock()

    # Prepare fake results from processor
    sample_result = [{"path": str(tmp_path / "a.txt"), "size": 1, "extension": "txt"}]

    with patch("nodupe.tools.commands.scan.FileProcessor") as mock_processor_cls, patch(
        "nodupe.tools.commands.scan.FileRepository"
    ) as mock_repo_cls:
        mock_processor = mock_processor_cls.return_value
        mock_processor.process_files.return_value = sample_result

        mock_repo = mock_repo_cls.return_value
        mock_repo.batch_add_files.return_value = 1

        args = SimpleNamespace(paths=[str(tmp_path)], container=fake_container, min_size=0, max_size=None, extensions=None, exclude=None, verbose=False)

        rc = tool.execute_scan(args)

        assert rc == 0
        mock_processor.process_files.assert_called()
        mock_repo.batch_add_files.assert_called_once()
