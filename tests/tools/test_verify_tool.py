import argparse
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from nodupe.tools.commands.verify import VerifyTool


def test_execute_verify_no_container_returns_error():
    tool = VerifyTool()
    args = SimpleNamespace(mode="all", fast=False, repair=False, verbose=False, output=None, container=None)

    rc = tool.execute_verify(args)
    assert rc == 1


def test__verify_integrity_counts_missing_files(tmp_path):
    tool = VerifyTool()

    # file_repo.get_all_files returns entries with a non-existent path
    file_repo = Mock()
    file_repo.get_all_files.return_value = [
        {"id": 1, "path": str(tmp_path / "nope.txt"), "size": 123, "is_duplicate": False, "duplicate_of": None}
    ]

    args = SimpleNamespace(fast=False, verbose=True)
    res = tool._verify_integrity(file_repo, args)

    assert res["checks"] == 1
    assert res["errors"] >= 1


def test__output_findings_to_file_writes_json(tmp_path):
    tool = VerifyTool()

    results = {
        "integrity": {"checks": 1, "errors": 0, "warnings": 0, "error_details": []},
        "consistency": {"checks": 0, "errors": 0, "warnings": 0, "error_details": []},
        "checksums": {"checks": 0, "errors": 0, "warnings": 0, "error_details": []},
    }

    out_file = tmp_path / "verify.json"
    args = SimpleNamespace(mode="all", fast=False, verbose=False, repair=False)

    tool._output_findings_to_file(results, str(out_file), args)

    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "timestamp" in data and "summary" in data


def test_execute_verify_checksums_fast_mode_skips(tmp_path):
    tool = VerifyTool()

    fake_container = Mock()
    fake_db = Mock()
    fake_container.get_service.return_value = fake_db

    args = SimpleNamespace(mode="checksums", fast=True, repair=False, verbose=False, output=None, container=fake_container)

    # Should return 0 (no errors) because checksums are skipped in fast mode
    rc = tool.execute_verify(args)
    assert rc == 0
