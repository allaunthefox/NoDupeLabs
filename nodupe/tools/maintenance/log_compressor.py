# pylint: disable=logging-fstring-interpolation
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Log Compression Utility.

Provides functionality to compress old log files using the built-in ZIP support.
"""

import glob
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .api.codes import ActionCode
from .container import container as global_container


logger = logging.getLogger(__name__)

class LogCompressor:
    """Utility to compress rotated log files (ISO 14721 / OAIS Compliant)."""

    RECOVERY_MANUAL = """# ISO 14721 (OAIS) RECOVERY MANUAL
This archive is a self-describing Archival Information Package (AIP).
If the original software (NoDupeLabs) is unavailable, follow these steps:

1. STRUCTURE:
   - [Original Log File]: The raw data.
   - [METADATA.json]: Standardized metadata (ISO 15836 / Dublin Core).

2. VERIFICATION:
   Open METADATA.json and locate the "fixity" section.
   To verify data integrity, run:
   sha256sum [Original Log File]
   Compare the result with the "value" in the fixity section.

3. STANDARDS:
   - Filename: ISO 8601 (YYYYMMDDTHHMMSSZ)
   - Timestamps: RFC 3339
   - Format: ISO/IEC 21320-1 (ZIP)
"""

    @staticmethod
    def _generate_metadata(file_path: Path) -> dict[str, Any]:
        """Generate ISO 15836 (Dublin Core) compliant metadata."""
        file_path.stat()
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        # ISO 15836 (Dublin Core) + ISO 14721 (OAIS)
        return {
            "dc:identifier": f"AIP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            "dc:title": f"Log Archive: {file_path.name}",
            "dc:format": "text/plain",
            "dc:language": "en-US",
            "dc:date": datetime.now(timezone.utc).isoformat(),
            "dc:publisher": "NoDupeLabs Archival Engine",
            "oais:package_type": "AIP",
            "oais:specification": "ISO 14721:2012",
            "fixity": {
                "algorithm": "sha256",
                "value": sha256_hash.hexdigest()
            }
        }

    @staticmethod
    def compress_old_logs(log_dir: str = "logs", pattern: str = "*.log.*") -> list[Path]:
        """Find and compress logs into software-independent ISO AIPs."""
        compressed_files = []
        log_path = Path(log_dir)
        if not log_path.exists(): return []

        archive_handler = global_container.get_service('archive_handler_service')
        if not archive_handler: return []

        files = glob.glob(os.path.join(log_dir, pattern))
        for file_path in files:
            p = Path(file_path)
            if p.suffix == '.zip' or not p.exists(): continue

            try:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                clean_name = p.name.replace(".", "_")
                zip_name = f"AIP_{timestamp}_{clean_name}.zip"
                zip_path = p.parent / zip_name

                # 1. Generate Dublin Core Metadata
                metadata = LogCompressor._generate_metadata(p)
                metadata_path = p.parent / "METADATA.json"
                metadata_path.write_text(json.dumps(metadata, indent=2))

                # 2. Generate Recovery Manual
                manual_path = p.parent / "RECOVERY_INSTRUCTIONS.txt"
                manual_path.write_text(LogCompressor.RECOVERY_MANUAL)

                # 3. Create AIP (Includes data + metadata + manual)
                archive_handler.create_archive(
                    str(zip_path),
                    [str(p), str(metadata_path), str(manual_path)],
                    format='zip'
                )

                logger.info(f"[{ActionCode.ARCHIVE_AIP}] Created self-describing AIP: {zip_name}")

                p.unlink()
                metadata_path.unlink()
                manual_path.unlink()
                compressed_files.append(zip_path)

            except Exception as e:
                logger.exception(f"[{ActionCode.ERR_EXEC_FAILED}] Archive creation failed: {e}")
