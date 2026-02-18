import hashlib
import json
from pathlib import Path
from unittest.mock import Mock, patch

from nodupe.tools.maintenance.log_compressor import LogCompressor


def test_generate_metadata_contains_fixity(tmp_path):
    f = tmp_path / "app.log.1"
    f.write_bytes(b"hello world")

    meta = LogCompressor._generate_metadata(f)
    assert "fixity" in meta and "value" in meta["fixity"]

    # verify sha256 matches
    sha = hashlib.sha256(f.read_bytes()).hexdigest()
    assert meta["fixity"]["value"] == sha


def test_compress_old_logs_no_dir_returns_empty(tmp_path):
    # Non-existent directory
    res = LogCompressor.compress_old_logs(str(tmp_path / "nope"))
    assert res == []


def test_compress_old_logs_no_archive_handler_returns_empty(tmp_path):
    d = tmp_path / "logs"
    d.mkdir()
    (d / "app.log.1").write_text("x")

    with patch("nodupe.tools.maintenance.log_compressor.global_container") as gc:
        gc.get_service.return_value = None
        res = LogCompressor.compress_old_logs(str(d), pattern="*.log.*")
        assert res == []


def test_compress_old_logs_creates_archive_and_cleans_up(tmp_path):
    d = tmp_path / "logs"
    d.mkdir()
    file_path = d / "app.log.1"
    file_path.write_text("logdata")

    fake_archive = Mock()

    # Make create_archive write an empty file to mimic real archive creation
    def create_archive(path, members, archive_format="zip"):
        Path(path).write_text("zip")

    fake_archive.create_archive.side_effect = create_archive

    with patch("nodupe.tools.maintenance.log_compressor.global_container") as gc:
        gc.get_service.return_value = fake_archive

        res = LogCompressor.compress_old_logs(str(d), pattern="*.log.*")

        # Expect one archive path returned
        assert len(res) == 1
        zip_path = res[0]
        assert zip_path.exists()

        # original file and metadata/manual should have been removed
        assert not file_path.exists()
        assert not (d / f"{file_path.name}.metadata.json").exists()
        assert not (d / "RECOVERY_INSTRUCTIONS.txt").exists()
