import os
import tempfile
import pytest
from pathlib import Path
from nodupe.cli import check_scan_requirements


def test_check_scan_requirements_success():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "input"
        root.mkdir()

        out = Path(td) / "output"
        out.mkdir()

        cfg = {
            "db_path": str(out / "index.db"),
            "log_dir": str(out / "logs"),
            "metrics_path": str(out / "metrics.json")
        }

        assert check_scan_requirements([str(root)], cfg) is True


def test_check_scan_requirements_missing_root():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "missing"

        cfg = {}
        # Should fail because root doesn't exist
        assert check_scan_requirements([str(root)], cfg) is False


def test_check_scan_requirements_unwritable_output():
    if os.geteuid() == 0:
        pytest.skip("Skipping permissions test as root")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "input"
        root.mkdir()

        out = Path(td) / "output"
        out.mkdir()
        # Make output read-only
        out.chmod(0o500)

        cfg = {
            # subdir creation should fail
            "db_path": str(out / "subdir" / "index.db"),
        }

        assert check_scan_requirements([str(root)], cfg) is False
