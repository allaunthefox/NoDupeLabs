import os
import shutil
import tempfile
from pathlib import Path

from nodupe.core.container import container
from nodupe.tools.archive.archive_logic import ArchiveHandler
from nodupe.tools.maintenance.log_compressor import LogCompressor


def test_log_compression():
    # Setup dependency injection
    container.register_service("archive_handler_service", ArchiveHandler())

    # Create a temporary log directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Create mock log files
        log1 = Path(temp_dir) / "app.log.1"
        log2 = Path(temp_dir) / "app.log.2"
        active_log = Path(temp_dir) / "app.log"

        log1.write_text("old log content 1")
        log2.write_text("old log content 2")
        active_log.write_text("active log content")

        # Run compression
        compressed = LogCompressor.compress_old_logs(
            temp_dir, pattern="app.log.[0-9]*"
        )

        # Verify results
        assert len(compressed) == 2

        # Check ZIP 1
        zip1_path = Path(temp_dir) / "app.log.1.zip"
        assert zip1_path.exists()
        import zipfile

        with zipfile.ZipFile(zip1_path, "r") as zf:
            namelist = zf.namelist()
            assert "app.log.1" in namelist
            assert "app.log.1.metadata.json" in namelist

        # Check ZIP 2
        zip2_path = Path(temp_dir) / "app.log.2.zip"
        assert zip2_path.exists()
        with zipfile.ZipFile(zip2_path, "r") as zf:
            namelist = zf.namelist()
            assert "app.log.2" in namelist
            assert "app.log.2.metadata.json" in namelist

        assert not log1.exists()
        assert not log2.exists()
        assert active_log.exists()

        print("Log compression test passed!")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_log_compression()
